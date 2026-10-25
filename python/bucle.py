"""Bucle cerrado simulador ↔ CLIPS (roadmap §9).

En cada paso t: el simulador calcula las observaciones; Python las aserta y ejecuta CLIPS
(Pont.paso); las órdenes del instante t vuelven al simulador, que las aplica y avanza. Python
solo aserta la familia 1 y lee órdenes, episodios y chunks: no decide.

Los episodios se guardan por id en cada paso, sobrescribiendo la versión anterior, y se escriben
al final: así cada uno queda en su última versión (resultado verificado por MONITORATGE en t+1)
aunque NETEJA lo retire después de la ventana episódica. Los chunks se guardan igual, por id e
instante de creación (un chunk olvidado y vuelto a aprender reutiliza el id, §5.10), con el último
instante en que estaban vivos.

La CPU por ciclo solo es comparable sin otras cargas (§11.2): cada ejecución guarda el loadavg al
empezar y al terminar y el número de CPU. Las reglas disparadas de cada ciclo se guardan como dos
huellas (del multiconjunto y de la secuencia), suficientes para comparar estrategias (§11.3) a
partir de ejecuciones guardadas; cargar() las lee para reanudar un experimento.

    uv run python python/bucle.py --semilla 0 [--dias 1] [--salida resultats/prova]
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import metricas
import simulador as sm
from pont_clips import BASE, RAIZ, Pont


@dataclass
class Ejecucion:
    semilla: int
    estrategia: str
    config: dict
    episodios: list[dict] = field(default_factory=list)       # última versión, por instante
    chunks: list[dict] = field(default_factory=list)          # última versión, con vivo-hasta
    ordenes: list[dict] = field(default_factory=list)
    observaciones: list[dict] = field(default_factory=list)   # lo que se asertó en cada paso
    estados: list[dict] = field(default_factory=list)         # estado real en cada paso
    ciclos: list[dict] = field(default_factory=list)          # disparos, CPU, reglas y huellas por paso
    traza: str = ""
    errores: str = ""
    entorno: dict = field(default_factory=dict)               # carga de la máquina (§11.2)


def huella(reglas) -> str:
    return hashlib.sha1("\n".join(reglas).encode()).hexdigest()[:16]


def ejecutar(semilla: int, config: dict | None = None, estrategia: str | None = None,
             base: Path = BASE, variante: str | None = None) -> Ejecucion:
    """Una ejecución; base permite una configuración variante, p. ej. C0 sin aprendizaje (§2.2), y
    variante, las reglas de clips/variants/ del experimento de agenda (§11.3)."""
    config = config or sm.cargar_config()
    sim = sm.Simulador(semilla, config)
    pont = Pont(estrategia, base, variante)     # un Environment por ejecución (§14)
    ej = Ejecucion(semilla, pont.estrategia, config)
    episodios, chunks, trazas, errores = {}, {}, [], []
    ej.entorno = {"loadavg-inicio": os.getloadavg(), "cpus": os.cpu_count()}
    for _ in range(sim.pasos):
        t = sim.instante()
        obs = sim.observaciones()
        ej.estados.append(sim.estado_real())
        ej.observaciones.append(obs)
        inicio = time.process_time()
        paso = pont.paso(t, obs["sensores"], obs["paneles"], obs["predicciones"])
        cpu = time.process_time() - inicio
        for e in paso.episodios:
            episodios[e["id"]] = e
        for c in paso.chunks:
            chunks[(c["id"], c["instante"])] = {**c, "vivo-hasta": t}
        ordenes = [o for o in paso.ordenes if o["instante"] == t]
        ej.ordenes += ordenes
        ej.ciclos.append({"instante": t, "disparos": paso.disparos, "cpu": cpu, "reglas": paso.reglas,
                          "chunks": len(paso.chunks), "multiconjunto": huella(sorted(paso.reglas)),
                          "secuencia": huella(paso.reglas)})
        trazas.append(paso.traza)
        if paso.errores:
            errores.append(f"t={t}: {paso.errores}")
        sim.aplicar(ordenes)
    ej.episodios = sorted(episodios.values(), key=lambda e: (e["instante"], e["sector"]))
    ej.chunks = sorted(chunks.values(), key=lambda c: (c["instante"], c["id"]))
    ej.traza = "".join(trazas)
    ej.errores = "".join(errores)
    ej.entorno["loadavg-fin"] = os.getloadavg()
    return ej


def guardar(ej: Ejecucion, directorio: Path, metricas: dict | None = None, clave: dict | None = None):
    """Registros de la ejecución y la configuración usada (§2.2, §9 paso 5). clave describe la
    configuración del experimento (base, variante…) y permite reanudarlo (cargar)."""
    directorio.mkdir(parents=True, exist_ok=True)
    def jsonl(nombre, filas):
        (directorio / nombre).write_text("".join(json.dumps(f, ensure_ascii=False) + "\n" for f in filas),
                                         encoding="utf-8")
    jsonl("episodios.jsonl", ej.episodios)
    jsonl("ordenes.jsonl", ej.ordenes)
    jsonl("chunks.jsonl", ej.chunks)
    jsonl("estado.jsonl", ej.estados)
    jsonl("ciclos.jsonl", [{k: v for k, v in c.items() if k != "reglas"} for c in ej.ciclos])
    (directorio / "traza.txt").write_text(ej.traza, encoding="utf-8")
    if metricas is not None:
        (directorio / "metricas.json").write_text(json.dumps(metricas, ensure_ascii=False, indent=1) + "\n",
                                                 encoding="utf-8")
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=RAIZ, capture_output=True, text=True).stdout.strip()
    (directorio / "configuracion.json").write_text(json.dumps(
        {"semilla": ej.semilla, "estrategia": ej.estrategia, "commit": commit, "simulacio": ej.config,
         "clave": clave or {}, "entorno": ej.entorno, "errores": ej.errores},
        ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def cargar(directorio: Path, semilla: int, estrategia: str, config: dict,
           clave: dict | None = None) -> tuple[dict, Ejecucion] | None:
    """Ejecución guardada con la misma semilla, estrategia, simulación y clave, con sus métricas;
    None si no hay ninguna completa. Lee órdenes, episodios, chunks, ciclos (sin las reglas, con
    sus huellas), traza y entorno; no lee el estado real ni las observaciones."""
    try:
        conf = json.loads((directorio / "configuracion.json").read_text(encoding="utf-8"))
        m = json.loads((directorio / "metricas.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if (conf.get("semilla"), conf.get("estrategia"), conf.get("simulacio"), conf.get("clave")) != \
            (semilla, estrategia, config, clave or {}):
        return None
    def jsonl(nombre):
        return [json.loads(l) for l in (directorio / nombre).read_text(encoding="utf-8").splitlines()]
    ej = Ejecucion(semilla, estrategia, config, episodios=jsonl("episodios.jsonl"), chunks=jsonl("chunks.jsonl"),
                   ordenes=jsonl("ordenes.jsonl"), ciclos=jsonl("ciclos.jsonl"),
                   traza=(directorio / "traza.txt").read_text(encoding="utf-8"),
                   errores=conf.get("errores", ""), entorno=conf.get("entorno", {}))
    return m, ej


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--semilla", type=int, default=0)
    parser.add_argument("--dias", type=float, default=None, help="días simulados (por defecto, simulacio.json)")
    parser.add_argument("--estrategia", default=None)
    parser.add_argument("--salida", default="resultats/prova")
    args = parser.parse_args(argv)
    config = sm.cargar_config()
    if args.dias is not None:
        config["dias"] = args.dias
    ej = ejecutar(args.semilla, config, args.estrategia)
    guardar(ej, RAIZ / args.salida / f"semilla_{args.semilla}", metricas.calcular(ej))
    print(f"semilla {args.semilla}: {len(ej.ciclos)} pasos, {len(ej.ordenes)} órdenes, "
          f"{len(ej.episodios)} episodios, errores: {ej.errores or 'ninguno'}")
    return 1 if ej.errores else 0


if __name__ == "__main__":
    sys.exit(main())
