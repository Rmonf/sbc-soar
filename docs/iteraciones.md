# Registro de iteraciones

Qué se hizo en cada iteración (roadmap §11.1), qué decisiones cambiaron el roadmap (con su commit y su motivo), los resultados de cada experimento, las incidencias abiertas y el siguiente paso. Sale de los commits, del roadmap y de las notas de los planes de ejecución. Se actualiza al cerrar cada iteración.

Los resultados completos se regeneran en `resultats/` (ignorado por git) con los comandos de CLAUDE.md.

---

## I0. Ontología, generador y verificador

### Qué se implementó
- `python/ontologia.py` lee el TTL en un modelo Python (`15fe07f`): las clases, las propiedades (con sus enumeraciones) y los individuos coinciden con los totales de §2.1.
- Las 9 plantillas del conocimiento estático en `clips/00_main.clp`, con su introspección (`092d6db`). Se adelantaron a I0 porque las necesita el generador.
- Generador de `config/base_coneixement.clp` (`4f35950`): un hecho por individuo, en orden determinista. Con `--set` se generan variantes de experimento y con `--salida`, ficheros fuera del versionado. El fichero carga en clipspy y el `reset` da 66 hechos.
- Verificador `--verificar` de §10.1 (`df2f9e9`), en mundo cerrado:
  - vocabulario, dominio, rango, propiedades funcionales, enumeraciones, disyunción y completitud;
  - partición de los umbrales;
  - tabla de fases;
  - objetivos, sectores y datos requeridos;
  - TTL frente a las plantillas.

### Decisiones que cambiaron el roadmap
| Commit | Cambio | Motivo |
|---|---|---|
| `092d6db` | §2.3.7: un slot numérico opcional es `(type NUMBER SYMBOL) (allowed-symbols nil) (default nil)` | CLIPS rechaza `(default nil)` en un slot `NUMBER`. |
| `092d6db` | §3.2: `situacion`, `alternativas` y `descartes` son multislot | En el TTL no son funcionales. |
| `568748f` | §10.1: la prueba por mutación es el experimento de cierre de I0; §8: directorio `tests/` | Probar el propio verificador. |
| `fa5a56c`, `7d4439d`, `481ecd3`, `b59a4bb` | Correcciones editoriales y de estilo del roadmap | Sin cambio de diseño. |

### Experimento: prueba por mutación del verificador (`568748f`)
Cada mutación introduce un error conocido en una copia del TTL o de `00_main.clp`, y la prueba comprueba que el verificador lo detecta con la categoría esperada.

| Origen | Mutaciones al cierre de I0 | Detectadas | Categorías |
|---|---|---|---|
| TTL | 20 | 20 | `enumeracion`, `vocabulario`, `funcional`, `rango`, `dominio`, `disyuncion`, `completitud`, `umbrales`, `fases`, `objetivos`, `sectores`, `datos-requeridos` |
| `00_main.clp` | 5 | 5 | `plantillas` |

En I3 se añadieron dos mutaciones más del TTL, de la categoría `tolerancia` (`790416f`). Hoy son 22 + 5, todas detectadas.

---

## I1. Prototipo vertical de un sector

### Qué se implementó
- **Comprobaciones de §14:** todas OK, con estos hallazgos:
  - el router de clipspy no puede reclamar el nombre lógico `build`;
  - `env.rules()` solo devuelve las reglas del módulo actual, así que se usa `(get-defrule-list *)`;
  - `reset` no reinicia `gensym*`, así que los ids se derivan del contenido;
  - un `test` no se reevalúa si cambia un hecho que no está en el LHS.
- **MAIN:** plantillas dinámicas, deffunctions y las cinco reglas de control (`364083e`).
- **Módulos mínimos para un sector:** viento → `mantenir-posicio` o `posicio-seguretat` (`d44c608`, `b984b05`, `a4a2600`).
  - ELABORACIO, PROPOSTA, AVALUACIO (R2, valoración, acción útil y estabilidad), SELECCIO (S3 y S4), MONITORATGE, APLICACIO, EXPLICACIO y NETEJA;
  - la traza la escribe una sola regla cuando el episodio está completo.
- **Puente y casos (`ce905ed`):**
  - `pont_clips.py` usa un `Environment` por ejecución;
  - `executar_casos.py` lista las reglas no disparadas;
  - batería de 11 casos, con tests de regresión y de traza.
