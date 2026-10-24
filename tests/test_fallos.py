"""Fallos inyectables (roadmap §9): cada fallo del calendario produce su efecto simbólico en CLIPS."""

import pytest

import bucle
import simulador as sm

CALENDARIO = [
    {"tipo": "moviment-no-ordenat", "sector": "s3", "inicio-min": 300, "durada-min": 5},
    {"tipo": "sensor-fallada", "sector": "s2", "variable": "vent", "inicio-min": 450, "durada-min": 10},
    {"tipo": "actuador-alarma", "sector": "s1", "inicio-min": 540, "durada-min": 30},
    {"tipo": "panell-sense-comunicacio", "sector": "s2", "inicio-min": 600, "durada-min": 30},
    {"tipo": "panell-lectura-antiga", "sector": "s2", "inicio-min": 660, "durada-min": 30},
    {"tipo": "tempesta", "inicio-min": 720, "durada-min": 60, "vent": 85},
    {"tipo": "actuador-encallat", "sector": "s1", "inicio-min": 360, "durada-min": 180},
    {"tipo": "persones", "sector": "s3", "inicio-min": 720, "durada-min": 60},
]


@pytest.fixture(scope="module")
def ejecucion():
    config = sm.cargar_config()
    config["dias"] = 0.6                                   # hasta las 14:24
    f = config["fallos"]
    for clave in ("prob-sensor-fallada", "prob-sensor-degradat", "prob-sensor-antic", "prob-sensor-absent"):
        f[clave] = 0.0
    f["prob-dia"] = {k: 0.0 for k in f["prob-dia"]}
    config["meteo"]["prob-tempesta-dia"] = 0.0             # solo la tormenta del calendario
    f["calendari"] = CALENDARIO
    ej = bucle.ejecutar(1, config)
    assert ej.errores == ""
    return ej


def _episodios(ej, sector, desde, hasta):
    return [e for e in ej.episodios if e["sector"] == sector and desde <= e["instante"] < hasta]


def test_sensor_fallado_da_dades_insuficients(ejecucion):
    for e in _episodios(ejecucion, "s2", 450, 460):
        assert "incertesa-dades:critic" in e["situacion"] and e["tipo-impasse"] == "dades-insuficients"


def test_movimiento_no_ordenado(ejecucion):
    """De noche el panel está quieto: la orden de t−1 no movía, así que la evidencia es
    moviment-no-ordenat (§5.2)."""
    (previo,) = _episodios(ejecucion, "s3", 295, 300)
    assert previo["angulo-ordenado"] == previo["angulo-previo"]
    assert previo["resultado"] == "fallada-actuador"
    assert "fallada-actuador=moviment-no-ordenat" in ejecucion.traza
    (e,) = _episodios(ejecucion, "s3", 300, 305)
    assert "fallada-actuador:alt" in e["situacion"]


def test_actuador_en_alarma(ejecucion):
    for e in _episodios(ejecucion, "s1", 540, 570):
        assert "fallada-actuador:alt" in e["situacion"] and e["accion"] == "diagnosticar"


def test_panel_sin_comunicacion_o_antiguo(ejecucion):
    for e in _episodios(ejecucion, "s2", 600, 630) + _episodios(ejecucion, "s2", 665, 690):
        assert e["tipo-impasse"] == "dades-insuficients" and e["angulo-ordenado"] == "nil"
        assert e["angulo-previo"] == "nil"
    assert "incertesa-dades=observacio-panel:absent" in ejecucion.traza
    assert "incertesa-dades=observacio-panel:antiga" in ejecucion.traza


def test_tormenta_da_r2(ejecucion):
    episodios = [e for s in sm.SECTORES for e in _episodios(ejecucion, s, 720, 780)]
    assert any("risc-mecanic:critic" in e["situacion"] and "R2" in e["restricciones-activas"]
               for e in episodios)
    assert not any(e["accion"] in ("orientar-produccio", "orientar-ombra") for e in episodios)


def test_actuador_encallado_da_fallada_y_r3(ejecucion):
    """Una orden que mueve no se cumple: fallada-actuador (ordre-incomplerta) al paso siguiente, y
    después R3 rechaza los candidatos que mueven."""
    episodios = _episodios(ejecucion, "s1", 360, 540)
    assert any(e["resultado"] == "fallada-actuador" for e in episodios)
    assert "fallada-actuador=ordre-incomplerta" in ejecucion.traza
    assert any("fallada-actuador:alt" in e["situacion"] for e in episodios)
    assert any("R3" in e["restricciones-activas"] for e in episodios)


def test_personas_con_tormenta(ejecucion):
    """Personas debajo con viento crítico: R1 contra R2 (constraint-failure) o, si la defensa no
    mueve, R1 no se activa; nunca se mueve con personas."""
    for e in _episodios(ejecucion, "s3", 720, 780):
        assert "risc-persones:critic" in e["situacion"]
        if e["tipo-impasse"] == "constraint-failure":
            assert e["escalado-humano"] == "TRUE" and e["accion"] == "mantenir-posicio"
        assert e["accion"] in ("mantenir-posicio", "diagnosticar", "posicio-seguretat")
