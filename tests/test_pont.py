"""Puente con CLIPS (roadmap §9)."""

import pytest

import pont_clips as pc


def test_calidad_obligatoria():
    """Sin calidad no se aserta nada: ni la lectura ni el ciclo (§3.2, dato ausente)."""
    pont = pc.Pont()
    with pytest.raises(ValueError, match="sin calidad"):
        pont.paso(0, [{"sector": "s2", "variable": "vent", "valor": 82}])
    assert [f for f in pont.env.facts()
            if f.template.name in ("observacion-sensor", "ciclo-temporal")] == []


def test_minutos_por_ciclo_coincide_con_el_simulador():
    """La activación de los chunks mide el tiempo en ciclos de decisión (§5.10): el defglobal de
    MAIN tiene que ser el Δt del simulador."""
    assert pc.Pont().env.eval("?*minutos-por-ciclo*") == pc.simulacio()["dt-min"]
