"""Experimentos (roadmap §11).

a1 y a2: experimentos de agenda (§11.3) sobre la batería de casos. Cada caso se ejecuta con
cada estrategia sobre las mismas entradas y se compara, ciclo a ciclo, con la primera:
  - el multiconjunto de nombres de reglas disparadas (debe ser igual) y su secuencia
    (puede diferir), indicando en qué módulos difiere;
  - las órdenes y los episodios por contenido, sin ids generados y con los multislots
    como conjuntos (§2.3.11);
  - la traza como multiconjunto de bloques (uno por sector y resultado observado) y el
    número de reglas disparadas.
a1 compara las siete estrategias de CLIPS con depth (random, con la semilla de simulacio.json);
a2, la especificidad: complexity frente a simplicity.

piloto: el núcleo en bucle cerrado con las semillas de simulacio.json (§11.2): métricas por
semilla, mediana, IQR y σ; violaciones de decisión con la cota de Clopper–Pearson (deben ser 0);
exposición real (informativa), y n por métrica para los δ fijados de antemano, con la cota
σ_d ≤ √2·σ, válida si ρ ≥ 0 (provisional hasta I4, que mide σ_d con C0–C1).

a1-bucle: A1 en bucle cerrado (§11.3): cada semilla con depth y con cada otra estrategia; por
estrategia, semillas con alguna discrepancia y su cota de Clopper–Pearson. Usa la configuración
por defecto, con el aprendizaje activo desde I4 (§11.3: la hipótesis vale con él y sin él).

aprenentatge: piloto del aprendizaje (§11.4) con las mismas semillas para C0 (sin aprendizaje),
C1 (sin olvido, umbral -100), C2 (umbral -2, por defecto) y el barrido del umbral (-1, -3): H1
(tie por cada 100 decisiones, δ = 0,5 · mediana de C0), H2 (fidelidad de las órdenes), H3
(chunks vivos y reaprendizaje), y la σ_d real de las diferencias por semilla con su n (§11.2).
Con --reutilizar C0 C1, esas configuraciones no se vuelven a ejecutar: se leen las métricas y las
órdenes guardadas en la carpeta de salida (solo es válido si el cambio no les afecta).

    uv run python python/experiments.py a1 [--estrategias depth breadth ...]
    uv run python python/experiments.py a2
    uv run python python/experiments.py piloto [--semillas 0 1 ...] [--dias 7]
    uv run python python/experiments.py a1-bucle [--semillas ...] [--dias 7]
    uv run python python/experiments.py aprenentatge [--semillas ...] [--dias 7] [--reutilizar C0 C1]
"""

import argparse
import json
import subprocess
import sys
import tempfile
from collections import Counter

import math
from pathlib import Path

import numpy as np
from scipy import stats

import bucle
import executar_casos as ec
import metricas
import ontologia as on
import pont_clips as pc
import simulador as sm
from pont_clips import RAIZ, Paso

RESULTATS = RAIZ / "resultats"


def _contenido(hechos: list[dict]) -> list[dict]:
    """Hechos sin el slot id y con los multislots ordenados, en orden canónico."""
    normal = [{k: sorted(v) if isinstance(v, list) else v for k, v in h.items() if k != "id"}
              for h in hechos]
    return sorted(normal, key=lambda h: json.dumps(h, sort_keys=True))


def _por_modulo(paso: Paso) -> dict[str, list[str]]:
    secuencias = {}
    for r in paso.reglas:
        secuencias.setdefault(paso.modulo_de[r], []).append(r)
    return secuencias


def comparar_paso(ref: Paso, otro: Paso) -> dict:
    mod_ref, mod_otro = _por_modulo(ref), _por_modulo(otro)
    return {
        "instante": ref.instante,
        "disparos": [ref.disparos, otro.disparos],
        "multiconjunto_igual": Counter(ref.reglas) == Counter(otro.reglas),
        "secuencia_igual": ref.reglas == otro.reglas,
        "modulos_con_secuencia_distinta": sorted(m for m in mod_ref.keys() | mod_otro.keys()
                                                 if mod_ref.get(m) != mod_otro.get(m)),
        "ordenes_iguales": _contenido(ref.ordenes) == _contenido(otro.ordenes),
        "episodios_iguales": _contenido(ref.episodios) == _contenido(otro.episodios),
        "traza_igual": Counter(ec.bloques(ref.traza)) == Counter(ec.bloques(otro.traza)),
        "secuencias": [ref.reglas, otro.reglas],
    }


