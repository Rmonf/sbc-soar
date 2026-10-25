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


def test_biserial_y_holm():
    import numpy as np
    assert experiments.biserial(np.array([1.0, 2.0, 0.0])) == 1.0
    assert experiments.biserial(np.array([-1.0, 1.0])) == 0.0
    assert experiments.biserial(np.zeros(3)) == 0.0
    # Holm: la menor por 3, la siguiente por 2 (y nunca por debajo de la anterior), la última por 1
    assert experiments.holm({"a": 0.01, "b": 0.04, "c": 0.03}) == pytest.approx({"a": 0.03, "b": 0.06, "c": 0.06})


def test_friedman():
    import numpy as np
    iguales = {k: np.arange(10, dtype=float) for k in "abc"}
    assert experiments.friedman(iguales)["pares"] == {}
    distintas = {"a": np.arange(10.0), "b": np.arange(10.0) + 1, "c": np.arange(10.0) + 2}
    res = experiments.friedman(distintas)
    assert res["p_friedman"] < 0.05 and set(res["pares"]) == {"a-b", "a-c", "b-c"}


def test_i5_corto_y_reanudable(tmp_path):
    """Las cuatro etapas de I5 en una semilla corta; la segunda vez todo sale del caché y el
    resultado es el mismo (salvo la línea del recuento de ejecuciones)."""
    texto, correcto = experiments.i5([0], 0.05, tmp_path, ["aprenentatge", "b0", "a3"])
    assert correcto, texto
    assert "Ejecuciones: 6 nuevas" in texto            # C0, C1, C2, B0, C0+A3s y C2+A3s
    texto2, _ = experiments.i5([0], 0.05, tmp_path, ["aprenentatge", "b0", "a3"])
    assert "0 nuevas" in texto2
    quitar = lambda s: [l for l in s.splitlines() if not l.startswith("Ejecuciones")]
    assert quitar(texto) == quitar(texto2)
    assert (tmp_path / "b0" / "resumen.txt").exists() and (tmp_path / "a3" / "resultados.json").exists()
