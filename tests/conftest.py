"""Fixtures compartidas: cada caso de casos/ se ejecuta una sola vez por sesión de pytest."""

import pytest

import executar_casos as ec

CASOS = ec.cargar_casos()


@pytest.fixture(scope="session")
def resultados():
    """id del caso -> (caso, resultados por paso) con la estrategia de simulacio.json."""
    return {c["id"]: (c, ec.ejecutar_caso(c)) for c in CASOS}