ESTRATEGIAS_A1 = ["depth", "breadth", "lex", "mea", "complexity", "simplicity", "random"]
ESTRATEGIAS_A2 = ["complexity", "simplicity"]


def comparar(estrategias: list[str], experimento: str) -> dict:
    """Cada caso con cada estrategia, comparado ciclo a ciclo con la primera."""
    referencia, otras = estrategias[0], estrategias[1:]
    filas = []
    for caso in ec.cargar_casos():
        base = ec.ejecutar_caso(caso, referencia)
        for estrategia in otras:
            otra = ec.ejecutar_caso(caso, estrategia)
            for ref, otro in zip(base, otra):
                filas.append({"caso": caso["id"], "estrategias": [referencia, estrategia],
                              **comparar_paso(ref, otro)})
    return {
        "experimento": f"{experimento} (roadmap §11.3)",
        "configuracion": {
            "estrategias": estrategias,
            "semilla-agenda (random)": pc.simulacio()["semilla-agenda"],
            "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=RAIZ, capture_output=True,
                                     text=True).stdout.strip(),
            "base_coneixement": "config/base_coneixement.clp (sin sobrescrituras)",
            "casos": sorted({f["caso"] for f in filas}),
        },
        "ciclos": filas,
    }


def a1(estrategias: list[str] = ESTRATEGIAS_A1) -> dict:
    """A1: las estrategias de agenda de CLIPS frente a la primera."""
    return comparar(estrategias, "A1")


def a2(estrategias: list[str] = ESTRATEGIAS_A2) -> dict:
    """A2: especificidad, complexity frente a simplicity."""
    return comparar(estrategias, "A2")


def invariante(res: dict) -> bool:
    """Hipótesis de §11.3: cambia el orden de disparo pero no lo que se decide ni se explica."""
    return all(c["multiconjunto_igual"] and c["ordenes_iguales"] and c["episodios_iguales"]
               and c["traza_igual"] for c in res["ciclos"])


def resumen(res: dict) -> str:
    conf = res["configuracion"]
    referencia = conf["estrategias"][0]
    lineas = [f"{res['experimento']}: {len(conf['casos'])} casos, referencia {referencia}.",
              f"  {'estrategia':11s} {'ciclos':>6s} {'multiconj.':>10s} {'secuencia':>9s} {'órdenes':>8s} "
              f"{'episodios':>9s} {'traza':>6s} {'disparos':>9s} {'ref.':>6s}"]
    for estrategia in conf["estrategias"][1:]:
        ciclos = [c for c in res["ciclos"] if c["estrategias"][1] == estrategia]
        def n(clave):
            return sum(c[clave] for c in ciclos)
        lineas.append(f"  {estrategia:11s} {len(ciclos):6d} {n('multiconjunto_igual'):10d} "
                      f"{n('secuencia_igual'):9d} {n('ordenes_iguales'):8d} {n('episodios_iguales'):9d} "
                      f"{n('traza_igual'):6d} {sum(c['disparos'][1] for c in ciclos):9d} "
                      f"{sum(c['disparos'][0] for c in ciclos):6d}")
    modulos = Counter(m for c in res["ciclos"] for m in c["modulos_con_secuencia_distinta"])
    lineas.append("  módulos donde cambia la secuencia (ciclos, todas las estrategias): "
                  + (", ".join(f"{m} ({k})" for m, k in modulos.most_common()) or "ninguno"))
    lineas.append(f"  invariante (multiconjunto, órdenes, episodios y traza iguales): "
                  f"{'sí' if invariante(res) else 'NO'}")
    return "\n".join(lineas)


# --- bucle cerrado: piloto y potencia (§11.2) ---------------------------------

# Métricas del piloto, la principal (H1, §11.4) primero.
METRICAS_PILOTO = ["tie-100", "energia-kwh", "horas-estres-sector-dia", "movimientos-sector-dia",
                   "reglas-ciclo", "cpu-ms-ciclo"]


