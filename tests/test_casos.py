"""Regresión de la batería de casos (roadmap §10.2)."""

import copy

import pytest

import executar_casos as ec
from conftest import CASOS


def test_bateria_minima():
    assert len(CASOS) >= 8                               # enunciado 3.10
    assert all(c["requisito"] for c in CASOS)            # trazabilidad (§10.2)


@pytest.mark.parametrize("id_caso", [c["id"] for c in CASOS])
def test_caso(resultados, id_caso):
    caso, pasos = resultados[id_caso]
    assert ec.comprobar(caso, pasos) == []


def test_reglas_no_disparadas(resultados):
    """En I1 solo quedan sin disparar las reglas de MAIN que abren y cierran impasses (§10.1)."""
    disparadas = {r for _, pasos in resultados.values() for p in pasos for r in p.reglas}
    todas = next(iter(resultados.values()))[1][0].modulo_de
    assert {r for r in todas if r not in disparadas} == {"abrir-deliberacio", "escalar-impasse"}


@pytest.mark.parametrize("slot, valor", [
    ("accion", "mantenir-posicio"), ("angulo-ordenado", 30.0), ("restricciones-activas", []),
    ("descartes", ["posicio-seguretat:estabilitat"]), ("criterio-determinante", "estabilitat"),
])
def test_comprobar_detecta_discrepancias(resultados, slot, valor):
    """La comparación no es vacía: una expectativa alterada del caso del anexo B falla."""
    caso, pasos = resultados["caso_08_anexo_b"]
    mutado = copy.deepcopy(caso)
    mutado["pasos"][0]["esperado"][slot] = valor
    assert ec.comprobar(mutado, pasos)


def test_comprobar_detecta_prohibido(resultados):
    caso, pasos = resultados["caso_08_anexo_b"]
    mutado = copy.deepcopy(caso)
    mutado["pasos"][0]["prohibido"] = {"accion": ["posicio-seguretat"]}
    assert ec.comprobar(mutado, pasos)


def test_a1_invariancia():
    """Hipótesis de A1 (§11.3): depth y breadth cambian la secuencia pero no lo que se decide."""
    import experiments
    res = experiments.a1(["depth", "breadth"])
    for c in res["ciclos"]:
        assert c["multiconjunto_igual"] and c["ordenes_iguales"] and c["episodios_iguales"], c["caso"]
        assert c["traza_igual"], c["caso"]
    assert not all(c["secuencia_igual"] for c in res["ciclos"])   # el experimento discrimina
