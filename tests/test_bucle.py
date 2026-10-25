"""Bucle cerrado simulador ↔ CLIPS (roadmap §9)."""

import json
import re

import pytest

import bucle
import metricas
import ontologia as on
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
    """Todo episodio con ángulo ordenado y panel vigente en t+1 tiene el resultado verificado
    (§5.2); sin panel vigente en t+1 queda pendent."""
    config, ej = un_dia
    dt = config["dt-min"]
    vigente = {(o["instante"], p["sector"]) for o in ej.observaciones for p in o["paneles"]
               if p["instante"] == o["instante"]}
    verificados = 0
    for e in ej.episodios:
        if e["angulo-ordenado"] != "nil" and (e["instante"] + dt, e["sector"]) in vigente:
            assert e["resultado"] in ("ok", "fallada-actuador"), e
            verificados += 1
        else:
            assert e["resultado"] == "pendent", e
    assert verificados > 0
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
    for nombre in ("episodios.jsonl", "ordenes.jsonl", "chunks.jsonl", "estado.jsonl", "ciclos.jsonl",
                   "traza.txt", "configuracion.json"):
        assert (tmp_path / nombre).exists()


def test_chunks_exportados(un_dia):
    """Los chunks vivos de cada ciclo y los exportados son coherentes, y cada uso de un chunk es
    de un chunk compilado antes (§6.2)."""
    config, ej = un_dia
    assert all("chunks" in c for c in ej.ciclos)
    assert max(c["chunks"] for c in ej.ciclos) <= len(ej.chunks)
    for e in ej.episodios:
        if e["chunk-aplicado"] != "nil":
            assert any(c["id"] == e["chunk-aplicado"] and c["instante"] < e["instante"] for c in ej.chunks)


def test_sin_aprendizaje_decide_igual(un_dia, tmp_path):
    """C0 (aprendizaje-activo FALSE) toma las mismas decisiones que C2 en bucle cerrado (H2)."""
    config, ej = un_dia
    c0 = bucle.ejecutar(0, config, base=on.generar_variante(["aprendizaje-activo=FALSE"], tmp_path / "c0.clp"))
    assert c0.chunks == [] and c0.errores == ""
    assert metricas.fidelidad(ej, c0)


def test_guardar_y_cargar(tmp_path):
    """Una ejecución guardada se recupera con la misma clave (para reanudar, §11.2) y no con otra."""
    config = sm.cargar_config()
    config["dias"] = 0.05
    ej = bucle.ejecutar(0, config)
    m = metricas.calcular(ej)
    bucle.guardar(ej, tmp_path, m, clave={"base": "C2"})
    m2, ej2 = bucle.cargar(tmp_path, 0, ej.estrategia, config, clave={"base": "C2"})
    assert m2 == json.loads(json.dumps(m))
    assert ej2.ordenes == ej.ordenes and ej2.traza == ej.traza
    assert [c["multiconjunto"] for c in ej2.ciclos] == [c["multiconjunto"] for c in ej.ciclos]
    assert ej2.entorno["cpus"] == ej.entorno["cpus"] and len(ej2.entorno["loadavg-fin"]) == 3
    assert bucle.cargar(tmp_path, 0, ej.estrategia, config, clave={"base": "C0"}) is None
    assert bucle.cargar(tmp_path, 1, ej.estrategia, config, clave={"base": "C2"}) is None
