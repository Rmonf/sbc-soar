"""Generador y verificador de la base de conocimiento (roadmap §2.2 y §10.1).

Lee la ontología OWL (TTL) y las plantillas de clips/00_main.clp. Con ellas:
- genera config/base_coneixement.clp: un deffacts MAIN:: con un hecho por individuo;
- con --verificar, comprueba la base de conocimiento (§10.1).
"""

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import clips
from rdflib import BNode, Graph, Literal, URIRef
from rdflib.collection import Collection
from rdflib.namespace import OWL, RDF, RDFS, XSD

RAIZ = Path(__file__).resolve().parent.parent
TTL = RAIZ / "ontologia" / "agrovoltaica-soar.ttl"
MAIN_CLP = RAIZ / "clips" / "00_main.clp"
SALIDA = RAIZ / "config" / "base_coneixement.clp"
NS = "http://www.upc.edu/ontologies/agrovoltaica-soar/"

# Tipo de cada literal según su datatype (§2.3.9); sin datatype es una cadena.
TIPOS_XSD = {XSD.decimal: "decimal", XSD.integer: "integer",
             XSD.boolean: "boolean", XSD.string: "string", None: "string"}


# ---------------------------------------------------------------------------
# Modelo de la ontología
# ---------------------------------------------------------------------------

@dataclass
class Propiedad:
    nombre: str
    de_objeto: bool
    funcional: bool
    dominio: str | None          # clase (nombre local) o None si es compartida
    rango: str | None            # clase, "decimal", "integer", "boolean" o "string"
    enumeracion: tuple[str, ...] | None = None


@dataclass
class Individuo:
    nombre: str
    clases: list[str]
    # propiedad -> lista de (valor, tipo); tipo es un tipo XSD de TIPOS_XSD,
    # "objeto" (el valor es el nombre local) u "otro" (literal de tipo desconocido)
    valores: dict[str, list[tuple[object, str]]] = field(default_factory=dict)


@dataclass
class Ontologia:
    clases: dict[str, str | None]            # clase -> superclase (None = raíz)
    propiedades: dict[str, Propiedad]
    individuos: dict[str, Individuo]
    disjuntas: list[set[str]]                # grupos de clases disjuntas dos a dos
    terminos_no_declarados: set[str] = field(default_factory=set)

    def raices(self) -> list[str]:
        return sorted(c for c, sup in self.clases.items() if sup is None)

    def concretas(self) -> list[str]:
        """Clases con plantilla (§2.3.1: las raíces no tienen)."""
        return sorted(c for c, sup in self.clases.items() if sup is not None)

    def ancestros(self, clase: str) -> set[str]:
        resultado = set()
        while clase is not None and clase not in resultado:
            resultado.add(clase)
            clase = self.clases.get(clase)
        return resultado

    def de_clase(self, clase: str) -> list[Individuo]:
        return [i for i in self.individuos.values() if clase in i.clases]


def kebab(nombre: str) -> str:
    """Clase → nombre de plantilla (§2.3.1): EstadoSOAR → estado-soar."""
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "-", nombre).lower()


def _local(nodo) -> str | None:
    if isinstance(nodo, URIRef) and str(nodo).startswith(NS):
        return str(nodo)[len(NS):]
    return None


def leer_grafo(ruta: Path = TTL) -> Graph:
    g = Graph()
    g.parse(ruta, format="turtle")
    return g