def clopper_pearson(k: int, n: int) -> tuple[float, float]:
    """Intervalo de confianza del 95 % de una proporción k/n (exacto)."""
    bajo = 0.0 if k == 0 else stats.beta.ppf(0.025, k, n - k + 1)
    alto = 1.0 if k == n else stats.beta.ppf(0.975, k + 1, n - k)
    return float(bajo), float(alto)


def tamano_muestra(sigma_d: float, delta: float, alfa: float = 0.05, potencia: float = 0.8,
                   minimo: int = 30) -> int:
    """n = ((z₁₋α/₂ + z₁₋β)·σ_d/δ)², con un mínimo de 30 semillas (§11.2)."""
    z = stats.norm.ppf(1 - alfa / 2) + stats.norm.ppf(potencia)
    return max(minimo, math.ceil((z * sigma_d / delta) ** 2)) if delta > 0 else minimo


def _config(dias: float | None) -> dict:
    config = sm.cargar_config()
    if dias is not None:
        config["dias"] = dias
    return config


def piloto(semillas: list[int] | None = None, dias: float | None = None,
           salida: Path | None = None) -> dict:
    config = _config(dias)
    semillas = config["semillas"] if semillas is None else semillas
    por_semilla = {}
    for semilla in semillas:
        ej = bucle.ejecutar(semilla, config)
        m = metricas.calcular(ej)
        if ej.errores:
            m["errores"] = ej.errores
        por_semilla[semilla] = m
        if salida is not None:
            bucle.guardar(ej, salida / f"semilla_{semilla}", m)
    n = len(semillas)
    resumen_m = {}
    for nombre in METRICAS_PILOTO:
        x = np.array([por_semilla[s][nombre] for s in semillas], dtype=float)
        sigma = float(x.std(ddof=1)) if n > 1 else 0.0
        mediana = float(np.median(x))
        d = config["delta"][nombre]
        delta = d["abs"] if "abs" in d else d["rel"] * mediana
        sigma_d = math.sqrt(2) * sigma                     # cota válida si ρ ≥ 0
        resumen_m[nombre] = {"mediana": mediana, "q1": float(np.percentile(x, 25)),
                             "q3": float(np.percentile(x, 75)), "sigma": sigma, "delta": delta,
                             "sigma_d_cota": sigma_d, "n": tamano_muestra(sigma_d, delta)}
    con_violacion = sum(1 for s in semillas if por_semilla[s]["violaciones-decision"]["total"] > 0)
    expuestas = sum(1 for s in semillas if por_semilla[s]["exposicion-real"]["total"] > 0)
    return {
        "experimento": "Piloto del núcleo (roadmap §11.2)",
        "configuracion": {"semillas": semillas, "dias": config["dias"], "dt-min": config["dt-min"],
                          "estrategia": config["estrategia"], "delta": config["delta"],
                          "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=RAIZ,
                                                   capture_output=True, text=True).stdout.strip()},
        "por_semilla": por_semilla,
        "metricas": resumen_m,
        "violaciones": {"semillas_con_violacion": con_violacion, "n": n,
                        "ic95": clopper_pearson(con_violacion, n),
                        "total": sum(por_semilla[s]["violaciones-decision"]["total"] for s in semillas)},
        "exposicion": {"semillas_expuestas": expuestas,
                       "total": sum(por_semilla[s]["exposicion-real"]["total"] for s in semillas),
                       "por_causa": {c: sum(por_semilla[s]["exposicion-real"][c] for s in semillas)
                                     for c in ("personas", "actuador", "viento", "desgaste")}},
        "errores": {s: m["errores"] for s, m in por_semilla.items() if "errores" in m},
    }


