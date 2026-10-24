"""Simulador heurístico (roadmap §9): reproducibilidad, rangos físicos y efecto de las órdenes."""

import copy

import numpy as np
import pytest

import pont_clips as pc
import simulador as sm


@pytest.fixture(scope="module")
def config():
    c = sm.cargar_config()
    c["dias"] = 2
    return c


def _serie(sim, pasos):
    res = []
    for _ in range(pasos):
        res.append(sim.observaciones())
        sim.aplicar([])
    return res


def test_misma_semilla_misma_serie(config):
    assert _serie(sm.Simulador(3, config), 300) == _serie(sm.Simulador(3, config), 300)


def test_semillas_distintas_series_distintas(config):
    assert _serie(sm.Simulador(3, config), 300) != _serie(sm.Simulador(4, config), 300)


def test_rangos_fisicos(config):
    m = sm.Simulador(0, config).meteo
    assert m.radiacion.min() >= 0 and m.radiacion.max() <= config["meteo"]["radiacio-max"]
    assert m.viento.min() >= 0 and m.lluvia.min() >= 0 and m.precio.min() >= 0
    assert m.radiacion[m.elevacion == 0].max() == 0          # de noche no hay sol
    assert np.all(np.abs(m.angulo_captacion) <= 60)
    sim = sm.Simulador(0, config)
    for _ in range(sim.pasos):
        sim.aplicar([])
        for e in sim.sectores.values():
            assert 0 <= e["humitat"] <= 100


def test_estado_inicial_desde_el_ttl(config):
    sim = sm.Simulador(0, config)
    assert sim.instal["s2"]["cultivo"] == "cultivo-s2" and sim.instal["s2"]["umbral-temp-estres"] == 26.0
    assert sim.instal["s1"]["tolerancia-angulo"] == 2.0


def _a_mediodia(config):
    sim = sm.Simulador(0, config)
    while sim.meteo.horas[sim.k] < 12:
        sim.aplicar([])
    return sim


def _orden(sim, s, angulo):
    return {"sector": s, "instante": sim.instante(), "angulo-ordenado": angulo}


def test_la_sombra_enfria_y_ahorra_agua(config):
    sombra, sol = _a_mediodia(config), _a_mediodia(config)
    for s in sm.SECTORES:
        sombra.sectores[s]["angulo"] = sombra.meteo.angulo_sombra(sombra.k)
        sol.sectores[s]["angulo"] = float(sol.meteo.angulo_captacion[sol.k])
    for s in sm.SECTORES:
        assert sombra.temp_cultivo(s) < sol.temp_cultivo(s)
        assert sombra.produccion(s) < sol.produccion(s)
    for _ in range(24):                                       # dos horas manteniendo la posición
        sombra.aplicar([]); sol.aplicar([])
    for s in sm.SECTORES:
        assert sombra.sectores[s]["humitat"] > sol.sectores[s]["humitat"]


def test_el_panel_va_al_angulo_ordenado(config):
    sim = _a_mediodia(config)
    sim.aplicar([_orden(sim, "s1", -30.0), _orden(sim, "s2", "nil")])
    assert abs(sim.sectores["s1"]["angulo"] + 30) <= sim.instal["s1"]["tolerancia-angulo"]
    assert sim.sectores["s2"]["angulo"] == 0.0               # nil = no mover


def test_orden_dentro_de_la_tolerancia_no_mueve(config):
    """Una orden a menos de la tolerancia del ángulo real (p. ej., mantener con el ángulo
    observado, que lleva ruido) no mueve el panel; una fuera de ella, sí."""
    sim = _a_mediodia(config)
    tol = sim.instal["s1"]["tolerancia-angulo"]
    sim.aplicar([_orden(sim, "s1", tol - 0.1), _orden(sim, "s2", tol + 3)])
    assert sim.sectores["s1"]["angulo"] == 0.0
    assert sim.sectores["s2"]["angulo"] != 0.0


def test_el_orden_de_las_ordenes_no_importa(config):
    """El orden en que llegan las órdenes (depende de la estrategia de agenda) no cambia el efecto."""
    a, b = _a_mediodia(config), _a_mediodia(config)
    ordenes = [_orden(a, s, -20.0) for s in sm.SECTORES]
    a.aplicar(ordenes)
    b.aplicar(list(reversed(ordenes)))
    assert a.sectores == b.sectores


def test_las_observaciones_entran_en_clips(config):
    """El formato de observaciones() es el que espera Pont.paso, y todas tienen calidad."""
    sim = _a_mediodia(config)
    obs = sim.observaciones()
    assert all("calidad" in s for s in obs["sensores"])
    paso = pc.Pont().paso(obs["instante"], obs["sensores"], obs["paneles"], obs["predicciones"])
    assert paso.errores == "" and len(paso.ordenes) == 3


def test_fallos_no_cambian_la_meteorologia(config):
    """Cada proceso aleatorio tiene su generador: consumir el de fallos no altera el tiempo."""
    a, b = sm.Simulador(5, config), sm.Simulador(5, copy.deepcopy(config))
    b.rng_fallos.random(1000)
    assert np.array_equal(a.meteo.viento, b.meteo.viento)
