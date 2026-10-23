"""Pruebas del generador y del verificador de la ontología (roadmap §2.2, §10.1)."""

from collections import Counter

import pytest

import ontologia as on


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


def test_plantillas_estaticas(plantillas):
    assert set(plantillas) == {
        "sector", "cultivo", "seguidor-solar", "objetivo-activo", "dato-requerido",
        "definicion-fase", "umbral", "parametros-aprendizaje", "estado-soar",
    }
    umbral = plantillas["umbral"]
    assert umbral["limite-inferior"].tipos == {"NUMBER", "SYMBOL"}
    assert umbral["limite-inferior"].simbolos == {"nil"}
    assert umbral["limite-inferior"].opcional
    assert not umbral["nivel"].opcional
    assert plantillas["estado-soar"]["estado-padre"].opcional
    assert plantillas["sector"]["id"].simbolos is None
    assert plantillas["seguidor-solar"]["max-movimientos-hora"].tipos == {"INTEGER"}


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
