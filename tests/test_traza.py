"""La traza contiene todos los datos del episodio y se escribe un bloque por episodio (§5.9)."""

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
        expandido = ec.expandir_paso(caso, p)
        assert sum(b.startswith("Fets d'entrada:") for b in ec.bloques(r.traza)) == len(expandido["sectores"])
        for sector in expandido["sectores"]:
            _comprobar_bloque(r, sector, expandido)


def _comprobar_bloque(r, sector, expandido):
    e = ec.episodio_de(r, sector)
    l = _lineas(ec.bloque_de(r.traza, sector))
    assert l["Fets d'entrada"].startswith(f"t={e['instante']}, sector={e['sector']}, ")
    if e["angulo-previo"] == "nil":
        assert l["Fets d'entrada"].endswith("panell=desconegut")
    else:
        assert f"panell={e['angulo-previo']} " in l["Fets d'entrada"]
    for s in expandido["sensores"]:
        if s["sector"] != sector:
            continue
        marca = "" if s["calidad"] == "ok" else f" ({s['calidad']})"
        assert f"{s['variable']}={float(s['valor'])}{marca}" in l["Fets d'entrada"]
    assert _conjunto(l["Diagnosi"]) == set(e["situacion"])
    assert _conjunto(l["Candidats"]) == set(e["alternativas"])
    assert _conjunto(l["Descartats"]) == set(e["descartes"])
    criterio = "-" if e["criterio-determinante"] == "nil" else e["criterio-determinante"]
    assert l["Decisio"] == f"{e['accion']}   Criteri: {criterio}"
    escalado = "si" if e["escalado-humano"] == "TRUE" else "no"
    assert l["Ordre"] == f"sector={e['sector']}, angle={e['angulo-ordenado']}, escalat a persona: {escalado}"
    estres = {x for x in e["situacion"] if x.startswith("estres")}
    agronomica, cultivo = l["Vista agronomica"].split("; benefici cultiu=")
    assert _conjunto(agronomica.removeprefix("estres=")) == estres
    assert cultivo == f"{e['beneficio-cultivo']}; renuncia cultiu={e['perdida-cultivo']}"
    impasse = l["Impasse"]
    assert (impasse == "-") == (e["tipo-impasse"] == "nil")
    if e["tipo-impasse"] != "nil":
        assert impasse.startswith(f"{e['tipo-impasse']} (")
    energia, restricciones = l["Vista energetica"].split("; restriccions actives: ")
    assert energia == f"benefici energia={e['beneficio-energia']}; renuncia energia={e['perdida-energia']}"
    assert _conjunto(restricciones) == set(e["restricciones-activas"])