def resumen_piloto(res: dict) -> str:
    conf, v = res["configuracion"], res["violaciones"]
    lineas = [f"{res['experimento']}: {len(conf['semillas'])} semillas × {conf['dias']} días, "
              f"estrategia {conf['estrategia']}.",
              f"  violaciones de decisión: {v['total']} en total; semillas con alguna "
              f"{v['semillas_con_violacion']}/{v['n']}, IC 95 % [{v['ic95'][0]:.3f}, {v['ic95'][1]:.3f}]",
              f"  exposición real (informativa): {res['exposicion']['total']} órdenes "
              f"({res['exposicion']['por_causa']}), en {res['exposicion']['semillas_expuestas']} semillas",
              f"  {'métrica':26s} {'mediana':>9s} {'IQR':>19s} {'σ':>8s} {'δ':>8s} {'n':>5s}"]
    for nombre, m in res["metricas"].items():
        etiqueta = nombre + (" (principal)" if nombre == "tie-100" else "")
        lineas.append(f"  {etiqueta:26s} {m['mediana']:9.3f} [{m['q1']:8.3f}, {m['q3']:8.3f}] "
                      f"{m['sigma']:8.3f} {m['delta']:8.3f} {m['n']:5d}")
    lineas.append("  n con σ_d ≤ √2·σ (válida si ρ ≥ 0), α = 0,05, potencia 0,8, mínimo 30: "
                  "provisional hasta I4 (σ_d real de C0–C1).")
    if res["errores"]:
        lineas.append(f"  ERRORES de CLIPS en las semillas {sorted(res['errores'])}")
    return "\n".join(lineas)


def a1_bucle(estrategias: list[str] = ESTRATEGIAS_A1, semillas: list[int] | None = None,
             dias: float | None = None) -> dict:
    """A1 en bucle cerrado: por semilla y estrategia, ¿cambia algo además del orden de disparo?"""
    config = _config(dias)
    semillas = config["semillas"] if semillas is None else semillas
    referencia, otras = estrategias[0], estrategias[1:]
    filas = []
    for semilla in semillas:
        base = bucle.ejecutar(semilla, config, referencia)
        for estrategia in otras:
            otra = bucle.ejecutar(semilla, config, estrategia)
            multiconjunto = all(Counter(a["reglas"]) == Counter(b["reglas"])
                                for a, b in zip(base.ciclos, otra.ciclos))
            secuencia = sum(a["reglas"] == b["reglas"] for a, b in zip(base.ciclos, otra.ciclos))
            fila = {"semilla": semilla, "estrategia": estrategia, "ciclos": len(base.ciclos),
                    "multiconjunto_igual": multiconjunto, "ciclos_secuencia_igual": secuencia,
                    "ordenes_iguales": _contenido(base.ordenes) == _contenido(otra.ordenes),
                    "episodios_iguales": _contenido(base.episodios) == _contenido(otra.episodios),
                    "traza_igual": Counter(ec.bloques(base.traza)) == Counter(ec.bloques(otra.traza)),
                    "disparos": [sum(c["disparos"] for c in base.ciclos),
                                 sum(c["disparos"] for c in otra.ciclos)]}
            fila["discrepancia"] = not (fila["multiconjunto_igual"] and fila["ordenes_iguales"]
                                        and fila["episodios_iguales"] and fila["traza_igual"])
            filas.append(fila)
    por_estrategia = {}
    for estrategia in otras:
        f = [x for x in filas if x["estrategia"] == estrategia]
        k = sum(x["discrepancia"] for x in f)
        por_estrategia[estrategia] = {"semillas": len(f), "discrepancias": k,
                                      "ic95": clopper_pearson(k, len(f)),
                                      "ciclos": sum(x["ciclos"] for x in f),
                                      "ciclos_secuencia_igual": sum(x["ciclos_secuencia_igual"] for x in f)}
    return {"experimento": "A1 en bucle cerrado (roadmap §11.3)",
            "configuracion": {"estrategias": estrategias, "semillas": semillas, "dias": config["dias"],
                              "semilla-agenda (random)": config["semilla-agenda"]},
            "filas": filas, "por_estrategia": por_estrategia}


def resumen_a1_bucle(res: dict) -> str:
    conf = res["configuracion"]
    lineas = [f"{res['experimento']}: {len(conf['semillas'])} semillas × {conf['dias']} días, "
              f"referencia {conf['estrategias'][0]}.",
              f"  {'estrategia':11s} {'discrepancias':>13s} {'IC 95 %':>17s} {'ciclos con secuencia igual':>27s}"]
    for estrategia, r in res["por_estrategia"].items():
        lineas.append(f"  {estrategia:11s} {r['discrepancias']:>6d}/{r['semillas']:<6d} "
                      f"[{r['ic95'][0]:.3f}, {r['ic95'][1]:.3f}] {r['ciclos_secuencia_igual']:>14d}/{r['ciclos']}")
    return "\n".join(lineas)


