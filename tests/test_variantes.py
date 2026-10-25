"""Variantes del experimento de agenda (roadmap §11.3): cada regla de clips/variants/ que copia
una de producción es textualmente igual a ella salvo la línea declare, y A3s solo cambia el
orden de disparo."""

import re
from collections import Counter

import pytest

import executar_casos as ec
import experiments
import pont_clips as pc

VARIANTS = pc.CLIPS_DIR / "variants"
DECLARE = re.compile(r"\n   \(declare \(salience (-?\d+)\)\)")


def reglas(fichero) -> dict[str, str]:
    """Texto de cada defrule de un fichero, hasta la primera línea en blanco."""
    texto = fichero.read_text(encoding="utf-8")
    return {m.group(1): texto[m.start(): (texto.find("\n\n", m.start()) + 1 or len(texto) + 1) - 1].rstrip("\n")
            for m in re.finditer(r"^\(defrule (\S+)\n", texto, re.M)}


PRODUCCION = {n: r for f in sorted(pc.CLIPS_DIR.glob("[01][0-9]_*.clp")) for n, r in reglas(f).items()}


def copias(variante: str) -> dict[str, tuple[int, str]]:
    """Reglas de la variante que tienen el nombre de una de producción: (salience, texto sin declare)."""
    res = {}
    for nombre, texto in reglas(VARIANTS / f"{variante}.clp").items():
        if nombre in PRODUCCION:
            m = DECLARE.search(texto)
            res[nombre] = (int(m.group(1)) if m else 0, DECLARE.sub("", texto, count=1))
    return res


def test_a3s_copias_textuales():
    c = copias("a3s")
    refinamientos = {"ELABORACIO::reforzar-risc-mecanic", "ELABORACIO::refinar-oportunitat-preu",
                     "ELABORACIO::anotar-estado-mecanico"}
    restricciones = {n for n in PRODUCCION if re.match(r"AVALUACIO::r[1-5]-", n)}
    assert len(restricciones) == 6 and set(c) == refinamientos | restricciones
    for nombre, (salience, texto) in c.items():
        assert texto == PRODUCCION[nombre], nombre
        assert salience == (-20 if nombre in restricciones else -10)


def test_produccion_sin_salience():
    """§4.2: todo el código de producción usa salience 0."""
    for f in pc.CLIPS_DIR.glob("[01][0-9]_*.clp"):
        assert "salience" not in re.sub(r";.*", "", f.read_text(encoding="utf-8")), f.name


def test_a3s_carga_y_redefine():
    pont = pc.Pont("depth", variante="a3s")
    assert len(pont.modulo_de) == len(pc.Pont("depth").modulo_de)          # redefine, no añade
    assert "(declare (salience -20))" in str(pont.env.find_rule("AVALUACIO::r1-rechazar-con-personas"))
    assert "(declare (salience -10))" in str(pont.env.find_rule("ELABORACIO::refinar-oportunitat-preu"))


@pytest.mark.parametrize("caso_id", ["caso_05_vent_alt", "caso_42_r1_personas_viento_alt",
                                     "caso_58_tres_impasses", "caso_80_chunk_olvidado_y_reaprendido"])
def test_a3s_invariante_en_casos(caso_id):
    caso = next(c for c in ec.cargar_casos() if c["id"] == caso_id)
    for ref, otro in zip(ec.ejecutar_caso(caso, "depth"), ec.ejecutar_caso(caso, "depth", variante="a3s")):
        c = experiments.comparar_paso(ref, otro)
        assert c["multiconjunto_igual"] and c["ordenes_iguales"] and c["episodios_iguales"] and c["traza_igual"]


def test_a3s_cambia_el_orden():
    """La salience sí cambia la secuencia en un ciclo con restricciones (R1 y viento)."""
    caso = next(c for c in ec.cargar_casos() if c["id"] == "caso_42_r1_personas_viento_alt")
    ref, otro = ec.ejecutar_caso(caso, "depth")[0], ec.ejecutar_caso(caso, "depth", variante="a3s")[0]
    assert ref.reglas != otro.reglas and Counter(ref.reglas) == Counter(otro.reglas)


