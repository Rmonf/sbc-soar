"""Batería de casos de prueba (roadmap §10.2): ejecuta casos/*.json y compara con lo esperado.

Cada caso es una ejecución (un Environment nuevo) de uno o varios pasos. Un caso parte de una
base (casos/_base_*.json, los tres sectores con datos completos) e indica solo lo que cambia por
sector y paso; null quita una observación. La mezcla la hace este arnés, no el sistema: lo que se
aserta queda escrito en la base y en el caso. Por paso se comprueba lo esperado y lo prohibido
por sector y unos invariantes generales. Además de los slots de la orden y del episodio,
esperado admite resultado-previo (resultado del episodio del paso anterior) y traza-contiene
(textos que deben aparecer en la traza del paso). Un paso puede indicar además chunks: los ids de
los chunks vivos tras el paso, como conjunto (§6.2). Al final lista las reglas no disparadas (§10.1).

    uv run python python/executar_casos.py [--estrategia depth]
"""

import argparse
import copy
import json
import sys
from pathlib import Path

from pont_clips import RAIZ, Paso, Pont

CASOS = RAIZ / "casos"


def cargar_casos(directorio: Path = CASOS) -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(directorio.glob("caso_*.json"))]


def _mezclar(base, cambios):
    """Mezcla recursiva de diccionarios; un valor None quita la clave."""
    if not isinstance(base, dict) or not isinstance(cambios, dict):
        return copy.deepcopy(cambios)
    res = copy.deepcopy(base)
    for k, v in cambios.items():
        if v is None:
            res.pop(k, None)
        else:
            res[k] = _mezclar(res.get(k), v)
    return res


def expandir_paso(caso: dict, paso: dict) -> dict:
    """Observaciones concretas del paso: la base del caso con los cambios del paso."""
    base = json.loads((CASOS / f"{caso['base']}.json").read_text(encoding="utf-8"))
    sectores = _mezclar(base["sectores"], paso.get("sectores", {}))
    globales = _mezclar(base.get("predicciones-globales", {}), paso.get("predicciones-globales", {}))
    sensores, paneles, predicciones = [], [], []
    for s, datos in sectores.items():
        for variable, lectura in datos.get("sensores", {}).items():
            sensores.append({"sector": s, "variable": variable, **lectura})
        if "panel" in datos:
            paneles.append({"sector": s, **datos["panel"]})
        for variable, valor in datos.get("predicciones", {}).items():
            predicciones.append({"sector": s, "variable": variable, "valor": valor})
    for variable, valor in globales.items():
        predicciones.append({"variable": variable, "valor": valor})
    return {"sectores": sorted(sectores), "sensores": sensores, "paneles": paneles,
            "predicciones": predicciones}


def ejecutar_caso(caso: dict, estrategia: str | None = None) -> list[Paso]:
    pont = Pont(estrategia)
    resultados = []
    for p in caso["pasos"]:
        e = expandir_paso(caso, p)
        resultados.append(pont.paso(p["instante"], e["sensores"], e["paneles"], e["predicciones"]))
    return resultados


def episodio_de(resultado: Paso, sector: str) -> dict | None:
    return next((e for e in resultado.episodios
                 if e["sector"] == sector and e["instante"] == resultado.instante), None)


def bloques(traza: str) -> list[str]:
    """La traza en bloques: uno por decisión de sector (desde "Fets d'entrada") y uno por
    línea "Resultat observat", "Deliberacio" o "Aprenentatge". El orden entre bloques depende de
    la estrategia (§2.3.11)."""
    res = []
    for linea in traza.splitlines(keepends=True):
        if linea.startswith(("Fets d'entrada:", "Resultat observat", "Deliberacio", "Aprenentatge")) or not res:
            res.append(linea)
        else:
            res[-1] += linea
    return res


def bloque_de(traza: str, sector: str) -> str | None:
    return next((b for b in bloques(traza)
                 if b.startswith("Fets d'entrada:") and f", sector={sector}," in b.splitlines()[0]),
                None)


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
        if r.errores:
            fallos.append(f"{donde}: CLIPS ha escrito errores o avisos: {r.errores.strip()}")
        if "chunks" in p and sorted(c["id"] for c in r.chunks) != sorted(p["chunks"]):
            fallos.append(f"{donde}: chunks vivos {sorted(c['id'] for c in r.chunks)}, se esperaban {sorted(p['chunks'])}")
        for s in expandir_paso(caso, p)["sectores"]:
            # Invariantes: una orden por sector, del instante actual (la de t−1 ya se ha retirado),
            # su episodio y un bloque de traza.
            ordenes = [o for o in r.ordenes if o["sector"] == s]
            if len(ordenes) != 1 or ordenes[0]["instante"] != r.instante:
                fallos.append(f"{donde}: se esperaba una orden de t={r.instante} para {s}, hay {ordenes}")
                continue
            orden, episodio = ordenes[0], episodio_de(r, s)
            if episodio is None:
                fallos.append(f"{donde}: no hay episodio de {s}")
                continue
            # Episodios vivos: los de los pasos dentro de la ventana episódica (§2.3.8, §5.11).
            vivos = sorted(e["instante"] for e in r.episodios if e["sector"] == s)
            esperados = [q["instante"] for q in caso["pasos"][:n]
                         if q["instante"] >= r.instante - r.ventana_episodica]
            if vivos != esperados:
                fallos.append(f"{donde}: episodios de {s} en t={vivos}, se esperaban t={esperados}")
            decisiones = sum(1 for b in bloques(r.traza)
                             if b.startswith("Fets d'entrada:") and f", sector={s}," in b.splitlines()[0])
            if decisiones != 1:
                fallos.append(f"{donde}: la traza tiene {decisiones} bloques de {s}, se esperaba 1")
            for slot, valor in p.get("esperado", {}).get(s, {}).items():
                if slot == "resultado-previo":              # episodio del paso anterior (§5.2)
                    previo = next((e for e in r.episodios if e["sector"] == s
                                   and e["instante"] == caso["pasos"][n - 2]["instante"]), {})
                    obtenido = previo.get("resultado")
                elif slot == "traza-contiene":              # textos que la traza del paso incluye
                    obtenido = [t for t in valor if t in r.traza]
                else:
                    obtenido = orden[slot] if slot in orden else episodio.get(slot)
                if not _igual(valor, obtenido):
                    fallos.append(f"{donde}: {s}.{slot} = {obtenido!r}, se esperaba {valor!r}")
            for slot, valores in p.get("prohibido", {}).get(s, {}).items():
                obtenido = orden[slot] if slot in orden else episodio.get(slot)
                prohibidos = set(obtenido if isinstance(obtenido, list) else [obtenido]) & set(valores)
                if prohibidos:
                    fallos.append(f"{donde}: {s}.{slot} contiene {sorted(prohibidos)}, que está prohibido")
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
