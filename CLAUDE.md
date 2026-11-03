# CLAUDE.md

Práctica de Sistemes Basats en Coneixement (GIA, UPC): un sistema de reglas en CLIPS, inspirado en SOAR, que orienta los paneles de una instalación agrovoltaica de tres sectores y aprende por chunking.

**Objetivo del proyecto: explicabilidad y minimalidad.** El profesor valora que se vea que el sistema funciona como SOAR y aprende, no el volumen de código ni de documentación.

## Fuentes de verdad

1. `fuentes/enunciado.md`: mínimos obligatorios (§3.9 y §3.10).
2. `README.md`: **especificación del sistema.** Lo que dice el README es lo que el sistema hace. Si el código tiene que apartarse, se dice y se actualiza el README.
3. `ontologia/agrovoltaica-soar.ttl`: vocabulario y conocimiento estático. Se puede modificar, pero **contiene solo lo que el sistema usa**: si algo deja de usarse, se quita del TTL, de las plantillas y de `docs/ontologia-explicada.md`.

La versión anterior, mucho más grande, está en la etiqueta `v-roadmap3`. Se puede consultar con `git show v-roadmap3:<ruta>`, pero no se copia su complejidad.

## Reglas

- **CLIPS decide; Python no.** Python lee el TTL, simula, aserta observaciones y lee resultados. Nunca modifica ni retracta hechos.
- **Una regla, una idea,** con un comentario de una línea que dice qué hace y qué concepto de SOAR implementa.
- **Las condiciones van en patrones.** Las deffunctions solo calculan valores o consultan hechos que no cambian en la fase.
- **Salience 0** en todo el sistema, salvo en `clips/b0.clp`.
- **Cada regla de un módulo empieza con** `(estado-soar (id S0) (fase <su fase>))`.
- **Minimalidad.** Antes de añadir una regla, función, fichero, opción o métrica, pregúntate si el README la necesita. Si no, no se añade.
- **Portabilidad.** La demo es en Windows 11: nada específico de Linux. Usa `pathlib`.
- **Si algo no cuadra,** sea un experimento que contradice el README o un hueco del diseño, para y explícalo. No ajustes las reglas para que el resultado salga.

## Comandos

```bash
uv sync
uv run pytest
uv run python python/sbc.py demo | caso <fichero> | aprendizaje | agenda
```

Dependencias: con `uv add`, nunca con `pip`. `requirements.txt` se regenera con `uv export --no-hashes --no-dev -o requirements.txt` y no se edita a mano.

El aviso `[ENVRNMNT8] Environment data not fully deallocated` al final de la salida es una fuga conocida de CLIPS y no es un error.

## Forma de trabajar

- Un cambio cada vez, con `uv run pytest` en verde y un commit en castellano por cambio.
- Comentarios del código en castellano.
