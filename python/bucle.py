"""Bucle cerrado simulador ↔ CLIPS (roadmap §9).

En cada paso t: el simulador calcula las observaciones; Python las aserta y ejecuta CLIPS
(Pont.paso); las órdenes del instante t vuelven al simulador, que las aplica y avanza. Python
solo aserta la familia 1 y lee órdenes y episodios: no decide.

Los episodios se guardan por id en cada paso, sobrescribiendo la versión anterior, y se escriben
al final: así cada uno queda en su última versión (resultado verificado por MONITORATGE en t+1)
aunque NETEJA lo retire después de la ventana episódica.

    uv run python python/bucle.py --semilla 0 [--dias 1] [--salida resultats/prova]
"""

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import metricas
import simulador as sm
from pont_clips import RAIZ, Pont


@dataclass
class Ejecucion:
    semilla: int
    estrategia: str
    config: dict
    episodios: list[dict] = field(default_factory=list)       # última versión, por instante
    ordenes: list[dict] = field(default_factory=list)
    observaciones: list[dict] = field(default_factory=list)   # lo que se asertó en cada paso
    estados: list[dict] = field(default_factory=list)         # estado real en cada paso
    ciclos: list[dict] = field(default_factory=list)          # disparos, CPU y reglas por paso
    traza: str = ""
    errores: str = ""


def ejecutar(semilla: int, config: dict | None = None, estrategia: str | None = None) -> Ejecucion:
    config = config or sm.cargar_config()
    sim = sm.Simulador(semilla, config)
    pont = Pont(estrategia)                     # un Environment por ejecución (§14)
    ej = Ejecucion(semilla, pont.estrategia, config)
    episodios, trazas, errores = {}, [], []
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
        ordenes = [o for o in paso.ordenes if o["instante"] == t]
        ej.ordenes += ordenes
        ej.ciclos.append({"instante": t, "disparos": paso.disparos, "cpu": cpu, "reglas": paso.reglas})
        trazas.append(paso.traza)
        if paso.errores:
            errores.append(f"t={t}: {paso.errores}")
        sim.aplicar(ordenes)
    ej.episodios = sorted(episodios.values(), key=lambda e: (e["instante"], e["sector"]))
    ej.traza = "".join(trazas)
    ej.errores = "".join(errores)
    return ej


def guardar(ej: Ejecucion, directorio: Path, metricas: dict | None = None):
    """Registros de la ejecución y la configuración usada (§2.2, §9 paso 5)."""
    directorio.mkdir(parents=True, exist_ok=True)
    def jsonl(nombre, filas):
        (directorio / nombre).write_text("".join(json.dumps(f, ensure_ascii=False) + "\n" for f in filas),
                                         encoding="utf-8")
    jsonl("episodios.jsonl", ej.episodios)
    jsonl("ordenes.jsonl", ej.ordenes)
    jsonl("estado.jsonl", ej.estados)
    jsonl("ciclos.jsonl", [{k: v for k, v in c.items() if k != "reglas"} for c in ej.ciclos])
    (directorio / "traza.txt").write_text(ej.traza, encoding="utf-8")
    if metricas is not None:
        (directorio / "metricas.json").write_text(json.dumps(metricas, ensure_ascii=False, indent=1) + "\n",
                                                 encoding="utf-8")
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=RAIZ, capture_output=True, text=True).stdout.strip()
    (directorio / "configuracion.json").write_text(json.dumps(
        {"semilla": ej.semilla, "estrategia": ej.estrategia, "commit": commit, "simulacio": ej.config},
        ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


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
