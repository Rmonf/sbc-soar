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
