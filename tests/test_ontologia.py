"""Pruebas del generador y del verificador de la ontología (roadmap §2.2, §10.1)."""

from collections import Counter

import pytest
from rdflib import Graph, Literal, Namespace
from rdflib.namespace import RDF, XSD

import ontologia as on

A = Namespace(on.NS)


@pytest.fixture(scope="module")
def onto():
    return on.leer_ontologia()


# --- Lectura del TTL: totales de §2.1 ---------------------------------------

def test_clases(onto):
    assert len(onto.raices()) == 6
    assert len(onto.concretas()) == 22
    assert on.kebab("EstadoSOAR") == "estado-soar"
    assert on.kebab("OperadorCandidato") == "operador-candidato"


def test_propiedades(onto):
    props = onto.propiedades.values()
    assert sum(p.de_objeto for p in props) == 11
    assert sum(not p.de_objeto for p in props) == 69
    assert len({frozenset(p.enumeracion) for p in props if p.enumeracion}) == 21


def test_individuos(onto):
    por_clase = Counter(c for i in onto.individuos.values() for c in i.clases)
    assert por_clase == {
        "Sector": 3, "Cultivo": 3, "SeguidorSolar": 3, "ObjetivoActivo": 5,
        "DatoRequerido": 4, "DefinicionFase": 11, "Umbral": 35,
        "ParametrosAprendizaje": 1, "EstadoSOAR": 1,
    }


# --- Plantillas de 00_main.clp -----------------------------------------------

@pytest.fixture(scope="module")
def plantillas():
    return on.leer_plantillas()


def test_plantillas(plantillas):
    assert set(plantillas) == {
        "sector", "cultivo", "seguidor-solar", "objetivo-activo", "dato-requerido",
        "definicion-fase", "umbral", "parametros-aprendizaje", "estado-soar",
        # familias dinámicas
        "impasse", "ciclo-temporal", "observacion-sensor", "observacion-panel", "prediccion",
        "abstraccion",
        "diagnostico", "operador-candidato", "valoracion", "preferencia", "orden-actuador",
        "episodio", "chunk",
    }
    umbral = plantillas["umbral"]
    assert umbral["limite-inferior"].tipos == {"NUMBER", "SYMBOL"}
    assert umbral["limite-inferior"].simbolos == {"nil"}
    assert umbral["limite-inferior"].opcional
    assert not umbral["nivel"].opcional
    assert plantillas["estado-soar"]["estado-padre"].opcional
    assert plantillas["sector"]["id"].simbolos is None
    assert plantillas["seguidor-solar"]["max-movimientos-hora"].tipos == {"INTEGER"}
    assert plantillas["episodio"]["tipo-impasse"].simbolos == {"tie", "dades-insuficients",
                                                              "constraint-failure", "nil"}
    assert plantillas["episodio"]["situacion"].multi
    assert plantillas["prediccion"]["sector"].opcional


# --- Generación de base_coneixement.clp --------------------------------------

def _generar(*sobrescrituras):
    onto = on.leer_ontologia()
    on.aplicar_sobrescrituras(onto, list(sobrescrituras))
    return on.generar(onto, on.leer_plantillas(), list(sobrescrituras))


def _cargar(tmp_path, texto):
    """Environment nuevo con 00_main.clp y la configuración dada, tras reset."""
    ruta = tmp_path / "base.clp"
    ruta.write_text(texto, encoding="utf-8")
    env = on.clips.Environment()
    env.load(str(on.MAIN_CLP))
    env.load(str(ruta))
    env.reset()
    return env


def _hechos(env, plantilla):
    return [f for f in env.facts() if f.template.name == plantilla]


def test_generacion_determinista_y_versionada():
    texto = _generar()
    assert texto == _generar()
    assert texto == on.SALIDA.read_text(encoding="utf-8"), "regenera con: uv run python python/ontologia.py"