def ontologia_desde_grafo(g: Graph) -> Ontologia:
    clases = {}
    for c in g.subjects(RDF.type, OWL.Class):
        nombre = _local(c)
        if nombre is not None:
            clases[nombre] = _local(g.value(c, RDFS.subClassOf))

    propiedades = {}
    for tipo, de_objeto in ((OWL.ObjectProperty, True), (OWL.DatatypeProperty, False)):
        for p in g.subjects(RDF.type, tipo):
            rango = g.value(p, RDFS.range)
            enumeracion = None
            if isinstance(rango, BNode):
                lista = g.value(rango, OWL.oneOf)
                enumeracion = tuple(str(v) for v in Collection(g, lista))
                rango_nombre = None
            elif de_objeto:
                rango_nombre = _local(rango)
            else:
                rango_nombre = TIPOS_XSD.get(rango, str(rango))
            propiedades[_local(p)] = Propiedad(
                nombre=_local(p),
                de_objeto=de_objeto,
                funcional=(p, RDF.type, OWL.FunctionalProperty) in g,
                dominio=_local(g.value(p, RDFS.domain)),
                rango=rango_nombre,
                enumeracion=enumeracion,
            )
    anotaciones = {_local(a) for a in g.subjects(RDF.type, OWL.AnnotationProperty)}

    individuos = {}
    no_declarados = set()
    for s in g.subjects(RDF.type, OWL.NamedIndividual):
        ind = Individuo(nombre=_local(s), clases=[])
        for p, o in g.predicate_objects(s):
            if p == RDF.type:
                if o != OWL.NamedIndividual:
                    ind.clases.append(_local(o) or str(o))
                continue
            prop = _local(p)
            if prop is None or prop in anotaciones:
                continue
            if isinstance(o, Literal):
                valor = (o.toPython(), TIPOS_XSD.get(o.datatype, "otro"))
            else:
                valor = (_local(o) or str(o), "objeto")
            ind.valores.setdefault(prop, []).append(valor)
        ind.clases.sort()
        for valores in ind.valores.values():
            valores.sort(key=str)
        individuos[ind.nombre] = ind

    # Términos del espacio de nombres usados como clase o propiedad sin declarar.
    for ind in individuos.values():
        no_declarados |= {c for c in ind.clases if c not in clases}
        no_declarados |= {p for p in ind.valores if p not in propiedades}

    disjuntas = []
    for a, b in g.subject_objects(OWL.disjointWith):
        disjuntas.append({_local(a), _local(b)})
    for nodo in g.subjects(RDF.type, OWL.AllDisjointClasses):
        miembros = g.value(nodo, OWL.members)
        disjuntas.append({_local(c) for c in Collection(g, miembros)})

    return Ontologia(clases, propiedades, individuos, disjuntas, no_declarados)


def leer_ontologia(ruta: Path = TTL) -> Ontologia:
    return ontologia_desde_grafo(leer_grafo(ruta))


# ---------------------------------------------------------------------------
# Plantillas de clips/00_main.clp (por introspección en clipspy)
# ---------------------------------------------------------------------------

@dataclass
class Slot:
    nombre: str
    multi: bool
    tipos: frozenset[str]              # FLOAT + INTEGER se resume como NUMBER
    simbolos: frozenset[str] | None    # allowed-symbols, o None si no hay
    opcional: bool                     # tiene (default nil) explícito (§2.3.7)


def _sexp(texto: str) -> list:
    """Convierte el texto de una construcción CLIPS en listas anidadas de tokens."""
    pila = [[]]
    for token in re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', texto):
        if token == "(":
            pila.append([])
        elif token == ")":
            hecho = pila.pop()
            pila[-1].append(hecho)
        else:
            pila[-1].append(token)
    return pila[0]


def leer_plantillas(ruta: Path = MAIN_CLP) -> dict[str, dict[str, Slot]]:
    """Plantilla -> slots (en orden de declaración) de las deftemplate de un fichero.

    clipspy no distingue un (default nil) explícito del default implícito de un
    slot SYMBOL, así que eso se lee del texto de la plantilla cargada.
    """
    env = clips.Environment()
    env.load(str(ruta))
    plantillas = {}
    for t in env.templates():
        if t.implied:
            continue
        explicitos = {e[1]: ["default", "nil"] in e[2:]
                      for e in _sexp(str(t))[0]
                      if isinstance(e, list) and e and e[0] in ("slot", "multislot")}
        slots = {}
        for s in t.slots:
            tipos = set(s.types)
            if {"FLOAT", "INTEGER"} <= tipos:
                tipos -= {"FLOAT", "INTEGER"}
                tipos.add("NUMBER")
            slots[s.name] = Slot(
                nombre=s.name,
                multi=s.multifield,
                tipos=frozenset(tipos),
                # sin allowed-symbols, clipspy devuelve el símbolo FALSE en vez de una tupla
                simbolos=frozenset(s.allowed_values) if isinstance(s.allowed_values, tuple) else None,
                opcional=explicitos[s.name],
            )
        plantillas[t.name] = slots
    return plantillas


# ---------------------------------------------------------------------------
# Generación de config/base_coneixement.clp (§2.2)
# ---------------------------------------------------------------------------

def plantilla_de(onto: Ontologia, ind: Individuo) -> str:
    """Plantilla del individuo: la de su única clase concreta (§2.3.1)."""
    concretas = [c for c in ind.clases if onto.clases.get(c) is not None]
    if len(concretas) != 1:
        raise ValueError(f"{ind.nombre}: debe tener exactamente una clase con plantilla, tiene {concretas}")
    return kebab(concretas[0])