- **Experimento A1** con `depth` y `breadth` (`c4da473`).

### Decisiones que cambiaron el roadmap
| Commit | Cambio | Motivo |
|---|---|---|
| `364083e` | §8: deffunction `accion-sin-movimiento` | La necesitan varias fases. |
| `af3281d` | §5.5c.2: con Δ dentro de la tolerancia, la acción sin movimiento es `better` | Evita un `tie` (y su escalado) en cada ciclo de viento `alt` con el panel ya en defensa. Caso 12. |
| `7de15e4` | §2.3.8: la ventana episódica es el defglobal `?*ventana-episodica*` | Es una constante de convención, no un umbral del dominio. NETEJA retira los episodios antiguos. Caso 13. |
| `d5c0b96` | §5.3: la abstracción ignora las lecturas `fallada` | Un valor fallado es desconocido (§3.2). Caso 14. |
| `c659859` → `dab4032` | §13: fuga `ENVRNMNT8` de CLIPS documentada; primero se filtraba y al final no se filtra | Filtrarla complicaba el código y no funcionaba en Windows. |
| `d316cd1` | La calidad de cada lectura de sensor es obligatoria en `pont_clips` (sin cambio en el roadmap) | Sin ella, CLIPS pondría `ok` y se imputaría en silencio un dato no observado (§3.2). |

### Experimento: A1, `depth` frente a `breadth` (§11.3)
| Momento | Casos | Ciclos | Multiconjunto igual | Secuencia igual | Órdenes, episodios y traza iguales |
|---|---|---|---|---|---|
| Cierre del prototipo | 11 | 12 | 12/12 | 0/12 | 12/12 |
| Tras las decisiones posteriores | 14 | 17 | 17/17 | 0/17 | 17/17 |

La hipótesis se cumple: la estrategia cambia el orden de disparo, pero no lo que se decide ni lo que se explica.

---

## I2. Las 11 fases, tres sectores e impasses

### Qué se implementó (pasos P0–P6)
- **P0 (`5901141`):** plantilla `prediccion`, que es global si el sector es nil.
  - Los casos pasan al formato "base + cambios" (`casos/_base_tranquil.json`, con `null` para quitar una observación).
  - La traza se compara por bloques de sector.
- **P1 (`cf7a7f4`):** PERCEPCIO (`incertesa-dades` con evidencia y nivel máximo) y MONITORATGE (verificación de t−1: `ok` o `fallada-actuador`; la orden se retracta en los tres resultados). Casos 15–23.
- **P2 (`56905b8`):**
  - ELABORACIO con las tres referencias y las predicciones;
  - los seis diagnósticos con sus refinamientos;
  - `orientar-ombra` y `orientar-produccio`;
  - valoración, criterios ordenados con zona gris y acción útil.

  Casos 24–41.
- **P3 (`69f2e37`):** R1–R5 (R4 usa la memoria episódica), y `posicio-seguretat` también por incertidumbre. Casos 42–49.
- **P4 (`e491ab0`):**
  - SELECCIO S1–S7;
  - DELIBERACIO con un subestado `sub-<impasse>` por impasse y estrategias mutuamente excluyentes;
  - `escalado-humano`, criterio determinante, impasse en la traza y limpieza de subestados.

  Casos 50–55.
- **P5 (`0b6f18e`):** casos con los tres sectores a la vez (martes difícil, noche del operador, tres impasses, temporal). Casos 56–59.
- **P6 (`d73e1b5`, `1712cf7`):** valores límite de los umbrales que deciden (casos 60–70) y experimentos A1 (7 estrategias) y A2.

### Decisiones que cambiaron el roadmap
| Commit | Cambio | Motivo |
|---|---|---|
| `cf7a7f4` | §3.3 (evidencias de `incertesa-dades`), §5.9 (traza sin panel: `panell=desconegut`, línea `Evidencies`) y §8 | Explicar con qué hechos se infiere (anexo B). El caso 14 cambia por la llegada de PERCEPCIO. |
| `56905b8` | §5.3 (las predicciones globales se abstraen para cada sector; también se ignoran las lecturas antiguas) y §8 | Las reglas emparejan por sector. |
| `69f2e37` | §8 | Funciones de R4 y de la definición de "candidato que mueve". |
| `e491ab0` | §5.7 (`escalat` es una reserva inalcanzable, probada con una variante de configuración), §5.9 (orden del criterio determinante: `escalat` → `require` → `better` de deliberación o chunk → `better` de regla) y §10.1 (reglas no disparadas justificadas) | Garantizar la terminación sin reglas muertas sin justificar. Los casos 14 y 17 cambian por la llegada de S1. |

