"""La traza contiene todos los datos del episodio y se escribe una vez por episodio (§5.9)."""

import pytest

import executar_casos as ec
from conftest import CASOS


def _lineas(traza: str) -> dict[str, str]:
    """Etiqueta -> resto de la línea ("Diagnosi: a, b" -> {"Diagnosi": "a, b"})."""
    return dict(l.split(": ", 1) for l in traza.splitlines() if ": " in l)


def _conjunto(texto: str) -> set[str]:
    return set() if texto == "-" else set(texto.split(", "))


@pytest.mark.parametrize("id_caso", [c["id"] for c in CASOS])
def test_traza_contiene_el_episodio(resultados, id_caso):
    caso, pasos = resultados[id_caso]
    for p, r in zip(caso["pasos"], pasos):
        e = ec.episodio_de(r, ec.sector_de(p))
        assert r.traza.count("Decisio:") == 1
        l = _lineas(r.traza)
        assert l["Fets d'entrada"].startswith(f"t={e['instante']}, sector={e['sector']}, ")
        assert f"panell={e['angulo-previo']} " in l["Fets d'entrada"]
        assert _conjunto(l["Diagnosi"]) == set(e["situacion"])
        assert _conjunto(l["Candidats"]) == set(e["alternativas"])
        assert _conjunto(l["Descartats"]) == set(e["descartes"])
        criterio = "-" if e["criterio-determinante"] == "nil" else e["criterio-determinante"]
        assert l["Decisio"] == f"{e['accion']}   Criteri: {criterio}"
        assert l["Ordre"] == f"sector={e['sector']}, angle={e['angulo-ordenado']}"
        assert l["Vista agronomica"] == (f"benefici cultiu={e['beneficio-cultivo']}; "
                                         f"renuncia cultiu={e['perdida-cultivo']}")
        energia, restricciones = l["Vista energetica"].split("; restriccions actives: ")
        assert energia == f"benefici energia={e['beneficio-energia']}; renuncia energia={e['perdida-energia']}"
        assert _conjunto(restricciones) == set(e["restricciones-activas"])