# Configuraciones del experimento de aprendizaje (§11.4): sobrescrituras de --set (§2.2).
CONFIGURACIONES = {"C0": ["aprendizaje-activo=FALSE"], "C1": ["umbral-olvido=-100"], "C2": [],
                   "C2-umbral-1": ["umbral-olvido=-1"], "C2-umbral-3": ["umbral-olvido=-3"]}
METRICAS_CHUNKS = ["chunks-vivos-max", "chunks-vivos-final", "chunks-compilados", "chunks-olvidados",
                   "usos-chunk", "usos-chunk-confirmados", "transferencia"]


def _delta(config: dict, nombre: str, mediana_c0: float) -> float:
    d = config["delta"][nombre]
    return d["abs"] if "abs" in d else d["rel"] * mediana_c0


def _comparacion(x0: np.ndarray, x1: np.ndarray, delta: float) -> dict:
    """Diferencias por semilla d = C0 − Cx: mediana, IC 95 % por bootstrap, σ_d, n y Wilcoxon
    unilateral de d > δ (reducción de al menos δ, §11.2)."""
    d = x0 - x1
    rng = np.random.default_rng(0)
    medianas = np.median(rng.choice(d, size=(10000, len(d)), replace=True), axis=1)
    sigma_d = float(d.std(ddof=1)) if len(d) > 1 else 0.0
    try:
        p = float(stats.wilcoxon(d - delta, alternative="greater").pvalue)
    except ValueError:                                  # todas las diferencias iguales a δ
        p = 1.0
    return {"mediana_diferencia": float(np.median(d)),
            "ic95": [float(np.percentile(medianas, 2.5)), float(np.percentile(medianas, 97.5))],
            "sigma_d": sigma_d, "delta": delta, "n": tamano_muestra(sigma_d, delta), "p_wilcoxon": p}


def _cargar(directorio: Path, semilla: int, config: dict) -> tuple[dict, "bucle.Ejecucion"]:
    """Métricas y órdenes de una ejecución guardada por bucle.guardar."""
    d = directorio / f"semilla_{semilla}"
    ej = bucle.Ejecucion(semilla, config["estrategia"], config)
    ej.ordenes = [json.loads(l) for l in (d / "ordenes.jsonl").read_text(encoding="utf-8").splitlines()]
    return json.loads((d / "metricas.json").read_text(encoding="utf-8")), ej


