"""Generador y verificador de la base de conocimiento (roadmap §2.2 y §10.1).

Lee la ontología OWL (TTL) y las plantillas de clips/00_main.clp. Con ellas:
- genera config/base_coneixement.clp: un deffacts MAIN:: con un hecho por individuo;
- con --verificar, comprueba la base de conocimiento (§10.1).
"""

import argparse
import math
import re
import sys
from collections import Counter, defaultdict
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
# Verificación de la base de conocimiento (§10.1), con mundo cerrado
# ---------------------------------------------------------------------------

NIVELES = ("baix", "mitja", "alt", "critic")   # escala ordinal (§2.3.5)


@dataclass(frozen=True)
class Anomalia:
    categoria: str
    mensaje: str


def _valor(ind: Individuo, prop: str):
    valores = ind.valores.get(prop)
    return valores[0][0] if valores else None


def _numero(ind: Individuo, prop: str, defecto: float) -> float:
    try:
        valor = _valor(ind, prop)
        return defecto if valor is None else float(valor)
    except (TypeError, ValueError):
        return defecto                              # ya lo señala verificar_vocabulario


def _ancestros(onto: Ontologia, clases: list[str]) -> set[str]:
    return set().union(*(onto.ancestros(c) for c in clases))


def verificar_vocabulario(onto: Ontologia, plantillas: dict[str, dict[str, Slot]]) -> list[Anomalia]:
    """Términos declarados, clase, disyunción, dominio, rango, funcionales,
    enumeraciones y slots obligatorios de cada individuo."""
    an = [Anomalia("vocabulario", f"término no declarado: {t}") for t in sorted(onto.terminos_no_declarados)]
    for ind in sorted(onto.individuos.values(), key=lambda i: i.nombre):
        concretas = [c for c in ind.clases if onto.clases.get(c) is not None]
        if len(concretas) != 1:
            an.append(Anomalia("vocabulario", f"{ind.nombre}: tiene {len(concretas)} clases con plantilla {concretas}"))
        ancestros = _ancestros(onto, ind.clases)
        for grupo in onto.disjuntas:
            if len(ancestros & grupo) > 1:
                an.append(Anomalia("disyuncion", f"{ind.nombre}: pertenece a clases disjuntas {sorted(ancestros & grupo)}"))
        clase = concretas[0] if len(concretas) == 1 else None
        slots = plantillas.get(kebab(clase)) if clase else None

        for nombre, valores in sorted(ind.valores.items()):
            prop = onto.propiedades.get(nombre)
            if prop is None:
                continue                                # ya es "término no declarado"
            if prop.dominio is not None and clase is not None and prop.dominio != clase:
                an.append(Anomalia("dominio", f"{ind.nombre}: {nombre} es de {prop.dominio}, no de {clase}"))
            elif slots is not None and nombre not in slots:
                an.append(Anomalia("dominio", f"{ind.nombre}: la plantilla {kebab(clase)} no tiene el slot {nombre}"))
            if prop.funcional and len(valores) > 1:
                an.append(Anomalia("funcional", f"{ind.nombre}: {nombre} es funcional y tiene {len(valores)} valores"))
            for valor, tipo in valores:
                if prop.enumeracion is not None:
                    if tipo != "string" or valor not in prop.enumeracion:
                        an.append(Anomalia("enumeracion", f"{ind.nombre}: {nombre}={valor} no está en {prop.enumeracion}"))
                elif prop.de_objeto:
                    destino = onto.individuos.get(valor) if tipo == "objeto" else None
                    if destino is None or prop.rango not in _ancestros(onto, destino.clases):
                        an.append(Anomalia("rango", f"{ind.nombre}: {nombre}={valor} no es un individuo de {prop.rango}"))
                elif tipo != prop.rango:
                    an.append(Anomalia("rango", f"{ind.nombre}: {nombre}={valor} es {tipo}, se espera {prop.rango}"))

        if slots is not None:
            for slot in slots.values():
                if slot.nombre != "id" and not slot.opcional and slot.nombre not in ind.valores:
                    an.append(Anomalia("completitud", f"{ind.nombre}: falta {slot.nombre}, obligatorio en {kebab(clase)}"))
    return an


