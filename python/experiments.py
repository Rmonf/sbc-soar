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
import hashlib
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


def comparar(estrategias: list[str], experimento: str, base: Path = pc.BASE,
             variante: str | None = None) -> dict:
    """Cada caso con cada estrategia, comparado ciclo a ciclo con la primera. Con variante (A3s,
    §11.3), la referencia sin variante se compara con la misma estrategia con la variante."""
    referencia, otras = estrategias[0], estrategias[1:]
    if variante:
        otras = [referencia]
    filas = []
    for caso in ec.cargar_casos():
        ref_pasos = ec.ejecutar_caso(caso, referencia, base)
        for estrategia in otras:
            otra = ec.ejecutar_caso(caso, estrategia, base, variante)
            for ref, otro in zip(ref_pasos, otra):
                filas.append({"caso": caso["id"], "estrategias": [referencia, estrategia],
                              "variante": variante, **comparar_paso(ref, otro)})
    return {
        "experimento": f"{experimento} (roadmap §11.3)",
        "configuracion": {
            "estrategias": estrategias,
            "semilla-agenda (random)": pc.simulacio()["semilla-agenda"],
            "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=RAIZ, capture_output=True,
                                     text=True).stdout.strip(),
            "base_coneixement": str(Path(base).relative_to(RAIZ) if Path(base).is_relative_to(RAIZ) else base),
            "variante": variante,
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


def a3s(base: Path = pc.BASE) -> dict:
    """A3s sobre la batería: depth frente a depth con la salience de clips/variants/a3s.clp."""
    return comparar(["depth"], "A3s", base, "a3s")


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
    for estrategia in dict.fromkeys(c["estrategias"][1] for c in res["ciclos"]):
        ciclos = [c for c in res["ciclos"] if c["estrategias"][1] == estrategia]
        def n(clave):
            return sum(c[clave] for c in ciclos)
        etiqueta = f"{estrategia}+{conf['variante']}" if conf.get("variante") else estrategia
        lineas.append(f"  {etiqueta:11s} {len(ciclos):6d} {n('multiconjunto_igual'):10d} "
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


def comparar_ejecuciones(a: "bucle.Ejecucion", b: "bucle.Ejecucion") -> dict:
    """¿Cambia algo además del orden de disparo entre dos ejecuciones de la misma semilla? (§11.3)
    Las reglas de cada ciclo se comparan por sus huellas (multiconjunto y secuencia), que también
    tienen las ejecuciones guardadas; órdenes y episodios por contenido, y la traza por bloques."""
    fila = {"ciclos": len(a.ciclos),
            "multiconjunto_igual": len(a.ciclos) == len(b.ciclos) and all(
                x["multiconjunto"] == y["multiconjunto"] for x, y in zip(a.ciclos, b.ciclos)),
            "ciclos_secuencia_igual": sum(x["secuencia"] == y["secuencia"] for x, y in zip(a.ciclos, b.ciclos)),
            "ordenes_iguales": _contenido(a.ordenes) == _contenido(b.ordenes),
            "episodios_iguales": _contenido(a.episodios) == _contenido(b.episodios),
            "traza_igual": Counter(ec.bloques(a.traza)) == Counter(ec.bloques(b.traza)),
            "disparos": [sum(c["disparos"] for c in a.ciclos), sum(c["disparos"] for c in b.ciclos)]}
    fila["discrepancia"] = not (fila["multiconjunto_igual"] and fila["ordenes_iguales"]
                                and fila["episodios_iguales"] and fila["traza_igual"])
    return fila


def _discrepancias(filas: list[dict]) -> dict:
    """Semillas con alguna discrepancia y su cota de Clopper–Pearson (§11.3)."""
    k = sum(x["discrepancia"] for x in filas)
    return {"semillas": len(filas), "discrepancias": k, "ic95": clopper_pearson(k, len(filas)),
            "ciclos": sum(x["ciclos"] for x in filas),
            "ciclos_secuencia_igual": sum(x["ciclos_secuencia_igual"] for x in filas)}


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
            filas.append({"semilla": semilla, "estrategia": estrategia, **comparar_ejecuciones(base, otra)})
    por_estrategia = {e: _discrepancias([x for x in filas if x["estrategia"] == e]) for e in otras}
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


def biserial(d: np.ndarray) -> float:
    """Correlación biserial de rangos de unas diferencias pareadas (§11.2): (W⁺ − W⁻)/(W⁺ + W⁻),
    sin las diferencias nulas; 0 si todas lo son."""
    d = d[d != 0]
    if len(d) == 0:
        return 0.0
    rangos = stats.rankdata(np.abs(d))
    return float((rangos[d > 0].sum() - rangos[d < 0].sum()) / rangos.sum())


def holm(p: dict) -> dict:
    """p corregidas por Holm–Bonferroni (§11.2), con las mismas claves."""
    orden = sorted(p, key=lambda k: p[k])
    corregidas, maximo = {}, 0.0
    for i, k in enumerate(orden):
        maximo = max(maximo, min(1.0, (len(orden) - i) * p[k]))
        corregidas[k] = maximo
    return {k: corregidas[k] for k in p}


def _wilcoxon(d: np.ndarray, **kw) -> float:
    """p de Wilcoxon de rangos con signo; 1 si todas las diferencias son nulas."""
    if not np.any(d != 0):
        return 1.0
    try:
        return float(stats.wilcoxon(d, **kw).pvalue)
    except ValueError:
        return 1.0


def friedman(series: dict[str, np.ndarray]) -> dict:
    """Más de dos configuraciones sobre las mismas semillas (§11.2): Friedman y, si p < 0,05,
    Wilcoxon bilateral por pares con Holm."""
    if all(np.array_equal(x, next(iter(series.values()))) for x in series.values()):
        p = 1.0                                         # todas iguales en cada semilla
    else:
        p = float(stats.friedmanchisquare(*series.values()).pvalue)
    res = {"p_friedman": p, "pares": {}}
    if p < 0.05:
        claves = list(series)
        crudas = {f"{a}-{b}": _wilcoxon(series[a] - series[b])
                  for i, a in enumerate(claves) for b in claves[i + 1:]}
        res["pares"] = {k: {"p": crudas[k], "p_holm": v} for k, v in holm(crudas).items()}
    return res


def _comparacion(x0: np.ndarray, x1: np.ndarray, delta: float) -> dict:
    """Diferencias por semilla d = C0 − Cx: mediana, IC 95 % por bootstrap, σ_d, n, biserial de
    rangos y Wilcoxon unilateral de d > δ (reducción de al menos δ, §11.2)."""
    d = x0 - x1
    rng = np.random.default_rng(0)
    medianas = np.median(rng.choice(d, size=(10000, len(d)), replace=True), axis=1)
    sigma_d = float(d.std(ddof=1)) if len(d) > 1 else 0.0
    p = _wilcoxon(d - delta, alternative="greater")
    return {"mediana_diferencia": float(np.median(d)),
            "ic95": [float(np.percentile(medianas, 2.5)), float(np.percentile(medianas, 97.5))],
            "sigma_d": sigma_d, "delta": delta, "n": tamano_muestra(sigma_d, delta), "p_wilcoxon": p,
            "p_menor_delta": _wilcoxon(d - delta, alternative="less"), "p_bilateral": _wilcoxon(d),
            "biserial": biserial(d)}


def _cargar(directorio: Path, semilla: int, config: dict) -> tuple[dict, "bucle.Ejecucion"]:
    """Métricas y órdenes de una ejecución guardada por bucle.guardar."""
    d = directorio / f"semilla_{semilla}"
    ej = bucle.Ejecucion(semilla, config["estrategia"], config)
    ej.ordenes = [json.loads(l) for l in (d / "ordenes.jsonl").read_text(encoding="utf-8").splitlines()]
    return json.loads((d / "metricas.json").read_text(encoding="utf-8")), ej


def aprenentatge(semillas: list[int] | None = None, dias: float | None = None,
                 salida: Path | None = None, configuraciones: dict | None = None,
                 reutilizar: list[str] = (), cache: "Cache | None" = None) -> dict:
    """Con cache (I5), las ejecuciones salen del caché compartido y reanudable; si no, se ejecutan
    y se guardan en salida/<configuración> (I4)."""
    config = cache.config if cache is not None else _config(dias)
    semillas = config["semillas"] if semillas is None else semillas
    configuraciones = CONFIGURACIONES if configuraciones is None else configuraciones
    bases = salida / "bases" if salida is not None else Path(tempfile.mkdtemp())
    metr, ejecuciones, entornos = {}, {}, []
    for nombre, sobrescrituras in configuraciones.items():
        base = on.generar_variante(sobrescrituras, bases / f"{nombre}.clp") if cache is None else None
        metr[nombre] = {}
        for semilla in semillas:
            if cache is not None:
                m, ej = cache.ejecucion(semilla, config["estrategia"], nombre)
                entornos.append(ej.entorno)
            elif nombre in reutilizar:
                m, ej = _cargar(salida / nombre, semilla, config)
            else:
                ej = bucle.ejecutar(semilla, config, base=base)
                m = metricas.calcular(ej)
                if ej.errores:
                    m["errores"] = ej.errores
                if salida is not None:
                    bucle.guardar(ej, salida / nombre / f"semilla_{semilla}", m)
                entornos.append(ej.entorno)
            metr[nombre][semilla] = m
            # solo hacen falta las órdenes (H2): no se guardan episodios ni trazas en memoria
            ejecuciones[(nombre, semilla)] = bucle.Ejecucion(semilla, ej.estrategia, config, ordenes=ej.ordenes)
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
    # H1 (reducción > δ en C1 y C2) y H3 (aumento < δ) forman una familia: Holm (§11.2)
    p_holm = holm({"H1 C0−C1": h1["C1"]["p_wilcoxon"], "H1 C0−C2": h1["C2"]["p_wilcoxon"],
                   "H3 C2−C1 < δ": h3["aumento-tie-100"]["p_menor_delta"]})
    # contabilidad de I4: tie(C0) = tie(Cx) + usos de chunk(Cx), semilla a semilla
    def ties(c, s):
        return round(metr[c][s]["tie-100"] * metr[c][s]["decisiones"] / 100)
    contabilidad = {c: sum(ties("C0", s) == ties(c, s) + metr[c][s]["usos-chunk"] for s in semillas)
                    for c in configuraciones if c != "C0"}
    cpu = {c: _comparacion(serie("C0", "cpu-ms-ciclo"), serie(c, "cpu-ms-ciclo"), 0.0)
           for c in configuraciones if c != "C0"}
    return {
        "experimento": "Piloto del aprendizaje (roadmap §11.4), iteración I4",
        "configuracion": {"semillas": semillas, "dias": config["dias"], "estrategia": config["estrategia"],
                          "configuraciones": configuraciones, "reutilizadas": list(reutilizar),
                          "delta": config["delta"],
                          "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=RAIZ,
                                                   capture_output=True, text=True).stdout.strip()},
        "por_semilla": metr, "metricas": resumen_m, "h1": h1, "h2": h2, "h3": h3,
        "potencia_c0_c1": potencia, "barrido": barrido, "holm": p_holm, "contabilidad": contabilidad,
        "cpu": cpu, "loadavg_max": max((max(e["loadavg-inicio"][0], e["loadavg-fin"][0]) for e in entornos
                                        if "loadavg-fin" in e), default=None),
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
             f"IC 95 % [{h3['aumento-tie-100']['ic95'][0]:.3f}, {h3['aumento-tie-100']['ic95'][1]:.3f}] (δ = {h3['delta']:.3f}, "
             f"Wilcoxon unilateral d < δ p = {h3['aumento-tie-100']['p_menor_delta']:.4g})")
    if "holm" in res:
        l.append("  Holm (H1 y H3): " + ", ".join(f"{k} p = {v:.4g}" for k, v in res["holm"].items()))
        l.append(f"  Contabilidad tie(C0) = tie(Cx) + usos(Cx): "
                 + ", ".join(f"{c} {k}/{len(conf['semillas'])}" for c, k in res["contabilidad"].items()))
        l.append(f"  CPU por ciclo (ms), C0 − Cx (loadavg máximo {res['loadavg_max']}):")
        for c, h in res["cpu"].items():
            l.append(f"    C0 − {c}: mediana {h['mediana_diferencia']:.3f}, IC 95 % [{h['ic95'][0]:.3f}, "
                     f"{h['ic95'][1]:.3f}], Wilcoxon bilateral p = {h['p_bilateral']:.4f}, biserial {h['biserial']:.2f}")
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


# --- I5: experimentos completos, reanudables (§11.2–§11.4) -------------------------

FICHEROS_EJECUCION = [RAIZ / "python" / f for f in ("simulador.py", "pont_clips.py", "bucle.py")]
BASES_I5 = ("C0", "C2")                    # aprendizaje desactivado y activado (§11.3)


def huella_codigo(base: Path, variante: str | None) -> str:
    """Huella de lo que determina una ejecución: los .clp que se cargan (base incluida) y el código
    del simulador, del puente y del bucle. Una ejecución guardada solo se reutiliza con la misma."""
    h = hashlib.sha1()
    for f in [*pc.ficheros(base, variante), *FICHEROS_EJECUCION]:
        h.update(Path(f).read_bytes())
    return h.hexdigest()[:16]


class Cache:
    """Ejecuciones de I5 en directorio/<estrategia>-<base>-<variante>/semilla_n, compartidas por todos
    los experimentos (C0 y C2 con depth sirven de referencia al aprendizaje, a B0, a A3 y a A1). Una
    ejecución ya guardada con la misma clave (semilla, estrategia, simulación, base, variante y
    huella del código) se lee en lugar de repetirse: así el experimento se puede reanudar (§11.2)."""

    def __init__(self, directorio: Path, config: dict):
        self.dir, self.config, self.bases = directorio, config, {}
        self.ejecutadas = self.reutilizadas = 0

    def base(self, nombre: str) -> Path:
        if nombre not in self.bases:
            self.bases[nombre] = on.generar_variante(CONFIGURACIONES[nombre], self.dir / "bases" / f"{nombre}.clp")
        return self.bases[nombre]

    def ejecucion(self, semilla: int, estrategia: str = "depth", base: str = "C2",
                  variante: str | None = None) -> tuple[dict, "bucle.Ejecucion"]:
        ruta = self.base(base)
        clave = {"base": base, "variante": variante, "huella": huella_codigo(ruta, variante)}
        d = self.dir / f"{estrategia}-{base}-{variante or 'nucleo'}" / f"semilla_{semilla}"
        cargada = bucle.cargar(d, semilla, estrategia, self.config, clave)
        if cargada is not None:
            self.reutilizadas += 1
            return cargada
        ej = bucle.ejecutar(semilla, self.config, estrategia, ruta, variante)
        m = metricas.calcular(ej)
        if ej.errores:
            m["errores"] = ej.errores
        bucle.guardar(ej, d, m, clave)
        ej.estados, ej.observaciones = [], []          # ya no hacen falta tras las métricas
        self.ejecutadas += 1
        print(f"  ejecutada {d.parent.name}/{d.name}", flush=True)
        return m, ej


def _diferencias_b0(nucleo: "bucle.Ejecucion", b0: "bucle.Ejecucion") -> dict:
    """Decisiones de B0 distintas de las del núcleo por sector e instante, en total y en los ciclos de
    conflicto (los del núcleo con un tie): por acción y por ángulo ordenado (más allá de la
    tolerancia, o nil frente a un ángulo); y trazabilidad, la proporción de episodios con criterio
    determinante (§11.3)."""
    instal = sm.instalacion()
    en = {(e["sector"], e["instante"]): e for e in nucleo.episodios}
    eb = {(e["sector"], e["instante"]): e for e in b0.episodios}
    conflicto = {k for k, e in en.items() if e["tipo-impasse"] == "tie"}
    def angulo_distinto(a, b, s):
        if a == "nil" or b == "nil":
            return a != b
        return abs(a - b) > instal[s]["tolerancia-angulo"]
    accion, angulo = set(), set()
    for k in en.keys() & eb.keys():
        if en[k]["accion"] != eb[k]["accion"]:
            accion.add(k)
        if angulo_distinto(en[k]["angulo-ordenado"], eb[k]["angulo-ordenado"], k[0]):
            angulo.add(k)
    def traz(eps):
        return sum(e["criterio-determinante"] != "nil" for e in eps.values()) / len(eps) if eps else 0.0
    return {"decisiones": len(en), "ciclos-conflicto": len(conflicto),
            "distintas-accion": len(accion), "distintas-angulo": len(angulo),
            "distintas-accion-conflicto": len(accion & conflicto),
            "distintas-angulo-conflicto": len(angulo & conflicto),
            "trazabilidad-nucleo": traz(en), "trazabilidad-b0": traz(eb)}


METRICAS_B0 = ["tie-100", "energia-kwh", "horas-estres-sector-dia", "movimientos-sector-dia", "escalados",
               "reglas-ciclo", "cpu-ms-ciclo"]


def b0_bucle(cache: Cache, semillas: list[int]) -> dict:
    """B0 frente al núcleo, los dos sin aprendizaje (C0), con las mismas semillas (§11.3)."""
    por_semilla, metr = {}, {"nucleo": {}, "b0": {}}
    for s in semillas:
        mn, en = cache.ejecucion(s, "depth", "C0")
        mb, eb = cache.ejecucion(s, "depth", "C0", "b0")
        metr["nucleo"][s], metr["b0"][s] = mn, mb
        por_semilla[s] = _diferencias_b0(en, eb)
    def serie(c, m):
        return np.array([metr[c][s][m] for s in semillas], dtype=float)
    comparaciones = {m: _comparacion(serie("nucleo", m), serie("b0", m), 0.0) for m in METRICAS_B0}
    p_holm = holm({m: c["p_bilateral"] for m, c in comparaciones.items()})
    for m in comparaciones:
        comparaciones[m]["p_holm"] = p_holm[m]
    medianas = {c: {m: float(np.median(serie(c, m))) for m in METRICAS_B0} for c in metr}
    def suma(clave):
        return sum(por_semilla[s][clave] for s in semillas)
    return {"experimento": "B0 frente al núcleo en bucle cerrado (roadmap §11.3)",
            "configuracion": {"semillas": semillas, "dias": cache.config["dias"], "base": "C0"},
            "por_semilla": por_semilla, "medianas": medianas, "comparaciones": comparaciones,
            "totales": {k: suma(k) for k in ("decisiones", "ciclos-conflicto", "distintas-accion",
                                             "distintas-angulo", "distintas-accion-conflicto",
                                             "distintas-angulo-conflicto")},
            "trazabilidad": {c: float(np.median([por_semilla[s][f"trazabilidad-{c}"] for s in semillas]))
                             for c in ("nucleo", "b0")},
            "violaciones": {c: sum(metr[c][s]["violaciones-decision"]["total"] for s in semillas) for c in metr},
            "errores": {f"{c}/{s}": metr[c][s]["errores"] for c in metr for s in semillas if "errores" in metr[c][s]}}


def resumen_b0(res: dict) -> str:
    conf, t = res["configuracion"], res["totales"]
    l = [f"{res['experimento']}: {len(conf['semillas'])} semillas × {conf['dias']} días, base {conf['base']}.",
         f"  violaciones de decisión: {res['violaciones']}",
         f"  decisiones distintas del núcleo: por acción {t['distintas-accion']}/{t['decisiones']}, por ángulo "
         f"{t['distintas-angulo']}/{t['decisiones']}; en los {t['ciclos-conflicto']} ciclos de conflicto (tie del "
         f"núcleo): por acción {t['distintas-accion-conflicto']}, por ángulo {t['distintas-angulo-conflicto']}",
         f"  trazabilidad (episodios con criterio determinante, mediana): núcleo {res['trazabilidad']['nucleo']:.3f}, "
         f"B0 {res['trazabilidad']['b0']:.3f}",
         f"  {'métrica':26s} {'núcleo':>9s} {'B0':>9s} {'mediana d':>10s} {'IC 95 %':>21s} {'biserial':>8s} {'p Holm':>8s}"]
    for m, c in res["comparaciones"].items():
        l.append(f"  {m:26s} {res['medianas']['nucleo'][m]:9.3f} {res['medianas']['b0'][m]:9.3f} "
                 f"{c['mediana_diferencia']:10.3f} [{c['ic95'][0]:8.3f}, {c['ic95'][1]:8.3f}] "
                 f"{c['biserial']:8.2f} {c['p_holm']:8.4f}")
    l.append("  d = núcleo − B0; Wilcoxon bilateral pareado con corrección de Holm.")
    if res["errores"]:
        l.append(f"  ERRORES de CLIPS en {sorted(res['errores'])}")
    return "\n".join(l)


def a3_bucle(cache: Cache, semillas: list[int]) -> dict:
    """A3s en bucle cerrado: depth frente a depth con a3s.clp, sin y con aprendizaje (§11.3)."""
    filas = []
    for base in BASES_I5:
        for s in semillas:
            _, ref = cache.ejecucion(s, "depth", base)
            _, otra = cache.ejecucion(s, "depth", base, "a3s")
            filas.append({"semilla": s, "base": base, **comparar_ejecuciones(ref, otra)})
    return {"experimento": "A3s en bucle cerrado (roadmap §11.3)",
            "configuracion": {"semillas": semillas, "dias": cache.config["dias"], "bases": list(BASES_I5)},
            "filas": filas,
            "por_base": {b: _discrepancias([f for f in filas if f["base"] == b]) for b in BASES_I5}}


def a1_bucle_i5(cache: Cache, semillas: list[int]) -> dict:
    """A1 y A2 en bucle cerrado sobre el caché, sin y con aprendizaje (§11.3). Cada estrategia se
    compara con depth (A1) y complexity con simplicity (A2). La CPU por ciclo, la única métrica
    que puede variar entre estrategias si se cumple la invariancia, se compara con Friedman."""
    filas, cpu = [], {b: {e: [] for e in ESTRATEGIAS_A1} for b in BASES_I5}
    for base in BASES_I5:
        for s in semillas:
            m, ref = cache.ejecucion(s, "depth", base)
            cpu[base]["depth"].append(m["cpu-ms-ciclo"])
            complejidad = None
            for e in ESTRATEGIAS_A1[1:]:
                m, otra = cache.ejecucion(s, e, base)
                cpu[base][e].append(m["cpu-ms-ciclo"])
                filas.append({"experimento": "A1", "semilla": s, "base": base, "estrategia": e,
                              **comparar_ejecuciones(ref, otra)})
                if e == "complexity":
                    complejidad = otra
                elif e == "simplicity":
                    filas.append({"experimento": "A2", "semilla": s, "base": base, "estrategia": e,
                                  **comparar_ejecuciones(complejidad, otra)})
                del otra
    por = {f"{x}/{b}/{e}": _discrepancias([f for f in filas if (f["experimento"], f["base"], f["estrategia"]) == (x, b, e)])
           for x, b, e in dict.fromkeys((f["experimento"], f["base"], f["estrategia"]) for f in filas)}
    return {"experimento": "A1 y A2 en bucle cerrado (roadmap §11.3)",
            "configuracion": {"semillas": semillas, "dias": cache.config["dias"], "bases": list(BASES_I5),
                              "estrategias": ESTRATEGIAS_A1, "semilla-agenda (random)": cache.config["semilla-agenda"]},
            "filas": filas, "por_comparacion": por,
            "cpu_mediana": {b: {e: float(np.median(v)) for e, v in c.items()} for b, c in cpu.items()},
            "cpu_friedman": {b: friedman({e: np.array(v) for e, v in c.items()}) for b, c in cpu.items()}}


def resumen_invariancia(res: dict, clave: str) -> str:
    conf = res["configuracion"]
    l = [f"{res['experimento']}: {len(conf['semillas'])} semillas × {conf['dias']} días, referencia depth "
         f"(A2: complexity).",
         f"  {'comparación':26s} {'discrepancias':>13s} {'IC 95 %':>17s} {'ciclos con secuencia igual':>27s}"]
    for nombre, r in res[clave].items():
        l.append(f"  {nombre:26s} {r['discrepancias']:>6d}/{r['semillas']:<6d} "
                 f"[{r['ic95'][0]:.3f}, {r['ic95'][1]:.3f}] {r['ciclos_secuencia_igual']:>14d}/{r['ciclos']}")
    if "cpu_friedman" in res:
        for b, f in res["cpu_friedman"].items():
            med = ", ".join(f"{e} {v:.2f}" for e, v in res["cpu_mediana"][b].items())
            l.append(f"  CPU por ciclo (ms, medianas) con {b}: {med}; Friedman p = {f['p_friedman']:.4g}")
            for par, v in f["pares"].items():
                if v["p_holm"] < 0.05:
                    l.append(f"    {par}: p Holm = {v['p_holm']:.4g}")
    return "\n".join(l)


def bateria_i5(cache: Cache, experimentos: list[str]) -> dict:
    """A1, A2 o A3s sobre la batería de casos, sin y con aprendizaje (§11.3)."""
    res = {}
    for base in BASES_I5:
        ruta = cache.base(base)
        for x in experimentos:
            res[f"{x}/{base}"] = {"A1": lambda: comparar(ESTRATEGIAS_A1, "A1", ruta),
                                  "A2": lambda: comparar(ESTRATEGIAS_A2, "A2", ruta),
                                  "A3s": lambda: comparar(["depth"], "A3s", ruta, "a3s")}[x]()
    return res


ETAPAS_I5 = ["aprenentatge", "b0", "a3", "a1"]          # el orden de lanzamiento (plan de I5)


def i5(semillas: list[int], dias: float | None, salida: Path, etapas: list[str] = ETAPAS_I5) -> tuple[str, bool]:
    """Experimentos completos de I5, en serie y reanudables. Cada etapa escribe su resultados.json y
    su resumen.txt al terminar; resumen.txt reúne todas las etapas ejecutadas."""
    config = _config(dias)
    config["semillas"] = semillas
    # δ de tie fijado con el piloto de I4, no con la mediana de C0 de estas semillas (§11.2)
    config["delta"]["tie-100"] = {"abs": config["delta"]["tie-100"]["piloto-i4"]}
    cache = Cache(salida / "ejecuciones", config)
    textos, correcto = [], True
    def escribir(nombre, res, texto):
        d = salida / nombre
        d.mkdir(parents=True, exist_ok=True)
        (d / "resultados.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        (d / "resumen.txt").write_text(texto + "\n", encoding="utf-8")
        textos.append(texto)
        print(texto, flush=True)
    for etapa in etapas:
        print(f"[{etapa}]", flush=True)
        if etapa == "aprenentatge":
            res = aprenentatge(semillas, configuraciones={c: CONFIGURACIONES[c] for c in ("C0", "C1", "C2")},
                               cache=cache)
            res["experimento"] = "Aprendizaje completo (roadmap §11.4), iteración I5"
            escribir(etapa, res, resumen_aprenentatge(res))
            correcto &= not any(res["violaciones"].values()) and not res["errores"]
        elif etapa == "b0":
            res = b0_bucle(cache, semillas)
            escribir(etapa, res, resumen_b0(res))
            correcto &= not any(res["violaciones"].values()) and not res["errores"]
        elif etapa in ("a3", "a1"):
            res = a3_bucle(cache, semillas) if etapa == "a3" else a1_bucle_i5(cache, semillas)
            clave = "por_base" if etapa == "a3" else "por_comparacion"
            texto = resumen_invariancia(res, clave)
            bat = bateria_i5(cache, ["A3s"] if etapa == "a3" else ["A1", "A2"])
            texto += "\n" + "\n".join(f"Batería, {k}:\n" + resumen(v) for k, v in bat.items())
            res["bateria"] = {k: {"configuracion": v["configuracion"], "invariante": invariante(v)} for k, v in bat.items()}
            escribir(etapa, res, texto)
            correcto &= all(r["discrepancias"] == 0 for r in res[clave].values()) and all(
                invariante(v) for v in bat.values())
    textos.append(f"Ejecuciones: {cache.ejecutadas} nuevas, {cache.reutilizadas} leídas del caché.")
    (salida / "resumen.txt").write_text("\n\n".join(textos) + "\n", encoding="utf-8")
    return "\n\n".join(textos), correcto


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
    p = sub.add_parser("a3s", help="A3s sobre la batería: depth frente a depth con salience (§11.3)")
    p.add_argument("--base", choices=["C0", "C2"], default="C2")
    p.add_argument("--salida", default=str(RESULTATS / "i5_a3s"))
    p = sub.add_parser("i5", help="experimentos completos de I5, reanudables (§11.2–§11.4)")
    p.add_argument("--semillas", nargs="+", type=int, default=list(range(10, 40)))
    p.add_argument("--dias", type=float, default=None)
    p.add_argument("--etapas", nargs="+", choices=ETAPAS_I5, default=ETAPAS_I5)
    p.add_argument("--salida", default=str(RESULTATS / "i5"))
    args = parser.parse_args(argv)

    if args.experimento == "i5":
        salida = RAIZ / args.salida
        texto, correcto = i5(args.semillas, args.dias, salida, args.etapas)
        print(f"\nResultados en {salida}")
        return 0 if correcto else 1

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

    if args.experimento == "a3s":
        base = on.generar_variante(CONFIGURACIONES[args.base], RAIZ / args.salida / "bases" / f"{args.base}.clp")
        res = a3s(base)
    else:
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