def aprenentatge(semillas: list[int] | None = None, dias: float | None = None,
                 salida: Path | None = None, configuraciones: dict | None = None,
                 reutilizar: list[str] = ()) -> dict:
    config = _config(dias)
    semillas = config["semillas"] if semillas is None else semillas
    configuraciones = CONFIGURACIONES if configuraciones is None else configuraciones
    bases = salida / "bases" if salida is not None else Path(tempfile.mkdtemp())
    metr, ejecuciones = {}, {}
    for nombre, sobrescrituras in configuraciones.items():
        base = on.generar_variante(sobrescrituras, bases / f"{nombre}.clp")
        metr[nombre] = {}
        for semilla in semillas:
            if nombre in reutilizar:
                metr[nombre][semilla], ejecuciones[(nombre, semilla)] = _cargar(salida / nombre, semilla, config)
                continue
            ej = bucle.ejecutar(semilla, config, base=base)
            m = metricas.calcular(ej)
            if ej.errores:
                m["errores"] = ej.errores
            metr[nombre][semilla] = m
            ejecuciones[(nombre, semilla)] = ej
            if salida is not None:
                bucle.guardar(ej, salida / nombre / f"semilla_{semilla}", m)
    def serie(nombre, metrica):
        return np.array([metr[nombre][s][metrica] for s in semillas], dtype=float)
    resumen_m = {nombre: {metrica: {"mediana": float(np.median(serie(nombre, metrica))),
                                    "q1": float(np.percentile(serie(nombre, metrica), 25)),
                                    "q3": float(np.percentile(serie(nombre, metrica), 75))}
                          for metrica in METRICAS_PILOTO + METRICAS_CHUNKS}
                 for nombre in configuraciones}
    mediana_c0 = {m: resumen_m["C0"][m]["mediana"] for m in METRICAS_PILOTO}
    potencia = {m: _comparacion(serie("C0", m), serie("C1", m), _delta(config, m, mediana_c0[m]))
                for m in METRICAS_PILOTO}
    h1 = {c: _comparacion(serie("C0", "tie-100"), serie(c, "tie-100"), _delta(config, "tie-100", mediana_c0["tie-100"]))
          for c in ("C1", "C2")}
    h2 = {}
    for c in configuraciones:
        if c == "C0":
            continue
        k = sum(metricas.fidelidad(ejecuciones[("C0", s)], ejecuciones[(c, s)]) for s in semillas)
        h2[c] = {"semillas_identicas": k, "n": len(semillas), "ic95": clopper_pearson(k, len(semillas))}
    delta_tie = _delta(config, "tie-100", mediana_c0["tie-100"])
    h3 = {"chunks-vivos-max": {c: resumen_m[c]["chunks-vivos-max"]["mediana"] for c in ("C1", "C2")},
          "chunks-vivos-final": {c: resumen_m[c]["chunks-vivos-final"]["mediana"] for c in ("C1", "C2")},
          "aumento-tie-100": _comparacion(serie("C2", "tie-100"), serie("C1", "tie-100"), delta_tie),
          "delta": delta_tie}
    barrido = {c: {m: resumen_m[c][m]["mediana"] for m in ("tie-100", "chunks-vivos-max", "chunks-vivos-final",
                                                           "chunks-compilados", "chunks-olvidados")}
               for c in configuraciones if c.startswith("C2")}
    return {
        "experimento": "Piloto del aprendizaje (roadmap §11.4), iteración I4",
        "configuracion": {"semillas": semillas, "dias": config["dias"], "estrategia": config["estrategia"],
                          "configuraciones": configuraciones, "reutilizadas": list(reutilizar),
                          "delta": config["delta"],
                          "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=RAIZ,
                                                   capture_output=True, text=True).stdout.strip()},
        "por_semilla": metr, "metricas": resumen_m, "h1": h1, "h2": h2, "h3": h3,
        "potencia_c0_c1": potencia, "barrido": barrido,
        "violaciones": {c: sum(metr[c][s]["violaciones-decision"]["total"] for s in semillas)
                        for c in configuraciones},
        "errores": {f"{c}/{s}": metr[c][s]["errores"] for c in configuraciones for s in semillas
                    if "errores" in metr[c][s]},
    }


