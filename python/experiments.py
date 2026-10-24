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
a2, la especificidad: complexity frente a simplicity. Sin simulador la ejecución es determinista
y no hay semillas de escenario: el piloto de §11.2 empieza en I3.

    uv run python python/experiments.py a1 [--estrategias depth breadth ...]
    uv run python python/experiments.py a2
"""

import argparse
import json
import subprocess
import sys
from collections import Counter

import executar_casos as ec
import pont_clips as pc
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="experimento", required=True)
    for nombre, ayuda, defecto in (("a1", "estrategias de agenda (§11.3)", ESTRATEGIAS_A1),
                                   ("a2", "especificidad: complexity frente a simplicity (§11.3)",
                                    ESTRATEGIAS_A2)):
        p = sub.add_parser(nombre, help=ayuda)
        p.add_argument("--estrategias", nargs="+", default=defecto)
        p.add_argument("--salida", default=str(RESULTATS / f"i2_{nombre}"))
    args = parser.parse_args(argv)

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