### Experimentos A1 y A2 (§11.3), sobre la batería
| Experimento | Casos | Ciclos | Estrategias frente a la referencia | Multiconjunto | Secuencia igual | Órdenes, episodios y traza | Disparos (ref.) |
|---|---|---|---|---|---|---|---|
| A1 (ref. `depth`), cierre de I2 | 70 | 92 | `breadth`, `lex`, `mea`, `complexity`, `simplicity`, `random` | 92/92 cada una | 0/92 | 92/92 cada una | 11 850 (11 850) |
| A2 (`complexity` frente a `simplicity`), cierre de I2 | 70 | 92 | `simplicity` | 92/92 | 0/92 | 92/92 | 11 850 (11 850) |
| A1, tras las correcciones de I3 | 76 | 99 | las mismas 6 | 99/99 cada una | 0/99 | 99/99 cada una | 12 903 (12 903) |
| A2, tras las correcciones de I3 | 76 | 99 | `simplicity` | 99/99 | 0/99 | 99/99 | 12 903 (12 903) |

Las dos hipótesis son invariantes. Las únicas reglas no disparadas son las de la reserva de escalado (`escalar-impasse`, `s7-escalado` y `anotar-criterio-escalat`), probadas en `tests/test_escalado.py`.

---

## I3. Simulador en bucle cerrado, pilotos y potencia

### Qué se implementó (pasos Q0–Q6)
- **Q0 (`077efca`):** un panel con lectura antigua cuenta como ausente. Da incertidumbre `critic` con evidencia `observacio-panel:antiga`, R5 y MONITORATGE `pendent`. Casos 71–73.
- **Q1 (`78f2d59`):** cada estrategia de deliberación escribe una línea `Deliberacio` con lo que comparó y el resultado.
- **Q2 (`be0a3f4`):** `python/simulador.py`, heurístico y reproducible:
  - meteorología, geometría solar, cultivo y panel;
  - el conocimiento estático lo lee del TTL;
  - un generador aleatorio por proceso.
- **Q3 (`6ad5da2`):** `python/bucle.py` conecta el simulador con CLIPS en bucle cerrado. Exporta episodios (en su última versión), órdenes, estado real, ciclos, traza y configuración.
- **Q4 (`2768f25`):** fallos inyectables por probabilidad o con un calendario fijo:
  - sensor `fallada`, `degradat`, antiguo o ausente;
  - panel sin comunicación o con lectura antigua;
  - actuador encallado o en `alarma`;
  - movimiento no ordenado;
  - personas o maquinaria;
  - tormenta.
- **Q5 (`d7e462f`):** `python/metricas.py`:
  - violaciones de decisión (deben ser 0) y exposición real (informativa);
  - `tie` por cada 100 decisiones (métrica principal de H1);
  - escalados, movimientos, reglas y CPU por ciclo, energía y horas de estrés.
- **Q6 (`e2b8278`, `a354fb9`):** δ fijados antes del piloto; `experiments.py piloto` y `a1-bucle`.
  - **Arreglo del simulador:** las órdenes se aplican en orden de sector. A1 en bucle cerrado destapó que el error aleatorio de posición dependía del orden de las órdenes, que depende de la estrategia.