def verificar_umbrales(onto: Ontologia) -> list[Anomalia]:
    """Los umbrales de cada variable son una partición de la recta, con niveles
    distintos y monótonos y una sola referencia."""
    an = []
    por_variable = defaultdict(list)
    for ind in onto.de_clase("Umbral"):
        por_variable[_valor(ind, "variable")].append(ind)
    for variable, inds in sorted(por_variable.items(), key=lambda kv: str(kv[0])):
        referencias = {_valor(i, "referencia") for i in inds}
        if len(referencias) != 1:
            an.append(Anomalia("umbrales", f"{variable}: varias referencias {sorted(map(str, referencias))}"))
        niveles = [_valor(i, "nivel") for i in inds]
        if len(set(niveles)) != len(niveles):
            an.append(Anomalia("umbrales", f"{variable}: niveles repetidos {sorted(map(str, niveles))}"))
        intervalos = sorted((_numero(i, "limite-inferior", -math.inf), _numero(i, "limite-superior", math.inf),
                             _valor(i, "nivel"), i.nombre) for i in inds)
        for inf, sup, _, nombre in intervalos:
            if inf >= sup:
                an.append(Anomalia("umbrales", f"{nombre}: intervalo vacío [{inf}, {sup})"))
        if intervalos[0][0] != -math.inf:
            an.append(Anomalia("umbrales", f"{variable}: no cubre (-inf, {intervalos[0][0]})"))
        if intervalos[-1][1] != math.inf:
            an.append(Anomalia("umbrales", f"{variable}: no cubre [{intervalos[-1][1]}, +inf)"))
        for (_, sup, _, a), (inf, _, _, b) in zip(intervalos, intervalos[1:]):
            if sup < inf:
                an.append(Anomalia("umbrales", f"{variable}: hueco [{sup}, {inf}) entre {a} y {b}"))
            elif sup > inf:
                an.append(Anomalia("umbrales", f"{variable}: solape [{inf}, {sup}) entre {a} y {b}"))
        orden = [NIVELES.index(n) for _, _, n, _ in intervalos if n in NIVELES]
        crecen = all(x < y for x, y in zip(orden, orden[1:]))
        decrecen = all(x > y for x, y in zip(orden, orden[1:]))
        if not (crecen or decrecen):
            an.append(Anomalia("umbrales", f"{variable}: niveles no monótonos {[n for _, _, n, _ in intervalos]}"))
    return an


def verificar_fases(onto: Ontologia) -> list[Anomalia]:
    """La tabla de fases recorre todas las fases de percepcio a espera, sin ciclos;
    deliberacio vuelve a seleccio; un módulo distinto por fase (§4.1)."""
    an = []
    filas = {}
    for ind in onto.de_clase("DefinicionFase"):
        fase = _valor(ind, "fase")
        if fase in filas:
            an.append(Anomalia("fases", f"{fase}: más de una fila"))
        filas[fase] = (_valor(ind, "modulo"), _valor(ind, "siguiente"))
    enumeracion = onto.propiedades["fase"].enumeracion if "fase" in onto.propiedades else ()
    for fase in enumeracion:
        if fase != "espera" and fase not in filas:
            an.append(Anomalia("fases", f"{fase}: no tiene fila"))
    if "espera" in filas:
        an.append(Anomalia("fases", "espera no debe tener fila: solo la abandona iniciar-ciclo"))
    for modulo, n in Counter(m for m, _ in filas.values()).items():
        if n > 1:
            an.append(Anomalia("fases", f"el módulo {modulo} ejecuta {n} fases"))

    recorrido, fase = [], "percepcio"
    while fase != "espera":
        if fase in recorrido:
            an.append(Anomalia("fases", f"ciclo en la secuencia: {' -> '.join(recorrido)} -> {fase}"))
            break
        if fase not in filas:
            an.append(Anomalia("fases", f"la secuencia se corta en {fase}: {' -> '.join(recorrido)}"))
            break
        recorrido.append(fase)
        fase = filas[fase][1]
    inalcanzables = set(filas) - set(recorrido) - {"deliberacio"}
    if inalcanzables:
        an.append(Anomalia("fases", f"fases inalcanzables desde percepcio: {sorted(map(str, inalcanzables))}"))
    if "deliberacio" in recorrido:
        an.append(Anomalia("fases", "deliberacio no debe estar en la secuencia principal"))
    if filas.get("deliberacio", (None, None))[1] != "seleccio":
        an.append(Anomalia("fases", "deliberacio debe volver a seleccio"))
    return an


