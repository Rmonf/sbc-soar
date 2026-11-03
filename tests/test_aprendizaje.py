from test_casos import CASOS

from sbc import ejecutar_caso


def decisiones_y_empates(aprendizaje):
    decisiones, empates = [], 0
    for ruta in CASOS:
        for r in ejecutar_caso(ruta, aprendizaje=aprendizaje)[1]:
            decisiones.append(sorted((s, o["accion"], o["angulo-ordenado"]) for s, o in r["ordenes"].items()))
            empates += sum(e["tipo-impasse"] == "tie" for e in r["episodios"].values())
    return decisiones, empates


def test_casos_mismas_decisiones_y_menos_empates():
    con, empates_con = decisiones_y_empates(True)
    sin, empates_sin = decisiones_y_empates(False)
    assert con == sin
    assert empates_con < empates_sin