def test_carga_en_clips(tmp_path):
    env = _cargar(tmp_path, _generar())
    assert len(list(env.facts())) == 66                 # CLIPS 6.4 no tiene initial-fact
    (s0,) = _hechos(env, "estado-soar")
    assert (s0["id"], s0["fase"], s0["subfase"], s0["estado-padre"]) == ("S0", "espera", "pendent", "nil")
    s1 = next(f for f in _hechos(env, "sector") if f["id"] == "s1")
    assert (s1["tiene-cultivo"], s1["tiene-seguidor"]) == ("cultivo-s1", "seguidor-s1")
    vent = {f["nivel"]: f for f in _hechos(env, "umbral") if f["variable"] == "vent"}
    assert (vent["baix"]["limite-inferior"], vent["baix"]["limite-superior"]) == ("nil", -40.0)
    assert (vent["critic"]["limite-inferior"], vent["critic"]["limite-superior"]) == (0.0, "nil")
    (seg,) = [f for f in _hechos(env, "seguidor-solar") if f["id"] == "seguidor-s1"]
    assert seg["max-movimientos-hora"] == 4 and isinstance(seg["max-movimientos-hora"], int)
    assert seg["umbral-viento-critico"] == 70.0 and isinstance(seg["umbral-viento-critico"], float)


def test_set_cambia_solo_ese_slot(tmp_path):
    base, variante = _generar(), _generar("aprendizaje-activo=FALSE", "umbral-olvido=-3")
    def cuerpo(texto):
        return [l for l in texto.splitlines() if not l.startswith(";;;")]
    assert ";;; Sobrescrituras: aprendizaje-activo=FALSE umbral-olvido=-3" in variante
    diferencias = [(a, b) for a, b in zip(cuerpo(base), cuerpo(variante)) if a != b]
    assert len(diferencias) == 1 and "parametros-aprendizaje" in diferencias[0][1]
    env = _cargar(tmp_path, variante)        # un Fact no mantiene vivo su Environment
    (p,) = _hechos(env, "parametros-aprendizaje")
    assert (p["aprendizaje-activo"], p["umbral-olvido"], p["tasa-decaimiento"]) == ("FALSE", -3.0, 0.5)


@pytest.mark.parametrize("asignacion", [
    "aprendizaje-activo=quizas", "max-referencias=2.5", "umbral-olvido", "nivel=alt", "inventada=1",
])
def test_set_invalido(asignacion):
    with pytest.raises(ValueError):
        _generar(asignacion)


# --- Verificación (§10.1) -----------------------------------------------------

def test_verificacion_limpia(onto, plantillas):
    anomalias, avisos = on.verificar(onto, plantillas)
    assert anomalias == []
    assert not any("pendientes" in a for a in avisos)   # con chunk (I4) no falta ninguna plantilla


def test_verificar_cli():
    assert on.main(["--verificar"]) == 0



# --- Prueba por mutación del verificador (experimento de cierre de I0) -------
# Cada mutación introduce un error conocido en una copia del TTL o de 00_main.clp
# y comprueba que el verificador lo detecta con la categoría esperada.

def _cambiar(sujeto, prop, valor):
    return lambda g: g.set((A[sujeto], A[prop], valor))


def _anadir(sujeto, prop, valor):
    return lambda g: g.add((A[sujeto], A[prop], valor))


def _quitar(sujeto, prop=None):
    return lambda g: g.remove((A[sujeto], A[prop] if prop else None, None))


def _decimal(x):
    return Literal(str(x), datatype=XSD.decimal)


def _sin_umbrales_humitat(g):
    for nivel in on.NIVELES:
        g.remove((A[f"llindar-humitat-sol-{nivel}"], None, None))