def verificar_completitud(onto: Ontologia) -> list[Anomalia]:
    """Objetivos, sectores y datos requeridos completos."""
    an = []
    objetivos = onto.de_clase("ObjetivoActivo")
    enumeracion = onto.propiedades["nombre-objetivo"].enumeracion if "nombre-objetivo" in onto.propiedades else ()
    prioridades = sorted(str(_valor(o, "prioridad")) for o in objetivos)
    if prioridades != sorted(str(n) for n in range(1, len(enumeracion) + 1)):
        an.append(Anomalia("objetivos", f"las prioridades {prioridades} no son 1..{len(enumeracion)}"))
    nombres = [_valor(o, "nombre-objetivo") for o in objetivos]
    if sorted(map(str, nombres)) != sorted(enumeracion):
        an.append(Anomalia("objetivos", f"los objetivos {sorted(map(str, nombres))} no cubren {sorted(enumeracion)}"))

    for prop in ("tiene-cultivo", "tiene-seguidor"):
        usados = Counter()
        for sector in onto.de_clase("Sector"):
            valor = _valor(sector, prop)
            if valor is None:
                an.append(Anomalia("sectores", f"{sector.nombre}: no tiene {prop}"))
            else:
                usados[valor] += 1
        for valor, n in usados.items():
            if n > 1:
                an.append(Anomalia("sectores", f"{valor} lo comparten {n} sectores ({prop})"))

    con_umbral = {_valor(u, "variable") for u in onto.de_clase("Umbral")}
    for dato in onto.de_clase("DatoRequerido"):
        if _valor(dato, "variable") not in con_umbral:
            an.append(Anomalia("datos-requeridos", f"{dato.nombre}: la variable {_valor(dato, 'variable')} no tiene umbrales"))
    return an


def _restriccion_esperada(prop: Propiedad, opcional: bool) -> tuple[set[str], frozenset[str] | None]:
    """Tipo y allowed-symbols que §2.3 asigna a la propiedad."""
    nil = {"nil"} if opcional else set()
    if prop.enumeracion is not None:
        return {"SYMBOL"}, frozenset(prop.enumeracion) | nil
    if prop.rango == "boolean":
        return {"SYMBOL"}, frozenset({"TRUE", "FALSE"}) | nil
    if prop.rango in ("integer", "decimal"):
        tipos = {"INTEGER" if prop.rango == "integer" else "NUMBER"}
        return (tipos | {"SYMBOL"}, frozenset(nil)) if opcional else (tipos, None)
    return {"SYMBOL"}, None                         # cadenas y objetos: nil ya es un SYMBOL