### Decisiones que cambiaron el roadmap
| Commit | Cambio | Motivo |
|---|---|---|
| `077efca` | §3.3, §5.1, §5.2 y §8: solo cuenta el panel vigente | Un panel antiguo es un dato desconocido. |
| `78f2d59` | §5.9: línea `Deliberacio` en la traza | Explicar qué comparó la deliberación. |
| `2768f25` | §9: fallos inyectables | Enunciado 3.8. |
| `0978ccd` | §11.2 y §11.4: cota σ_d ≤ √2·σ (válida si ρ ≥ 0), n provisional hasta I4, δ fijados de antemano, violaciones de decisión separadas de la exposición real; `tie` por cada 100 decisiones como métrica principal de H1 y reglas por ciclo como secundaria | Diseño estadístico del piloto. |
| `d582007` | §11.2 y §11.4: el δ de `tie` pasa a ser relativo, δ = 0,5 · mediana de C0, fijado tras el piloto y antes de cualquier dato de C1 | El δ absoluto (1 por cada 100 decisiones) era inalcanzable con una mediana de 0,198. |
| `a052830` | §5.5b, §5.5c, §5.7 y §6.2: la acción sin movimiento hereda los beneficios de los candidatos con coste `baix`; los criterios ordenados la comparan también a ella; regla de **cercanía**; acción útil solo si no hereda nada; argumento de corrección del chunk sin el invariante | El panel oscilaba entre sombra y producción: un candidato ya alcanzado perdía su beneficio. Cambian los casos 09, 12, 38, 43 y 66 (cada uno con una clave `cambio`); casos nuevos 74–76. |
| `a6dd26a` | §9: una orden a menos de la tolerancia del ángulo real no mueve el panel; el error de posición tiene un generador propio | `mantenir` ordena el ángulo observado (con ruido) y el panel derivaba como un paseo aleatorio. Con el generador propio, las decisiones no cambian los fallos de los sensores. |
| `bcd027d` | §9: tipos de día `templat`/`calor`/`nuvol` (0,5/0,3/0,2), nubosidad AR(1); final de primavera, datos sintéticos | Antes todos los días eran de calor (temperatura del cultivo entre 12 y 17 h con mediana de 33 °C en los tres sectores). |
| `790416f` | §10.1: comprobación de que la tolerancia de cada seguidor es menor que el límite `baix`/`mitja` de `moviment`, con dos mutaciones | El argumento de §6.2 depende de ello. |
| `c4479c7` | §11.2: la nota del δ de `tie`, con las cifras del piloto repetido | Cierre de la iteración. |

### Experimento: piloto del núcleo, 10 semillas × 7 días (§11.2)

**Antes de la corrección de §5.5b** (`a354fb9`; un solo tipo de día, δ de `tie` absoluto):

| Métrica | Mediana | IQR | σ | δ | n |
|---|---|---|---|---|---|
| `tie` por cada 100 decisiones (principal) | 0,198 | 0,149–0,273 | 0,075 | 1,000 | 30 |
| Energía (kWh) | 19 905 | 18 203–20 172 | 2 022 | 398 | 405 |
| Horas de estrés por sector y día | 6,50 | 5,71–7,02 | 0,74 | 1,0 | 30 |
| Movimientos por sector y día | 35,7 | 33,9–36,2 | 2,21 | 2,0 | 30 |
| Reglas por ciclo | 182,5 | 181,1–184,0 | 2,50 | 9,13 | 30 |
| CPU por ciclo (ms) | 10,32 | 10,23–10,45 | 0,19 | 1,03 | 30 |

- Violaciones de decisión: 0, ninguna semilla afectada (IC 95 % [0; 0,308]).
- Exposición real: 42 órdenes (40 con el actuador encallado y 2 con viento).
- **Análisis de los movimientos.** `angle-captacio` cambia 0,714° por ciclo. Aun así, solo el 0,3 % de los movimientos tenía Δ ≤ 5°: el coste `baix` (< 5°) anulaba la persecución fina del sol.
  - 28,2 de los 35,3 movimientos por sector y día eran cambios entre `orientar-ombra` y `orientar-produccio`, con un Δ mediano de unos 45°, limitados solo por R4.
  - En el 89 % de las salidas de la sombra el estrés era `alt` o `critic`.
  - La tolerancia no era la causa; el defecto estaba en §5.5b.

**Después de las correcciones** (§5.5b, orden dentro de la tolerancia, tipos de día; δ de `tie` relativo):

| Métrica | Mediana | IQR | σ | δ | n |
|---|---|---|---|---|---|
| `tie` por cada 100 decisiones (principal) | 1,596 | 1,339–1,881 | 0,690 | 0,798 | 30 |
| Energía (kWh) | 22 897 | 21 943–23 254 | 965 | 458 | 70 |
| Horas de estrés por sector y día | 3,70 | 3,15–4,57 | 1,19 | 1,0 | 30 |
| Movimientos por sector y día | 19,7 | 19,4–20,3 | 0,74 | 2,0 | 30 |
| Reglas por ciclo | 181,0 | 179,3–184,2 | 3,83 | 9,05 | 30 |
| CPU por ciclo (ms) | 10,20 | 9,99–10,33 | 0,19 | 1,02 | 30 |

- Violaciones de decisión: 0, ninguna semilla afectada (IC 95 % [0; 0,308]).
- Exposición real: 46 órdenes, todas con el actuador encallado.

