"""S5 frente a S6 (roadmap §5.6): S6 niega exactamente la condición de S5.

S6 solo se bloquea si hay exactamente dos no dominados y un chunk aplicable a ese par; con tres
o más no dominados, S6 abre el tie como siempre, aunque un chunk encaje con dos de ellos. Con el
conocimiento actual no hay empates de tres (la acción sin movimiento que no hereda nada queda
dominada por la acción útil, y la que hereda domina por cercanía al candidato que la sirve), así
que la prueba ejercita SELECCIO sola: carga MAIN, la configuración y SELECCIO, y construye a mano
los candidatos, las valoraciones y el chunk. Se quitan las definiciones de fase para que el
control de MAIN no enfoque módulos que no están cargados.
"""

import pont_clips as pc

CHUNK = ("(chunk (id chunk-orientar-ombra-mitja-orientar-produccio-alt-similar) "
         "(accion-preferida orientar-ombra) (beneficio-preferida mitja) "
         "(accion-descartada orientar-produccio) (beneficio-descartada alt) (relacion-delta similar) "
         "(criterio proteccio-cultiu) (estrategia-resolucion prioritat-objectius) (instante 0) (referencias 0))")


def _seleccio(candidatos: list[tuple[str, str, str, str, str]]):
    """Ejecuta SELECCIO con S0 en seleccio, el chunk y los candidatos (id, acción, mecánico,
    cultivo, energía) de s3, todos con Δ = 30 desde el panel a 0°."""
    import clips
    env = clips.Environment()
    for ruta in (pc.CLIPS_DIR / "00_main.clp", pc.BASE, pc.CLIPS_DIR / "06_seleccio.clp"):
        env.load(str(ruta))
    env.reset()
    env.eval("(do-for-all-facts ((?f definicion-fase)) TRUE (retract ?f))")
    env.eval("(do-for-all-facts ((?f estado-soar)) TRUE (retract ?f))")
    env.eval("(assert (ciclo-temporal (instante 5)))")
    env.eval(f"(assert {CHUNK})")
    for ident, accion, mec, cul, ene in candidatos:
        env.eval(f"(assert (operador-candidato (id {ident}) (en-estado S0) (sector s3) (accion {accion}) "
                 f"(angulo-objetivo 30) (estado-candidato candidat)))")
        env.eval(f"(assert (valoracion (evalua-operador {ident}) (beneficio-mecanico {mec}) "
                 f"(beneficio-cultivo {cul}) (beneficio-energia {ene}) (coste-movimiento alt) "
                 f"(desplazamiento 30.0)))")
    # S0 entra en seleccio con las valoraciones ya asertadas, como en el ciclo real: los test de
    # SELECCIO se evalúan al emparejar el patrón de fase y no se reevalúan después (§14)
    env.eval("(assert (estado-soar (id S0) (fase seleccio) (subfase feta)))")
    env.eval("(focus SELECCIO)")
    env.run()
    hechos = {}
    for f in env.facts():
        hechos.setdefault(f.template.name, []).append(dict(f))
    return hechos


def test_empate_de_dos_con_chunk_aplica_s5():
    h = _seleccio([("s3-ombra", "orientar-ombra", "baix", "mitja", "baix"),
                   ("s3-prod", "orientar-produccio", "baix", "baix", "alt")])
    assert "impasse" not in h
    (better,) = [p for p in h["preferencia"] if str(p["origen"]) == "chunk"]
    assert (str(better["operador-referencia"]), str(better["operador-comparado"])) == ("s3-ombra", "s3-prod")
    seleccionados = [str(c["id"]) for c in h["operador-candidato"] if str(c["estado-candidato"]) == "seleccionat"]
    assert seleccionados == ["s3-ombra"]


def test_empate_de_tres_abre_tie_aunque_un_chunk_encaje_con_dos():
    h = _seleccio([("s3-ombra", "orientar-ombra", "baix", "mitja", "baix"),
                   ("s3-prod", "orientar-produccio", "baix", "baix", "alt"),
                   ("s3-seg", "posicio-seguretat", "mitja", "baix", "baix")])
    assert not [p for p in h.get("preferencia", []) if str(p["origen"]) == "chunk"]
    (impasse,) = h["impasse"]
    assert str(impasse["tipo-impasse"]) == "tie"
    assert sorted(map(str, impasse["operadores-en-conflicto"])) == ["s3-ombra", "s3-prod", "s3-seg"]