# --- B0 -----------------------------------------------------------------------

def _caso(caso_id):
    return next(c for c in ec.cargar_casos() if c["id"] == caso_id)


def _decision(pasos, sector, i=0):
    return next(o["accion"] for o in pasos[i].ordenes if o["sector"] == sector and o["instante"] == pasos[i].instante)


def test_b0_copias_textuales():
    c = copias("b0")
    restricciones = {n for n in PRODUCCION if re.match(r"AVALUACIO::r[1-5]-", n)}
    assert set(c) == restricciones | {"SELECCIO::descartar-resto"}
    for nombre, (salience, texto) in c.items():
        assert texto == PRODUCCION[nombre], nombre
        assert salience == (10 if nombre in restricciones else 0)


def test_b0_salience_es_6_menos_prioridad():
    """Cada regla de elección de B0 tiene salience 6 − prioridad de su objetivo en el TTL, por debajo
    de las restricciones, y hay una por objetivo salvo seguretat-persones (solo prohibe, R1 y R5)."""
    pont = pc.Pont("depth", variante="b0")
    prioridad = {str(f["nombre-objetivo"]): int(f["prioridad"]) for f in pont.env.facts()
                 if f.template.name == "objetivo-activo"}
    eleccion = {n.split("b0-elegir-")[1]: s for n, (s, _) in
                {n: (int(DECLARE.search(t).group(1)), t) for n, t in reglas(VARIANTS / "b0.clp").items()
                 if "b0-elegir-" in n}.items()}
    assert set(eleccion) == set(prioridad) - {"seguretat-persones"}
    for objetivo, salience in eleccion.items():
        assert salience == 6 - prioridad[objetivo] and salience < 10


def test_b0_viento_alt_no_critico_elige_seguretat():
    """Caso 05: viento alt (60 km/h, no crítico) en s2: B0 también elige posicio-seguretat."""
    caso = _caso("caso_05_vent_alt")
    b0, nucleo = ec.ejecutar_caso(caso, "depth", variante="b0"), ec.ejecutar_caso(caso, "depth")
    assert _decision(b0, "s2") == _decision(nucleo, "s2") == "posicio-seguretat"
    assert not b0[0].errores


def test_b0_respeta_r1():
    """Caso 42: personas bajo el panel de s2 con viento alt: R1 rechaza posicio-seguretat y B0 no mueve."""
    pasos = ec.ejecutar_caso(_caso("caso_42_r1_personas_viento_alt"), "depth", variante="b0")
    assert _decision(pasos, "s2") == "mantenir-posicio"
    assert "R1" in ec.episodio_de(pasos[0], "s2")["restricciones-activas"]


def test_b0_sin_empate_ni_criterio():
    """Caso 54: el núcleo empata en s3 y delibera; B0 decide por salience (cultivo antes que
    energía), sin impasse ni criterio determinante en la traza."""
    caso = _caso("caso_54_tie_minima_intervencio")
    b0, nucleo = ec.ejecutar_caso(caso, "depth", variante="b0"), ec.ejecutar_caso(caso, "depth")
    assert ec.episodio_de(nucleo[0], "s3")["tipo-impasse"] == "tie"
    e = ec.episodio_de(b0[0], "s3")
    assert e["accion"] == "orientar-ombra" and e["tipo-impasse"] == "nil" and e["criterio-determinante"] == "nil"
    assert "Criteri: -" in ec.bloque_de(b0[0].traza, "s3")


def test_b0_recorre_la_bateria():
    """B0 carga y recorre las fases en toda la batería sin errores, con una orden por sector y ciclo
    y sin abrir nunca DELIBERACIO."""
    for caso in ec.cargar_casos():
        for paso in ec.ejecutar_caso(caso, "depth", variante="b0"):
            assert not paso.errores, caso["id"]
            assert len([o for o in paso.ordenes if o["instante"] == paso.instante]) == 3, caso["id"]
            assert all(e["tipo-impasse"] == "nil" for e in paso.episodios if e["instante"] == paso.instante)
