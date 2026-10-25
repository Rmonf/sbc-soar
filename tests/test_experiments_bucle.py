"""Piloto, potencia y A1 en bucle cerrado (roadmap §11.2, §11.3): pruebas de humo cortas.
Los experimentos completos (10 semillas × 7 días) se ejecutan con experiments.py."""

import pytest

import experiments


def test_clopper_pearson():
    bajo, alto = experiments.clopper_pearson(0, 10)
    assert bajo == 0.0 and alto == pytest.approx(0.3085, abs=1e-3)        # ≈ 3/n
    bajo, alto = experiments.clopper_pearson(10, 10)
    assert alto == 1.0 and bajo == pytest.approx(0.6915, abs=1e-3)


def test_tamano_muestra():
    # (1,96 + 0,84)² ≈ 7,85: σ_d = δ da 8, que sube al mínimo de 30
    assert experiments.tamano_muestra(1.0, 1.0) == 30
    assert experiments.tamano_muestra(3.0, 1.0) == 71
    assert experiments.tamano_muestra(1.0, 0.0) == 30


def test_piloto_corto():
    res = experiments.piloto([0, 1], dias=0.2)
    assert res["violaciones"]["total"] == 0 and not res["errores"]
    assert list(res["metricas"])[0] == "tie-100"                         # la principal primero
    for m in res["metricas"].values():
        assert m["n"] >= 30 and m["sigma_d_cota"] == pytest.approx(2 ** 0.5 * m["sigma"])
    assert "válida si ρ ≥ 0" in experiments.resumen_piloto(res)


def test_a1_bucle_corto():
    res = experiments.a1_bucle(["depth", "breadth"], [0], dias=0.2)
    assert res["por_estrategia"]["breadth"]["discrepancias"] == 0
    assert res["por_estrategia"]["breadth"]["ciclos_secuencia_igual"] < res["por_estrategia"]["breadth"]["ciclos"]


def test_aprenentatge_corto():
    """C0, C1 y C2 en dos semillas cortas: sin violaciones, decisiones idénticas y C0 sin chunks."""
    res = experiments.aprenentatge([0, 1], dias=0.2, configuraciones={
        "C0": ["aprendizaje-activo=FALSE"], "C1": ["umbral-olvido=-100"], "C2": []})
    assert not res["errores"] and not any(res["violaciones"].values())
    assert res["h2"]["C1"]["semillas_identicas"] == 2 and res["h2"]["C2"]["semillas_identicas"] == 2
    assert res["metricas"]["C0"]["chunks-compilados"]["mediana"] == 0
    assert "H2, fidelidad" in experiments.resumen_aprenentatge(res)