def resumen_aprenentatge(res: dict) -> str:
    conf = res["configuracion"]
    l = [f"{res['experimento']}: {len(conf['semillas'])} semillas × {conf['dias']} días, "
         f"estrategia {conf['estrategia']}, configuraciones {', '.join(conf['configuraciones'])}.",
         f"  violaciones de decisión: {res['violaciones']}",
         "  H1, tie por cada 100 decisiones (principal):"]
    for c in res["metricas"]:
        m = res["metricas"][c]["tie-100"]
        l.append(f"    {c:12s} mediana {m['mediana']:7.3f}  IQR [{m['q1']:.3f}, {m['q3']:.3f}]")
    for c, h in res["h1"].items():
        l.append(f"    C0 − {c}: mediana de la diferencia {h['mediana_diferencia']:.3f}, IC 95 % "
                 f"[{h['ic95'][0]:.3f}, {h['ic95'][1]:.3f}], δ = {h['delta']:.3f}, "
                 f"Wilcoxon unilateral (d > δ) p = {h['p_wilcoxon']:.4f}")
    l.append("  H2, fidelidad de las órdenes frente a C0:")
    for c, h in res["h2"].items():
        l.append(f"    {c:12s} {h['semillas_identicas']}/{h['n']} semillas idénticas, "
                 f"IC 95 % [{h['ic95'][0]:.3f}, {h['ic95'][1]:.3f}]")
    h3 = res["h3"]
    l.append(f"  H3, olvido: chunks vivos máx. {h3['chunks-vivos-max']}, final {h3['chunks-vivos-final']}; "
             f"aumento de tie-100 de C2 frente a C1 (C2 − C1): mediana {h3['aumento-tie-100']['mediana_diferencia']:.3f}, "
             f"IC 95 % [{h3['aumento-tie-100']['ic95'][0]:.3f}, {h3['aumento-tie-100']['ic95'][1]:.3f}] (δ = {h3['delta']:.3f})")
    l.append("  Barrido del umbral de olvido (medianas):")
    for c, b in res["barrido"].items():
        l.append(f"    {c:12s} " + ", ".join(f"{k} {v:.3f}" for k, v in b.items()))
    l.append(f"  Transferencia (mediana, C2): {res['metricas']['C2']['transferencia']['mediana']:.3f}")
    l.append(f"  σ_d real de C0 − C1 y n (α = 0,05, potencia 0,8, mínimo 30):")
    l.append(f"    {'métrica':26s} {'σ_d':>8s} {'δ':>8s} {'n':>5s}")
    for m, p in res["potencia_c0_c1"].items():
        l.append(f"    {m:26s} {p['sigma_d']:8.3f} {p['delta']:8.3f} {p['n']:5d}")
    if res["errores"]:
        l.append(f"  ERRORES de CLIPS en {sorted(res['errores'])}")
    return "\n".join(l)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="experimento", required=True)
    for nombre, ayuda, defecto in (("a1", "estrategias de agenda (§11.3)", ESTRATEGIAS_A1),
                                   ("a2", "especificidad: complexity frente a simplicity (§11.3)",
                                    ESTRATEGIAS_A2)):
        p = sub.add_parser(nombre, help=ayuda)
        p.add_argument("--estrategias", nargs="+", default=defecto)
        p.add_argument("--salida", default=str(RESULTATS / f"i2_{nombre}"))
    p = sub.add_parser("piloto", help="piloto del núcleo en bucle cerrado y potencia (§11.2)")
    p.add_argument("--semillas", nargs="+", type=int, default=None)
    p.add_argument("--dias", type=float, default=None)
    p.add_argument("--salida", default=str(RESULTATS / "i3_piloto"))
    p = sub.add_parser("a1-bucle", help="A1 en bucle cerrado (§11.3)")
    p.add_argument("--estrategias", nargs="+", default=ESTRATEGIAS_A1)
    p.add_argument("--semillas", nargs="+", type=int, default=None)
    p.add_argument("--dias", type=float, default=None)
    p.add_argument("--salida", default=str(RESULTATS / "i3_a1"))
    p = sub.add_parser("aprenentatge", help="piloto del aprendizaje: C0, C1, C2 y barrido (§11.4)")
    p.add_argument("--semillas", nargs="+", type=int, default=None)
    p.add_argument("--dias", type=float, default=None)
    p.add_argument("--salida", default=str(RESULTATS / "i4_aprenentatge"))
    p.add_argument("--reutilizar", nargs="+", default=[], choices=list(CONFIGURACIONES),
                   help="configuraciones que se leen de la salida en lugar de ejecutarse")
    args = parser.parse_args(argv)

    if args.experimento in ("piloto", "a1-bucle", "aprenentatge"):
        salida = RAIZ / args.salida
        salida.mkdir(parents=True, exist_ok=True)
        if args.experimento == "piloto":
            res = piloto(args.semillas, args.dias, salida)
            texto = resumen_piloto(res)
            correcto = res["violaciones"]["total"] == 0 and not res["errores"]
        elif args.experimento == "aprenentatge":
            res = aprenentatge(args.semillas, args.dias, salida, reutilizar=args.reutilizar)
            texto = resumen_aprenentatge(res)
            correcto = not any(res["violaciones"].values()) and not res["errores"]
        else:
            res = a1_bucle(args.estrategias, args.semillas, args.dias)
            texto = resumen_a1_bucle(res)
            correcto = all(r["discrepancias"] == 0 for r in res["por_estrategia"].values())
        (salida / "resultados.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n",
                                                encoding="utf-8")
        (salida / "resumen.txt").write_text(texto + "\n", encoding="utf-8")
        print(texto)
        print(f"\nResultados en {salida}")
        return 0 if correcto else 1

    res = {"a1": a1, "a2": a2}[args.experimento](args.estrategias)
    salida = RAIZ / args.salida                     # una ruta absoluta sustituye a RAIZ
    salida.mkdir(parents=True, exist_ok=True)
    (salida / "resultados.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n",
                                            encoding="utf-8")
    texto = resumen(res)
    (salida / "resumen.txt").write_text(texto + "\n", encoding="utf-8")
    print(texto)
    print(f"\nResultados en {salida}")
    return 0 if invariante(res) else 1


if __name__ == "__main__":
    sys.exit(main())