def verificar_plantillas(onto: Ontologia, plantillas: dict[str, dict[str, Slot]]) -> tuple[list[Anomalia], list[str]]:
    """Las plantillas de 00_main.clp coinciden con el TTL. Devuelve también los avisos
    de lo que aún no está escrito."""
    an, avisos = [], []
    clase_de = {kebab(c): c for c in onto.concretas()}
    for nombre in plantillas:
        if nombre not in clase_de:
            an.append(Anomalia("plantillas", f"{nombre}: no corresponde a ninguna clase del TTL"))
    pendientes = [n for n in sorted(clase_de) if n not in plantillas]
    if pendientes:
        avisos.append(f"plantillas pendientes en {MAIN_CLP.name}: {', '.join(pendientes)}")

    for nombre, slots in plantillas.items():
        clase = clase_de.get(nombre)
        if clase is None:
            continue
        for prop in sorted(onto.propiedades.values(), key=lambda p: p.nombre):
            if prop.dominio == clase and prop.nombre not in slots:
                an.append(Anomalia("plantillas", f"{nombre}: falta el slot {prop.nombre}"))
        for slot in slots.values():
            prop = onto.propiedades.get(slot.nombre)
            if prop is None:
                an.append(Anomalia("plantillas", f"{nombre}.{slot.nombre}: no es una propiedad del TTL"))
                continue
            if prop.dominio not in (None, clase):
                an.append(Anomalia("plantillas", f"{nombre}.{slot.nombre}: la propiedad es de {prop.dominio}"))
            if slot.multi == prop.funcional:
                esperado = "slot" if prop.funcional else "multislot"
                an.append(Anomalia("plantillas", f"{nombre}.{slot.nombre}: debe ser {esperado}"))
            tipos, simbolos = _restriccion_esperada(prop, slot.opcional)
            if slot.tipos != tipos:
                an.append(Anomalia("plantillas", f"{nombre}.{slot.nombre}: tipo {sorted(slot.tipos)}, se espera {sorted(tipos)}"))
            if slot.simbolos != simbolos:
                an.append(Anomalia("plantillas", f"{nombre}.{slot.nombre}: allowed-symbols "
                                   f"{sorted(slot.simbolos or ())}, se espera {sorted(simbolos or ())}"))

    usadas = {s for slots in plantillas.values() for s in slots}
    sin_slot = sorted(p for p in onto.propiedades if p not in usadas)
    if sin_slot:
        mensaje = f"propiedades sin slot en ninguna plantilla: {', '.join(sin_slot)}"
        if pendientes:
            avisos.append(mensaje)
        else:
            an.append(Anomalia("plantillas", mensaje))
    return an, avisos


def verificar(onto: Ontologia, plantillas: dict[str, dict[str, Slot]]) -> tuple[list[Anomalia], list[str]]:
    """Todas las comprobaciones de §10.1 que no necesitan la batería de casos."""
    an_plantillas, avisos = verificar_plantillas(onto, plantillas)
    anomalias = (verificar_vocabulario(onto, plantillas) + verificar_umbrales(onto)
                 + verificar_fases(onto) + verificar_completitud(onto) + an_plantillas)
    avisos.append("reglas no disparadas en la batería de casos: pendiente hasta que haya reglas (I2)")
    return anomalias, avisos


# ---------------------------------------------------------------------------
# Línea de órdenes
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Genera config/base_coneixement.clp a partir del TTL (§2.2) "
                                             "o verifica la base de conocimiento (§10.1).")
    ap.add_argument("--verificar", action="store_true", help="verifica en lugar de generar")
    ap.add_argument("--set", action="append", default=[], metavar="PROP=VALOR", dest="sobrescrituras",
                    help="sobrescribe un parámetro de aprendizaje (p. ej. aprendizaje-activo=FALSE)")
    ap.add_argument("--salida", type=Path, default=SALIDA, help="fichero generado")
    args = ap.parse_args(argv)

    onto = leer_ontologia()
    plantillas = leer_plantillas()
    if args.verificar:
        anomalias, avisos = verificar(onto, plantillas)
        print("Verificación de la base de conocimiento (roadmap §10.1)")
        for a in anomalias:
            print(f"  [{a.categoria}] {a.mensaje}")
        for aviso in avisos:
            print(f"  (aviso) {aviso}")
        print(f"{len(anomalias)} anomalías, {len(avisos)} avisos.")
        return 1 if anomalias else 0
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
