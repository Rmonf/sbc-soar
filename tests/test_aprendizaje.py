from test_casos import CASOS

from sbc import ejecutar_caso
from simulador import simular
from sistema import Sistema


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


def test_dia_simulado_mismas_decisiones_y_menos_empates():
    resultados = {}
    for aprendizaje in (True, False):
        pasos = simular(Sistema(aprendizaje=aprendizaje), semilla=0)
        resultados[aprendizaje] = ([sorted((s, o["accion"], o["angulo-ordenado"]) for s, o in r["ordenes"].items())
                                    for r in pasos],
                                   sum(e["tipo-impasse"] == "tie" for r in pasos for e in r["episodios"].values()))
    assert resultados[True][0] == resultados[False][0]
    assert resultados[True][1] < resultados[False][1]
