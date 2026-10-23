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
