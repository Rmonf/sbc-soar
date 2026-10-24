"""Métricas de una ejecución en bucle cerrado (roadmap §11.2).

Son un oráculo de evaluación: se calculan después, a partir de los registros, y no influyen en
ninguna decisión. Las restricciones duras se miden de dos formas:
  - violaciones de decisión: contra lo observado en ese ciclo, es decir, lo que CLIPS sabía.
    Deben ser 0; una sola indica un error del sistema;
  - exposición real: las mismas condiciones contra el estado real del simulador (p. ej.,
    personas que un panel sin comunicación no mostraba). Es informativa: mide el efecto de los
    fallos de observación, no un error de la decisión.

Una orden mueve si su ángulo no es nil y difiere del ángulo previo en más de la tolerancia
(definiciones de §5, R4). La métrica principal de H1 (§11.4) son los impasses tie por cada 100
decisiones; las reglas disparadas por ciclo son secundarias.
"""

from statistics import mean

import simulador as sm

TIPOS_IMPASSE = ("tie", "dades-insuficients", "constraint-failure")
CAUSAS = ("personas", "sin-panel", "actuador", "viento", "desgaste")


def _mueve(e: dict, tol: float) -> bool:
    return (e["angulo-ordenado"] != "nil" and e["angulo-previo"] != "nil"
            and abs(e["angulo-ordenado"] - e["angulo-previo"]) > tol)


def _observado(obs: dict, sector: str):
    """Panel vigente y lecturas válidas de viento (observado y previsto) del sector en el ciclo."""
    t = obs["instante"]
    panel = next((p for p in obs["paneles"] if p["sector"] == sector and p["instante"] == t), None)
    vientos = [s["valor"] for s in obs["sensores"]
               if s["sector"] == sector and s["variable"] == "vent" and s["calidad"] != "fallada"
               and s.get("instante", t) == t]
    vientos += [p["valor"] for p in obs["predicciones"]
                if p.get("sector") == sector and p["variable"] == "vent-previst"]
    return panel, vientos


def calcular(ej, instal: dict | None = None) -> dict:
    instal = instal or sm.instalacion()
    dt, dias = ej.config["dt-min"], ej.config["dias"]
    por_paso = {o["instante"]: (o, e) for o, e in zip(ej.observaciones, ej.estados)}
    episodios = {(e["sector"], e["instante"]): e for e in ej.episodios}
    decision = dict.fromkeys(CAUSAS, 0)
    exposicion = dict.fromkeys(("personas", "actuador", "viento", "desgaste"), 0)
    movimientos = 0
    for (s, t), e in episodios.items():
        p = instal[s]
        if not _mueve(e, p["tolerancia-angulo"]):
            continue
        movimientos += 1
        obs, real = por_paso[t]
        panel, vientos = _observado(obs, s)
        r = real["sectores"][s]
        previo = episodios.get((s, t - dt))
        recientes = sum(1 for (s2, t2), e2 in episodios.items()
                        if s2 == s and t - 60 <= t2 < t and _mueve(e2, p["tolerancia-angulo"]))
        orienta = e["accion"] in ("orientar-produccio", "orientar-ombra")
        # violaciones de decisión: contra lo observado
        if panel is None:
            decision["sin-panel"] += 1
        else:
            decision["personas"] += panel["ocupacion"] != "lliure"
            decision["actuador"] += (panel["estado-mecanico"] != "operatiu"
                                     or (previo is not None and previo["resultado"] == "fallada-actuador"))
        decision["viento"] += orienta and any(v >= p["umbral-viento-critico"] for v in vientos)
        desgaste = e["accion"] != "posicio-seguretat" and recientes >= p["max-movimientos-hora"]
        decision["desgaste"] += desgaste
        # exposición real: contra el estado del simulador
        exposicion["personas"] += r["ocupacion"] != "lliure"
        exposicion["actuador"] += r["estado-mecanico"] != "operatiu" or r["actuador-encallat"]
        exposicion["viento"] += orienta and real["viento"] >= p["umbral-viento-critico"]
        exposicion["desgaste"] += desgaste
    n = len(episodios)
    impasses = {ti: sum(1 for e in episodios.values() if e["tipo-impasse"] == ti) for ti in TIPOS_IMPASSE}
    escalados = sum(1 for e in episodios.values() if e["escalado-humano"] == "TRUE")
    estres = 0
    for real in ej.estados:
        for s, r in real["sectores"].items():
            estres += (r["temp-cultiu"] > instal[s]["umbral-temp-estres"]
                       or r["humitat"] < instal[s]["umbral-humedad-critica"])
    acciones = {}
    for e in episodios.values():
        acciones[e["accion"]] = acciones.get(e["accion"], 0) + 1
    sectores = len(instal)
    return {
        "decisiones": n,
        "violaciones-decision": {"total": sum(decision.values()), **decision},
        "exposicion-real": {"total": sum(exposicion.values()), **exposicion},
        "tie-100": 100 * impasses["tie"] / n if n else 0.0,
        "impasses-100": {ti: 100 * k / n if n else 0.0 for ti, k in impasses.items()},
        "escalados": escalados,
        "movimientos-sector-dia": movimientos / (sectores * dias),
        "reglas-ciclo": mean(c["disparos"] for c in ej.ciclos),
        "cpu-ms-ciclo": 1000 * mean(c["cpu"] for c in ej.ciclos),
        "energia-kwh": sum(r["produccion"] for real in ej.estados for r in real["sectores"].values()) * dt / 60,
        "horas-estres-sector-dia": estres * dt / 60 / (sectores * dias),
        "acciones": acciones,
    }
