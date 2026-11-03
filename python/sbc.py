"""Punto de entrada: demo, caso, aprendizaje y agenda."""

import argparse
import json
from pathlib import Path

from sistema import Sistema

SECTORES = ("s1", "s2", "s3")
ESTRATEGIAS = ("depth", "breadth", "lex", "mea", "complexity", "simplicity", "random")
# Valores tranquilos para lo que un caso no menciona: todo baix y el panel en 0°.
TRANQUILO = {"vent": 10, "radiacio": 100, "temp-cultiu": 15, "humitat-sol": 80,
             "angle-captacio": 0, "angle-ombra": -45, "panel": {"angulo-actual": 0}}


def observaciones_caso(sectores: dict) -> dict:
    return {s: {**TRANQUILO, **sectores.get(s, {})} for s in SECTORES}


def ejecutar_caso(ruta, estrategia="depth", aprendizaje=True, variante=None) -> tuple[dict, list]:
    """Ejecuta los pasos de un caso; devuelve el caso y el resultado de cada paso."""
    caso = json.loads(Path(ruta).read_text(encoding="utf-8"))
    sistema = Sistema(estrategia, aprendizaje, variante)
    return caso, [sistema.paso(p["t"], observaciones_caso(p.get("sectores", {}))) for p in caso["pasos"]]


def discrepancias(caso: dict, resultados: list) -> list[str]:
    """Diferencias entre lo esperado por el caso y lo obtenido (vacía si cuadra)."""
    errores = []
    for paso, r in zip(caso["pasos"], resultados):
        for s, esperado in paso.get("esperado", {}).items():
            e = r["episodios"][s]
            obtenido = {"accion": e["accion"], "impasse": None if e["tipo-impasse"] == "nil" else e["tipo-impasse"],
                        "chunk": e["chunk-aplicado"] != "nil"}
            for clave, valor in esperado.items():
                if obtenido[clave] != valor:
                    errores.append(f"t={paso['t']} {s} {clave}: esperado {valor}, obtenido {obtenido[clave]}")
        if "chunks" in paso and sorted(k["id"] for k in r["chunks"]) != sorted(paso["chunks"]):
            errores.append(f"t={paso['t']} chunks: esperado {paso['chunks']}, "
                           f"obtenido {[k['id'] for k in r['chunks']]}")
        if r["errores"]:
            errores.append(f"t={paso['t']} errores de CLIPS: {r['errores']}")
    return errores


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("orden", choices=("demo", "caso", "aprendizaje", "agenda"))
    ap.add_argument("fichero", nargs="?")
    ap.add_argument("--estrategia", choices=ESTRATEGIAS, default="depth")
    args = ap.parse_args()
    if args.orden == "caso":
        caso, resultados = ejecutar_caso(args.fichero, args.estrategia)
        print(f"{caso['descripcion']}\nRequisit: {caso['requisito']}\n")
        for paso, r in zip(caso["pasos"], resultados):
            print(f"===== t={paso['t']} =====\n{r['traza']}")
        print("\n".join(discrepancias(caso, resultados)) or "Resultat: tot com s'esperava")


if __name__ == "__main__":
    main()
