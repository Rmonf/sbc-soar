"""Batería de casos de prueba (roadmap §10.2): ejecuta casos/*.json y compara con lo esperado.

Cada caso es una ejecución (un Environment nuevo) de uno o varios pasos. Por paso se comprueba
lo esperado en la orden y en el episodio del sector, lo prohibido (casos negativos) y unos
invariantes generales. Al final lista las reglas que ninguna ejecución ha disparado (§10.1).

    uv run python python/executar_casos.py [--estrategia depth]
"""

import argparse
import json
import sys
from pathlib import Path

from pont_clips import RAIZ, Paso, Pont

CASOS = RAIZ / "casos"


def cargar_casos(directorio: Path = CASOS) -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(directorio.glob("caso_*.json"))]


def ejecutar_caso(caso: dict, estrategia: str | None = None) -> list[Paso]:
    pont = Pont(estrategia)
    return [pont.paso(p["instante"], p.get("sensores", []), p.get("paneles", [])) for p in caso["pasos"]]


def sector_de(paso_caso: dict) -> str:
    return paso_caso["paneles"][0]["sector"] if paso_caso.get("paneles") else paso_caso["sensores"][0]["sector"]


def episodio_de(resultado: Paso, sector: str) -> dict | None:
    return next((e for e in resultado.episodios
                 if e["sector"] == sector and e["instante"] == resultado.instante), None)


def _igual(esperado, obtenido) -> bool:
    """Los multislots se comparan como conjuntos (§2.3.11)."""
    if isinstance(esperado, list):
        return isinstance(obtenido, list) and sorted(esperado) == sorted(obtenido)
    return esperado == obtenido


def comprobar(caso: dict, resultados: list[Paso]) -> list[str]:
    """Lista de fallos del caso; vacía si pasa."""
    fallos = []
    for n, (p, r) in enumerate(zip(caso["pasos"], resultados), start=1):
        donde = f"paso {n} (t={r.instante})"
        s = sector_de(p)
        if r.errores:
            fallos.append(f"{donde}: CLIPS ha escrito errores o avisos: {r.errores.strip()}")
        # Invariantes: una orden por sector, del instante actual (la de t−1 ya se ha retirado).
        ordenes = [o for o in r.ordenes if o["sector"] == s]
        if len(ordenes) != 1 or ordenes[0]["instante"] != r.instante:
            fallos.append(f"{donde}: se esperaba una orden de t={r.instante} para {s}, hay {ordenes}")
            continue
        orden, episodio = ordenes[0], episodio_de(r, s)
        if episodio is None:
            fallos.append(f"{donde}: no hay episodio de {s}")
            continue
        # Episodios vivos: los de los pasos dentro de la ventana episódica (§2.3.8, §5.11).
        vivos = sorted(e["instante"] for e in r.episodios)
        esperados = [q["instante"] for q in caso["pasos"][:n]
                     if q["instante"] >= r.instante - r.ventana_episodica]
        if vivos != esperados:
            fallos.append(f"{donde}: episodios de t={vivos}, se esperaban t={esperados}")
        if r.traza.count("Decisio:") != 1:
            fallos.append(f"{donde}: la traza tiene {r.traza.count('Decisio:')} decisiones, se esperaba 1")
        for slot, valor in p.get("esperado", {}).items():
            obtenido = orden[slot] if slot in orden else episodio.get(slot)
            if not _igual(valor, obtenido):
                fallos.append(f"{donde}: {slot} = {obtenido!r}, se esperaba {valor!r}")
        for slot, valores in p.get("prohibido", {}).items():
            if orden.get(slot) in valores:
                fallos.append(f"{donde}: {slot} = {orden[slot]!r} está prohibido")
    return fallos


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--estrategia", default=None, help="estrategia de agenda (por defecto, simulacio.json)")
    args = parser.parse_args(argv)

    casos = cargar_casos()
    disparadas, todas, fallidos = set(), [], 0
    for caso in casos:
        resultados = ejecutar_caso(caso, args.estrategia)
        todas = resultados[0].modulo_de
        for r in resultados:
            disparadas.update(r.reglas)
        fallos = comprobar(caso, resultados)
        fallidos += bool(fallos)
        print(f"{'PASS' if not fallos else 'FAIL'}  {caso['id']}  [{caso['requisito']}]")
        for f in fallos:
            print(f"      {f}")
    muertas = [f"{todas[r]}::{r}" for r in todas if r not in disparadas]
    print(f"\n{len(casos) - fallidos}/{len(casos)} casos pasan.")
    print(f"Reglas no disparadas en la batería (§10.1): {', '.join(muertas) or 'ninguna'}")
    return 1 if fallidos else 0


if __name__ == "__main__":
    sys.exit(main())
