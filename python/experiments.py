"""Experimentos (roadmap §11).

a1: experimento de agenda A1 (§11.3) sobre la batería de casos. Cada caso se ejecuta con
cada estrategia sobre las mismas entradas y se compara, ciclo a ciclo, con la primera:
  - el multiconjunto de nombres de reglas disparadas (debe ser igual) y su secuencia
    (puede diferir), indicando en qué módulos difiere;
  - las órdenes y los episodios por contenido, sin ids generados y con los multislots
    como conjuntos (§2.3.11);
  - la traza y el número de reglas disparadas.
En I1 la ejecución es determinista y no hay simulador, así que no hay semillas (§11.2 empieza en I3).

    uv run python python/experiments.py a1 [--estrategias depth breadth]
"""

import argparse
import json
import subprocess
import sys
from collections import Counter

import executar_casos as ec
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
        "traza_igual": ref.traza == otro.traza,
        "secuencias": [ref.reglas, otro.reglas],
    }


def a1(estrategias: list[str]) -> dict:
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
        "experimento": "A1 (roadmap §11.3), iteración I1",
        "configuracion": {
            "estrategias": estrategias,
            "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=RAIZ, capture_output=True,
                                     text=True).stdout.strip(),
            "base_coneixement": "config/base_coneixement.clp (sin sobrescrituras)",
            "casos": sorted({f["caso"] for f in filas}),
        },
        "ciclos": filas,
    }


def resumen_a1(res: dict) -> str:
    ciclos = res["ciclos"]
    n = len(ciclos)
    def contar(clave):
        return sum(c[clave] for c in ciclos)
    modulos = Counter(m for c in ciclos for m in c["modulos_con_secuencia_distinta"])
    lineas = [
        f"A1 con {' frente a '.join(res['configuracion']['estrategias'])}: "
        f"{len(res['configuracion']['casos'])} casos, {n} ciclos.",
        f"  multiconjunto de reglas igual:  {contar('multiconjunto_igual')}/{n}",
        f"  secuencia de disparo igual:     {contar('secuencia_igual')}/{n}",
        f"  órdenes iguales (contenido):    {contar('ordenes_iguales')}/{n}",
        f"  episodios iguales (contenido):  {contar('episodios_iguales')}/{n}",
        f"  traza igual:                    {contar('traza_igual')}/{n}",
        f"  módulos donde cambia la secuencia (ciclos): "
        + (", ".join(f"{m} ({k})" for m, k in modulos.most_common()) or "ninguno"),
        "  reglas disparadas por ciclo:",
    ]
    for c in ciclos:
        lineas.append(f"    {c['caso']:30s} t={c['instante']:<3d} {c['disparos'][0]:3d} {c['disparos'][1]:3d}"
                      + ("" if c["secuencia_igual"] else "   secuencia distinta"))
    return "\n".join(lineas)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="experimento", required=True)
    p_a1 = sub.add_parser("a1", help="experimento de agenda A1 (§11.3)")
    p_a1.add_argument("--estrategias", nargs="+", default=["depth", "breadth"])
    p_a1.add_argument("--salida", default=str(RESULTATS / "i1_a1"))
    args = parser.parse_args(argv)

    res = a1(args.estrategias)
    salida = RAIZ / args.salida                     # una ruta absoluta sustituye a RAIZ
    salida.mkdir(parents=True, exist_ok=True)
    (salida / "resultados.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n",
                                            encoding="utf-8")
    texto = resumen_a1(res)
    (salida / "resumen.txt").write_text(texto + "\n", encoding="utf-8")
    print(texto)
    print(f"\nResultados en {salida}")
    invariante = all(c["multiconjunto_igual"] and c["ordenes_iguales"] and c["episodios_iguales"]
                     and c["traza_igual"] for c in res["ciclos"])
    return 0 if invariante else 1


if __name__ == "__main__":
    sys.exit(main())
