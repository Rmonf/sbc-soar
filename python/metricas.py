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
decisiones; las reglas disparadas por ciclo son secundarias. Las métricas de los chunks (§11.4)
salen de los episodios (chunk-aplicado), de los chunks exportados y de los vivos en cada ciclo.

Dos métricas descriptivas de las incidencias de I5: las rachas de diagnosticar (ciclos seguidos
de un sector con esa acción, y su causa según la situación del episodio) y los empates por tipo
de día (la zona gris de s3, §5.5c.3).
"""

from statistics import mean

import simulador as sm

TIPOS_IMPASSE = ("tie", "dades-insuficients", "constraint-failure")
CAUSAS = ("personas", "sin-panel", "actuador", "viento", "desgaste")
RACHA_LARGA_MIN = 30        # una racha de diagnosticar es larga desde 30 min (criterio de informe)


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


def chunks(ej) -> dict:
    """Chunks vivos (máximo y final), compilados, olvidados, usos, usos confirmados (los que
    refuerzan, §6.2) y transferencia: proporción de usos en un sector que no aprendió el chunk,
    es decir, sin episodio tie con la acción preferida en el instante de creación (§11.4)."""
    vivos = [c.get("chunks", 0) for c in ej.ciclos]
    final = ej.ciclos[-1].get("instante") if ej.ciclos else None
    usos = [e for e in ej.episodios if e.get("chunk-aplicado", "nil") != "nil"]
    origen = {}
    for c in ej.chunks:
        origen[(c["id"], c["instante"])] = {
            e["sector"] for e in ej.episodios
            if e["instante"] == c["instante"] and e["tipo-impasse"] == "tie"
            and e["accion"] == c["accion-preferida"] and c["accion-descartada"] in e.get("alternativas", [])}
    transferidos = 0
    for e in usos:
        versiones = [k for k in origen if k[0] == e["chunk-aplicado"] and k[1] < e["instante"]]
        if versiones and e["sector"] not in origen[max(versiones, key=lambda k: k[1])]:
            transferidos += 1
    return {
        "chunks-vivos-max": max(vivos, default=0),
        "chunks-vivos-final": vivos[-1] if vivos else 0,
        "chunks-compilados": len(ej.chunks),
        "chunks-olvidados": sum(1 for c in ej.chunks if c["vivo-hasta"] != final),
        "usos-chunk": len(usos),
        "usos-chunk-confirmados": sum(1 for e in usos if e["resultado"] == "ok"),
        "transferencia": transferidos / len(usos) if usos else 0.0,
    }


def _causa(situacion: list[str]) -> str:
    """Causa de un diagnosticar según la situación del episodio (§5.4): fallada-actuador si la
    hay; si no, incertesa-dades."""
    tipos = {s.split(":")[0] for s in situacion}
    return next((c for c in ("fallada-actuador", "incertesa-dades") if c in tipos), "otra")


def diagnosticar(ej) -> dict:
    """Rachas de diagnosticar: ciclos consecutivos de un sector con esa acción. Por cada racha,
    su duración y la causa del primer episodio; las largas (≥ RACHA_LARGA_MIN) se cuentan por causa."""
    dt = ej.config["dt-min"]
    rachas = []                                     # (duración en ciclos, causa)
    por_sector = {}
    for e in sorted(ej.episodios, key=lambda e: (e["sector"], e["instante"])):
        por_sector.setdefault(e["sector"], []).append(e)
    for eps in por_sector.values():
        actual = None
        for e in eps:
            if e["accion"] != "diagnosticar":
                actual = None
                continue
            if actual is not None and e["instante"] - actual["fin"] == dt:
                actual["fin"] = e["instante"]
                rachas[actual["i"]][0] += 1
            else:
                actual = {"fin": e["instante"], "i": len(rachas)}
                rachas.append([1, _causa(e.get("situacion", []))])
    largas = [(n, c) for n, c in rachas if n * dt >= RACHA_LARGA_MIN]
    return {"diagnosticar-rachas": len(rachas),
            "diagnosticar-racha-max-min": max((n for n, _ in rachas), default=0) * dt,
            "diagnosticar-ciclos-rachas-largas": sum(n for n, _ in largas),
            "diagnosticar-rachas-largas": {c: sum(1 for _, c2 in largas if c2 == c)
                                           for c in sorted({c for _, c in largas})}}


def tie_por_tipo_dia(ej) -> dict:
    """Empates por tipo de día (zona gris, §5.5c.3): episodios tie y días de cada tipo."""
    tipo = {r["instante"]: r.get("tipus-dia") for r in ej.estados}
    pasos_dia = 24 * 60 // ej.config["dt-min"]
    dias = {}
    for i, r in enumerate(ej.estados):
        if i % pasos_dia == 0:
            dias[r.get("tipus-dia")] = dias.get(r.get("tipus-dia"), 0) + 1
    ties = dict.fromkeys(dias, 0)
    for e in ej.episodios:
        if e["tipo-impasse"] == "tie" and tipo.get(e["instante"]) in ties:
            ties[tipo[e["instante"]]] += 1
    return {"dias-por-tipo": dias, "tie-por-tipo-dia": ties}


def fidelidad(a, b) -> bool:
    """¿Toman dos ejecuciones las mismas decisiones en todos los pasos? Compara las órdenes
    (acción, ángulo y escalado por sector e instante), sin ids (H2, §11.4)."""
    def decisiones(ej):
        return sorted((o["instante"], o["sector"], o["accion"], o["angulo-ordenado"], o["escalado-humano"])
                      for o in ej.ordenes)
    return decisiones(a) == decisiones(b)


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
        **chunks(ej),
        **diagnosticar(ej),
        **tie_por_tipo_dia(ej),
    }