MUTACIONES_TTL = [
    ("valor fuera de la enumeración", _cambiar("cultivo-s1", "sensibilidad", Literal("altisim")), "enumeracion"),
    ("propiedad no declarada", _anadir("cultivo-s1", "color", Literal("verd")), "vocabulario"),
    ("dos valores en una funcional", _anadir("obj-estabilitat", "prioridad", Literal(6)), "funcional"),
    ("decimal en un slot entero", _cambiar("seguidor-s1", "max-movimientos-hora", _decimal(4.0)), "rango"),
    ("objeto de otra clase", _cambiar("s1", "tiene-cultivo", A["seguidor-s1"]), "rango"),
    ("propiedad de otra clase", _anadir("s1", "prioridad", Literal(1)), "dominio"),
    ("dos clases disjuntas", lambda g: g.add((A["cultivo-s1"], RDF.type, A.Umbral)), "disyuncion"),
    ("falta un slot obligatorio", _quitar("req-vent", "nivel"), "completitud"),
    ("hueco entre umbrales", _cambiar("llindar-vent-alt", "limite-inferior", _decimal(-15.0)), "umbrales"),
    ("solape entre umbrales", _cambiar("llindar-vent-alt", "limite-inferior", _decimal(-25.0)), "umbrales"),
    ("umbral sin +inf", _anadir("llindar-vent-critic", "limite-superior", _decimal(100.0)), "umbrales"),
    ("nivel repetido", _cambiar("llindar-vent-mitja", "nivel", Literal("alt")), "umbrales"),
    ("dos referencias en una variable", _cambiar("llindar-vent-alt", "referencia", Literal("absoluta")), "umbrales"),
    ("ciclo en las fases", _cambiar("fase-explicacio", "siguiente", Literal("percepcio")), "fases"),
    ("fase inalcanzable", _cambiar("fase-monitoratge", "siguiente", Literal("proposta")), "fases"),
    ("deliberacio no vuelve a seleccio", _cambiar("fase-deliberacio", "siguiente", Literal("aplicacio")), "fases"),
    ("prioridad duplicada", _cambiar("obj-estabilitat", "prioridad", Literal(4)), "objetivos"),
    ("sector sin seguidor", _quitar("s2", "tiene-seguidor"), "sectores"),
    ("seguidor compartido", _cambiar("s2", "tiene-seguidor", A["seguidor-s1"]), "sectores"),
    ("dato requerido sin umbrales", _sin_umbrales_humitat, "datos-requeridos"),
    ("tolerancia igual al límite de moviment", _cambiar("seguidor-s2", "tolerancia-angulo", _decimal(5.0)), "tolerancia"),
    ("límite de moviment bajo la tolerancia", _cambiar("llindar-moviment-mitja", "limite-inferior", _decimal(1.5)), "tolerancia"),
]

MUTACIONES_CLP = [
    ("nil fuera de allowed-symbols",
     "(slot limite-inferior (type NUMBER SYMBOL) (allowed-symbols nil) (default nil))",
     "(slot limite-inferior (type NUMBER SYMBOL) (default nil))"),
    ("tipo cambiado", "(slot max-movimientos-hora (type INTEGER))", "(slot max-movimientos-hora (type NUMBER))"),
    ("multislot de una funcional", "(slot tiene-cultivo (type SYMBOL))", "(multislot tiene-cultivo (type SYMBOL))"),
    ("falta un slot", "   (slot umbral-viento-critico (type NUMBER))\n", ""),
    ("enumeración incompleta", "(allowed-symbols dura tova)", "(allowed-symbols dura)"),
]


@pytest.fixture(scope="module")
def grafo():
    return on.leer_grafo()


@pytest.mark.parametrize("descripcion, mutar, categoria", MUTACIONES_TTL, ids=[m[0] for m in MUTACIONES_TTL])
def test_mutacion_ttl(grafo, plantillas, descripcion, mutar, categoria):
    copia = Graph()
    copia += grafo
    mutar(copia)
    anomalias, _ = on.verificar(on.ontologia_desde_grafo(copia), plantillas)
    assert categoria in {a.categoria for a in anomalias}, anomalias


@pytest.mark.parametrize("descripcion, original, mutado", MUTACIONES_CLP, ids=[m[0] for m in MUTACIONES_CLP])
def test_mutacion_plantillas(onto, tmp_path, descripcion, original, mutado):
    texto = on.MAIN_CLP.read_text(encoding="utf-8")
    assert texto.count(original) == 1
    ruta = tmp_path / "00_main.clp"
    ruta.write_text(texto.replace(original, mutado), encoding="utf-8")
    anomalias, _ = on.verificar(onto, on.leer_plantillas(ruta))
    assert "plantillas" in {a.categoria for a in anomalias}, anomalias
