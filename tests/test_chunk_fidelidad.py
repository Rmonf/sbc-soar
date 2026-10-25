"""El chunk preserva la competencia (roadmap §6.2, H2 de §11.4) y generaliza entre sectores.

- Batería: cada caso decide lo mismo, paso a paso, con aprendizaje y sin él (variante generada
  con aprendizaje-activo=FALSE). Solo cambian tipo-impasse y chunk-aplicado.
- Rejilla de s3: en dos pasos (aprender y volver a la misma geometría) se comprueba que la
  decisión del chunk es la de la deliberación. Cubre el argumento de §6.2 sin el invariante para
  la acción sin movimiento: el resultado depende solo del par, los beneficios y la relación.
- Generalización: con el TTL actual solo s3 puede empatar (§11.4, transferencia), así que se usa
  una variante con s1 de sensibilidad mitja: un chunk aprendido en s3 se aplica en s1, y si los
  dos sectores empatan igual en el mismo ciclo solo se compila un chunk, con la misma traza en
  depth y breadth.
"""

import copy
import itertools
from collections import Counter

import pytest

import executar_casos as ec
import ontologia as on
import pont_clips as pc
from conftest import CASOS

DECISION = ("accion", "angulo-ordenado", "escalado-humano")
EPISODIO = ("accion", "criterio-determinante", "descartes", "restricciones-activas", "resultado")


@pytest.fixture(scope="module")
def base_c0(tmp_path_factory):
    return on.generar_variante(["aprendizaje-activo=FALSE"], tmp_path_factory.mktemp("c0") / "base_c0.clp")


def _decisiones(pasos):
    res = []
    for p in pasos:
        ordenes = sorted((o["sector"], *(o[k] for k in DECISION)) for o in p.ordenes if o["instante"] == p.instante)
        episodios = sorted((e["sector"], *(sorted(e[k]) if isinstance(e[k], list) else e[k] for k in EPISODIO))
                           for e in p.episodios)
        res.append((ordenes, episodios))
    return res


@pytest.mark.parametrize("id_caso", [c["id"] for c in CASOS])
def test_bateria_decide_igual_sin_aprendizaje(base_c0, id_caso):
    caso = next(c for c in CASOS if c["id"] == id_caso)
    con = ec.ejecutar_caso(caso)
    sin = ec.ejecutar_caso(caso, base=base_c0)
    assert _decisiones(con) == _decisiones(sin)
    assert all(not p.chunks for p in sin)                 # C0 no compila ni aplica chunks


def _paso_s3(t, temp, rad, preu, panel, captacio, ombra):
    return {"instante": t,
            "sectores": {"s3": {"sensores": {"temp-cultiu": {"valor": temp, "calidad": "ok"},
                                             "radiacio": {"valor": rad, "calidad": "ok"}},
                                "panel": {"angulo-actual": panel},
                                "predicciones": {"angle-captacio": captacio, "angle-ombra": ombra}}},
            "predicciones-globales": {"preu-energia": preu}}


REJILLA = list(itertools.product((33, 37), (300, 600, 900), (40, 120), (-30, 0, 20, 30)))


def test_rejilla_s3_el_chunk_decide_como_la_deliberacion(base_c0):
    """Paso 1 en (panel, captación 30°, sombra -30°); paso 2 con el panel donde se ordenó y los
    dos ángulos desplazados lo mismo, de modo que los Δ se repiten."""
    usados = []
    for temp, rad, preu, panel in REJILLA:
        p1 = _paso_s3(0, temp, rad, preu, panel, 30, -30)
        primero = ec.ejecutar_caso({"id": "r", "base": "_base_tranquil", "pasos": [p1]})[0]
        destino = next(o["angulo-ordenado"] for o in primero.ordenes if o["sector"] == "s3")
        d = destino - panel
        caso = {"id": "rejilla", "base": "_base_tranquil",
                "pasos": [p1, _paso_s3(5, temp, rad, preu, destino, 30 + d, -30 + d)]}
        con = ec.ejecutar_caso(caso)
        sin = ec.ejecutar_caso(caso, base=base_c0)
        assert _decisiones(con) == _decisiones(sin), (temp, rad, preu, panel)
        usados.append(ec.episodio_de(con[1], "s3")["chunk-aplicado"])
    usados = [u for u in usados if u != "nil"]
    # la rejilla ejercita el chunk, también con la acción sin movimiento frente a cada candidato
    assert len(usados) >= len(REJILLA) // 3
    assert any(u.startswith("chunk-mantenir-posicio-") and "-orientar-produccio-" in u for u in usados)
    assert any(u.startswith("chunk-mantenir-posicio-") and "-orientar-ombra-" in u for u in usados)


@pytest.fixture(scope="module")
def base_s1_mitja(tmp_path_factory):
    texto = pc.BASE.read_text(encoding="utf-8")
    original = "(id cultivo-s1) (nombre-cultivo tomate) (fase-fenologica floracion) (sensibilidad alt)"
    assert original in texto
    ruta = tmp_path_factory.mktemp("s1") / "base_s1_mitja.clp"
    ruta.write_text(texto.replace(original, original.replace("(sensibilidad alt)", "(sensibilidad mitja)")),
                    encoding="utf-8")
    return ruta


SOMBRA_FRENTE_A_PRODUCCION = {"sensores": {"radiacio": {"valor": 600, "calidad": "ok"}}}
CH = "chunk-orientar-ombra-mitja-orientar-produccio-alt-similar"


def _empate(sector):
    """Estrés mitja y oportunidad alt con el panel a 0°: sombra y producción a 30° (caso 55).
    Temperaturas: viña (umbral 35) 32 °C; tomate (umbral 30) 28 °C."""
    s = copy.deepcopy(SOMBRA_FRENTE_A_PRODUCCION)
    s["sensores"]["temp-cultiu"] = {"valor": 32 if sector == "s3" else 28, "calidad": "ok"}
    return s


def test_chunk_aprendido_en_s3_se_aplica_en_s1(base_s1_mitja):
    caso = {"id": "transferencia", "base": "_base_tranquil", "pasos": [
        {"instante": 0, "sectores": {"s3": _empate("s3")}},
        {"instante": 5, "sectores": {"s3": {"panel": {"angulo-actual": -30}}, "s1": _empate("s1")}}]}
    pasos = ec.ejecutar_caso(caso, base=base_s1_mitja)
    assert all(not p.errores for p in pasos)
    assert ec.episodio_de(pasos[0], "s3")["tipo-impasse"] == "tie"
    e1 = ec.episodio_de(pasos[1], "s1")
    assert (e1["accion"], e1["tipo-impasse"], e1["chunk-aplicado"]) == ("orientar-ombra", "nil", CH)


def test_dos_sectores_con_el_mismo_empate_compilan_un_chunk(base_s1_mitja):
    caso = {"id": "duplicado", "base": "_base_tranquil", "pasos": [
        {"instante": 0, "sectores": {"s1": _empate("s1"), "s3": _empate("s3")}}]}
    trazas = []
    for estrategia in ("depth", "breadth"):
        (paso,) = ec.ejecutar_caso(caso, estrategia, base=base_s1_mitja)
        assert not paso.errores
        assert [c["id"] for c in paso.chunks] == [CH]
        assert {ec.episodio_de(paso, s)["tipo-impasse"] for s in ("s1", "s3")} == {"tie"}
        trazas.append(Counter(ec.bloques(paso.traza)))
        assert sum(b.startswith("Aprenentatge") for b in ec.bloques(paso.traza)) == 1
    assert trazas[0] == trazas[1]
