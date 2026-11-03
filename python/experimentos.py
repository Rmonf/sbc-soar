"""Experimentos de aprendizaje y de agenda. Escriben el resumen en la consola y en resultats/."""

import json
import statistics
from pathlib import Path

import matplotlib
from scipy.stats import wilcoxon

from sbc import ESTRATEGIAS, ejecutar_caso
from simulador import CONFIG, SECTORES, simular
from sistema import CLIPS, Sistema

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RESULTATS = Path(__file__).resolve().parent.parent / "resultats"
CASOS = sorted((CLIPS.parent / "casos").glob("*.json"))
CICLOS_DIA = 288
PARAMETROS = json.loads(CONFIG.read_text(encoding="utf-8"))["experiments"]


def _decisiones(pasos):
    return [sorted((s, o["accion"], o["angulo-ordenado"]) for s, o in r["ordenes"].items()) for r in pasos]


def _escribir(nombre, lineas):
    RESULTATS.mkdir(exist_ok=True)
    texto = "\n".join(lineas)
    (RESULTATS / nombre).write_text(texto + "\n", encoding="utf-8")
    print(texto)


def _por_dia(pasos, dias):
    """Empates, usos de chunk, chunks vivos al final y chunks olvidados de cada día."""
    res = []
    for d in range(dias):
        dia = pasos[d * CICLOS_DIA:(d + 1) * CICLOS_DIA]
        episodios = [e for r in dia for e in r["episodios"].values()]
        res.append({"empates": sum(e["tipo-impasse"] == "tie" for e in episodios),
                    "usos": sum(e["chunk-aplicado"] != "nil" for e in episodios),
                    "vivos": len(dia[-1]["chunks"]),
                    "olvidados": sum(r["traza"].count(": oblidat ") for r in dia)})
    return res


def aprendizaje():
    """Las mismas semillas con y sin aprendizaje: empates por día, decisiones idénticas y Wilcoxon."""
    semillas, dias = range(PARAMETROS["aprenentatge"]["llavors"]), PARAMETROS["aprenentatge"]["dies"]
    datos, identicas = {True: [], False: []}, 0
    for semilla in semillas:
        pasos = {a: simular(Sistema(aprendizaje=a), semilla, dias) for a in (True, False)}
        identicas += _decisiones(pasos[True]) == _decisiones(pasos[False])
        for a in (True, False):
            datos[a].append(_por_dia(pasos[a], dias))
    def media(a, clave, d):
        valores = [s[d][clave] for s in datos[a]]
        return f"{statistics.mean(valores):6.1f} ± {statistics.stdev(valores):4.1f}"
    lineas = [f"Experiment d'aprenentatge: {len(semillas)} llavors x {dias} dies (mitjana ± desviació per dia)",
              "dia | empats sense | empats amb   | usos chunk   | chunks vius  | oblidats"]
    for d in range(dias):
        lineas.append(f"{d + 1:3d} | {media(False, 'empates', d)} | {media(True, 'empates', d)} | "
                      f"{media(True, 'usos', d)} | {media(True, 'vivos', d)} | {media(True, 'olvidados', d)}")
    totales = {a: [sum(dia["empates"] for dia in s) for s in datos[a]] for a in (True, False)}
    prueba = wilcoxon(totales[True], totales[False])
    lineas += [f"Empats totals per llavor sense aprenentatge: {totales[False]}",
               f"Empats totals per llavor amb aprenentatge:   {totales[True]}",
               f"Decisions idèntiques amb i sense aprenentatge: {identicas}/{len(semillas)}",
               f"Wilcoxon aparellat (empats per llavor): W={prueba.statistic}, p={prueba.pvalue:.4f}"]
    _escribir("aprendizaje.txt", lineas)
    x = range(1, dias + 1)
    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(6, 6))
    for a, etiqueta in ((False, "sense aprenentatge"), (True, "amb aprenentatge")):
        ax1.plot(x, [statistics.mean(s[d]["empates"] for s in datos[a]) for d in range(dias)], "o-", label=etiqueta)
    ax1.set_ylabel("empats (tie) per dia")
    ax1.legend()
    ax2.plot(x, [statistics.mean(s[d]["vivos"] for s in datos[True]) for d in range(dias)], "s-", color="tab:green")
    ax2.set_ylabel("chunks vius al final del dia")
    ax2.set_xlabel("dia")
    fig.tight_layout()
    fig.savefig(RESULTATS / "aprendizaje.png", dpi=120)


def _reglas_con_salience(variante=None):
    env = Sistema(variante=variante).env
    return sum("salience" in str(env.find_rule(str(n))) for n in env.eval("(get-defrule-list *)"))


def agenda():
    """Las 7 estrategias frente a depth (casos y días simulados) y B0 frente al núcleo."""
    semillas = range(PARAMETROS["agenda"]["llavors"])
    lineas = ["Experiment de l'agenda: cada estrategia comparada amb depth",
              "estrategia | ordres iguals (casos) | cicles amb una altra seqüència (casos) | "
              "ordres iguals (dies) | cicles amb una altra seqüència (dies)"]
    base_casos = [ejecutar_caso(c)[1] for c in CASOS]
    base_dias = [simular(Sistema(), s) for s in semillas]
    for e in ESTRATEGIAS:
        casos = [ejecutar_caso(c, e)[1] for c in CASOS]
        dias = [simular(Sistema(e), s) for s in semillas]
        fila = []
        for base, otro in ((base_casos, casos), (base_dias, dias)):
            iguales = sum(_decisiones(b) == _decisiones(o) for b, o in zip(base, otro))
            ciclos = sum(len(b) for b in base)
            distintos = sum(x["reglas"] != y["reglas"] for b, o in zip(base, otro) for x, y in zip(b, o))
            fila += [f"{iguales}/{len(base)}", f"{distintos}/{ciclos}"]
        lineas.append(f"{e:10s} | {fila[0]:21s} | {fila[1]:38s} | {fila[2]:20s} | {fila[3]}")
    lineas.append(f"Regles amb salience: nucli {_reglas_con_salience()}, B0 {_reglas_con_salience('b0')}")
    lineas += ["", f"B0 (decisió per salience) enfront del nucli: {len(semillas)} llavors x 1 dia"]
    distintas, total, criterio = 0, 0, {}
    movimientos = {}
    for variante in (None, "b0"):
        pasos = [simular(Sistema(variante=variante), s) for s in semillas]
        episodios = [e for p in pasos for r in p for e in r["episodios"].values()]
        movimientos[variante] = sum(e["accion"] in ("orientar-produccio", "orientar-ombra", "posicio-seguretat")
                                    for e in episodios) / (len(semillas) * len(SECTORES))
        criterio[variante] = 100 * sum(e["criterio-determinante"] != "nil" for e in episodios) / len(episodios)
        if variante is None:
            nucleo = pasos
        else:
            for a, b in zip(nucleo, pasos):
                for x, y in zip(a, b):
                    for s in SECTORES:
                        distintas += x["ordenes"][s]["accion"] != y["ordenes"][s]["accion"]
                        total += 1
    lineas += [f"Decisions diferents de B0: {100 * distintas / total:.1f} % ({distintas}/{total})",
               f"Moviments per sector i dia: nucli {movimientos[None]:.1f}, B0 {movimientos['b0']:.1f}",
               f"Episodis amb criteri determinant: nucli {criterio[None]:.1f} %, B0 {criterio['b0']:.1f} %"]
    _escribir("agenda.txt", lineas)