def valor_clips(valor, tipo: str) -> str:
    """Literal del TTL → valor CLIPS (§2.3.6, §2.3.9)."""
    if tipo == "decimal":
        return repr(float(valor))
    if tipo == "boolean":
        return "TRUE" if valor else "FALSE"
    return str(valor)


def _convertir(texto: str, rango: str):
    if rango == "boolean" and texto.upper() in ("TRUE", "FALSE"):
        return texto.upper() == "TRUE"
    if rango == "decimal":
        return float(texto)
    if rango == "integer":
        return int(texto)
    raise ValueError(f"'{texto}' no es un valor {rango}")


def aplicar_sobrescrituras(onto: Ontologia, asignaciones: list[str]) -> None:
    """Aplica --set prop=valor sobre los parámetros de aprendizaje (§2.2)."""
    if not asignaciones:
        return
    params = onto.de_clase("ParametrosAprendizaje")
    if len(params) != 1:
        raise ValueError("debe haber exactamente un individuo ParametrosAprendizaje")
    for asignacion in asignaciones:
        nombre, igual, texto = asignacion.partition("=")
        prop = onto.propiedades.get(nombre)
        if not igual or prop is None or prop.dominio != "ParametrosAprendizaje":
            raise ValueError(f"--set {asignacion}: se espera prop=valor con una propiedad de ParametrosAprendizaje")
        try:
            params[0].valores[nombre] = [(_convertir(texto, prop.rango), prop.rango)]
        except ValueError as e:
            raise ValueError(f"--set {asignacion}: {e}") from None


def generar(onto: Ontologia, plantillas: dict[str, dict[str, Slot]],
            sobrescrituras: list[str] = ()) -> str:
    """Texto del deffacts con un hecho por individuo, en orden determinista."""
    grupos: dict[str, list[str]] = {}
    for ind in sorted(onto.individuos.values(), key=lambda i: i.nombre):
        nombre = plantilla_de(onto, ind)
        if nombre not in plantillas:
            raise ValueError(f"{ind.nombre}: la plantilla {nombre} no está en {MAIN_CLP.name}")
        slots = plantillas[nombre]
        sobrantes = set(ind.valores) - set(slots)
        if sobrantes:
            raise ValueError(f"{ind.nombre}: la plantilla {nombre} no tiene los slots {sorted(sobrantes)}")
        partes = []
        for slot in slots:
            if slot == "id":
                partes.append(f"(id {ind.nombre})")      # §2.3.6: id = nombre local
            elif slot in ind.valores:                    # ausente → default de la plantilla
                valores = " ".join(valor_clips(v, t) for v, t in ind.valores[slot])
                partes.append(f"({slot} {valores})")
        grupos.setdefault(nombre, []).append(f"   ({nombre} {' '.join(partes)})")

    lineas = [
        f";;; {SALIDA.name}: GENERADO por python/ontologia.py a partir de ontologia/{TTL.name}.",
        ";;; No se edita a mano: si cambia el TTL, se regenera (roadmap §2.2).",
    ]
    if sobrescrituras:
        lineas.append(f";;; Sobrescrituras: {' '.join(sobrescrituras)}")
    lineas += ["", "(deffacts MAIN::base-coneixement"]
    for nombre in plantillas:                            # orden de 00_main.clp
        if nombre in grupos:
            lineas += [f"   ;; {nombre}", *grupos[nombre]]
    lineas.append(")")
    return "\n".join(lineas) + "\n"


# ---------------------------------------------------------------------------
# Línea de órdenes
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Genera config/base_coneixement.clp a partir del TTL (§2.2).")
    ap.add_argument("--set", action="append", default=[], metavar="PROP=VALOR", dest="sobrescrituras",
                    help="sobrescribe un parámetro de aprendizaje (p. ej. aprendizaje-activo=FALSE)")
    ap.add_argument("--salida", type=Path, default=SALIDA, help="fichero generado")
    args = ap.parse_args(argv)

    onto = leer_ontologia()
    plantillas = leer_plantillas()
    try:
        aplicar_sobrescrituras(onto, args.sobrescrituras)
        texto = generar(onto, plantillas, args.sobrescrituras)
    except ValueError as e:
        ap.error(str(e))
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(texto, encoding="utf-8")
    print(f"Generado {args.salida} ({len(onto.individuos)} hechos)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
