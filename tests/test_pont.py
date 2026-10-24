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
