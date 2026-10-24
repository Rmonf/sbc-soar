"""Bucle cerrado simulador ↔ CLIPS (roadmap §9)."""

import re

import pytest

import bucle
import pont_clips as pc
import simulador as sm


@pytest.fixture(scope="module")
def un_dia():
    config = sm.cargar_config()
    config["dias"] = 1
    return config, bucle.ejecutar(0, config)


def test_un_dia_sin_errores(un_dia):
    config, ej = un_dia
    pasos = int(24 * 60 / config["dt-min"])
    assert ej.errores == ""
    assert len(ej.ciclos) == pasos
    assert len(ej.ordenes) == 3 * pasos                       # una orden por sector y paso
    assert len(ej.episodios) == 3 * pasos


def test_episodios_en_su_ultima_version(un_dia):
    """Todo episodio salvo los del último paso tiene el resultado verificado en t+1 (§5.2)."""
    config, ej = un_dia
    ultimo = ej.ciclos[-1]["instante"]
    for e in ej.episodios:
        if e["instante"] < ultimo and e["angulo-ordenado"] != "nil":
            assert e["resultado"] in ("ok", "fallada-actuador"), e
    # se conservan los episodios que NETEJA retiró al salir de la ventana episódica
    assert min(e["instante"] for e in ej.episodios) == 0


def test_misma_semilla_misma_ejecucion(un_dia):
    config, ej = un_dia
    otra = bucle.ejecutar(0, config)
    assert otra.episodios == ej.episodios and otra.ordenes == ej.ordenes


def test_python_solo_aserta():
    """Python no modifica ni retracta hechos ni elige acciones (§9): el puente, el simulador y el
    bucle no usan las operaciones de clipspy que cambian hechos existentes."""
    for modulo in (pc, sm, bucle):
        fuente = open(modulo.__file__, encoding="utf-8").read()
        assert not re.search(r"\.retract\(|\.modify_slots\(|\(retract|\(modify", fuente), modulo.__name__


def test_guardar(un_dia, tmp_path):
    config, ej = un_dia
    bucle.guardar(ej, tmp_path)
    for nombre in ("episodios.jsonl", "ordenes.jsonl", "estado.jsonl", "ciclos.jsonl", "traza.txt",
                   "configuracion.json"):
        assert (tmp_path / nombre).exists()