Desglose del piloto repetido:

| | s1 (tomate) | s2 (lechuga) | s3 (viña) |
|---|---|---|---|
| `tie` por cada 100 decisiones | 0 | 0 | 4,65 |
| Movimientos por sector y día | 21,6 | 19,4 | 18,4 |
| Horas de estrés: día `nuvol` / `templat` / `calor` | 0 / 0,1 / 9,7 | 1,0 / 4,2 / 13,1 | 0 / 0 / 4,7 |

- **Días sorteados:** 37 `templat`, 22 `calor` y 11 `nuvol`.
- **Empates por día:** 0 los días `nuvol`, 0,35 los `templat` y 42 los `calor`. Es la zona gris de s3: la viña con estrés `mitja` y el panel en sombra, frente a producción.
- **Movimientos:** 3047 repiten la acción (seguimiento del sol, con un Δ mediano de 5,6°) frente a 1079 que la cambian.
- **Escenario secundario de zona gris:** propuesto y descartado, porque el escenario principal ya tiene bastantes empates.

### Análisis de potencia (provisional hasta I4)
n = ((z₀,₉₇₅ + z₀,₈) · σ_d / δ)², con la cota σ_d ≤ √2·σ (válida si ρ ≥ 0) y un mínimo de 30 semillas. Con el piloto repetido: **30** para todas las métricas salvo la energía, que necesita **70**. La gran σ de la energía viene de la variabilidad meteorológica entre semillas; con el diseño pareado, la σ_d real debería ser bastante menor.

### Experimento: A1 en bucle cerrado, 10 semillas × 7 días (§11.3)
| Estrategia (ref. `depth`) | Discrepancias (antes de la corrección) | Discrepancias (después) | IC 95 % | Ciclos con secuencia igual |
|---|---|---|---|---|
| `breadth` | 0/10 | 0/10 | [0; 0,308] | 0/20 160 |
| `lex` | 0/10 | 0/10 | [0; 0,308] | 0/20 160 |
| `mea` | 0/10 | 0/10 | [0; 0,308] | 0/20 160 |
| `complexity` | 0/10 | 0/10 | [0; 0,308] | 0/20 160 |
| `simplicity` | 0/10 | 0/10 | [0; 0,308] | 0/20 160 |
| `random` | 0/10 | 0/10 | [0; 0,308] | 0/20 160 |

"Antes" ya incluye el arreglo del orden de aplicación de las órdenes.

### Estado al cierre
- 0 anomalías en la verificación, 239 tests y 76/76 casos en verde.
- A1 y A2 son invariantes en la batería y en bucle cerrado.

---

## Incidencias abiertas
- **Fuga `ENVRNMNT8` (§13):** CLIPS deja unos 128 bytes por cada hecho con multislot que Python leyó y una regla retractó después. Son unos 0,8 MB por ejecución de 7 días. Aparece al final de la salida, no afecta a ningún resultado y, por decisión del equipo, no se filtra.
- **`escalat` sigue siendo inalcanzable** con el conocimiento actual. Es una reserva de terminación probada con una variante de configuración (`tests/test_escalado.py`).
- **Los n son provisionales:** usan la cota √2·σ, válida solo si ρ ≥ 0. El de la energía (70) es el que más depende de ella.
- **Modelos del simulador heurísticos:** la lechuga (umbral de 26 °C, del TTL) tiene unas 4 h de estrés también los días templados, lo que es plausible para lechuga en verano. Los parámetros meteorológicos son sintéticos y no están calibrados con datos reales.

## Siguiente paso: I4 (APRENENTATGE)
Chunking con refuerzo y olvido (§5.10, §6), regla S5, plantilla `chunk` y configuraciones C0, C1 y C2 (§11.4). Dos pendientes de I3:

1. **Comprobar con casos el argumento de §6.2:** el chunk sigue siendo correcto sin el invariante para la acción sin movimiento. Si `mantenir` está en un empate de dos, el otro candidato está a 5° o más (la cercanía lo dominaría si no), así que la relación es siempre `menor` y decide `minima-intervencio`. La condición estática (tolerancia < límite `baix`/`mitja` de `moviment`) ya la comprueba `--verificar`; faltan los casos que lo ejerciten con chunks.
2. **Recalcular n con la σ_d real** de las diferencias por semilla entre C0 y C1. Con la mediana de C0, δ de `tie` = 0,5 · esa mediana.
