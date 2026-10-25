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

## I4. APRENENTATGE: chunking con refuerzo y olvido

### Qué se implementó (pasos K0–K8)
- **K0 (`974e645`):** cambios de especificación aprobados con el plan (tabla siguiente).
- **K1 (`a9b612f`):** plantilla `chunk` (§3.2) y deffunctions de MAIN `beneficio-maximo`, `relacio-delta`, `activacio` y `chunk-aplicable` (§8). `--verificar` ya no avisa de plantillas pendientes.
- **K2 (`1fe5c1d`):** `compilar-chunk`, a partir de un `tie` de dos resuelto por `minima-intervencio` o `prioritat-objectius`, con la detección de duplicados en el LHS (un `not` sobre las cinco condiciones, que Rete reevalúa; un `test` no se reevaluaría, §14). `pont_clips` lee `chunk` y los casos admiten la clave `chunks` (chunks vivos tras el paso).
- **K3 (`19877f0`):**
  - S5 aplica el chunk a un empate de dos, y S6 niega exactamente su condición: con tres o más no dominados, S6 abre el `tie` (`tests/test_seleccio_chunk.py`, con SELECCIO sola y los hechos construidos a mano, porque con el conocimiento actual no hay empates de tres);
  - EXPLICACIO anota `chunk-aplicado` y la línea `Decisio` nombra el chunk y su estrategia;
  - `bloques()` reconoce `Aprenentatge`.

  Caso 77.
- **K4 (`339b2b4`):** `reforzar-chunk` (uso confirmado, recorte a `max-referencias`) y `olvidar-chunk` (activación base, salvo refuerzo pendiente). `ontologia.generar_variante` genera las variantes de los tests y los experimentos. Casos 78–80 (refuerzo, sin refuerzo tras `fallada-actuador`, olvido y nuevo aprendizaje con el mismo id; el caso 80 prueba desde `a4bb375` el límite de 55 ciclos) y test del recorte con `max-referencias=2`.
- **K5 (`6db8e1e`):** el primer pendiente de I3, el argumento de §6.2 con casos:
  - casos 81 (la acción sin movimiento hereda cultivo, frente a producción) y 82 (hereda energía, frente a sombra): el chunk se compila con relación `menor` desde `minima-intervencio` y, al reutilizarse, decide lo mismo;
  - `tests/test_chunk_fidelidad.py`: los 82 casos deciden igual paso a paso con y sin aprendizaje; una rejilla de s3 con 48 situaciones en dos pasos usa 24 veces un chunk (12 chunks distintos, 6 con la acción sin movimiento como preferida), y en todas el chunk decide como la deliberación;
  - con la variante de s1 con sensibilidad `mitja`, un chunk aprendido en s3 se aplica en s1, y dos sectores con el mismo empate en un ciclo compilan un solo chunk, con la misma traza en `depth` y `breadth`.
- **K6 (`8acfe4d`):** `bucle` exporta `chunks.jsonl` (última versión por id e instante de creación, con `vivo-hasta`) y los chunks vivos por ciclo, y admite una base variante. `metricas` añade los chunks vivos, compilados, olvidados, usos, usos confirmados, transferencia y `fidelidad`.
- **K7 (`04fa295`):** `experiments.py aprenentatge`.

### Decisiones que cambiaron el roadmap
| Commit | Cambio | Motivo |
|---|---|---|
| `974e645` | §5.10, §5.9: el id del chunk se deriva de sus cinco condiciones; un chunk olvidado y vuelto a aprender reutiliza el id | `gensym*` no se reinicia (I1), y el chunk no debe depender de qué sector lo compiló cuando dos empatan igual en el mismo ciclo. |
| `974e645` | §5.9, §5.10: bloques `Aprenentatge (t=…)` propios en la traza, sin sector; `Resultat observat` ya no menciona el chunk | Que la traza no dependa del orden de disparo y que cada fase escriba lo suyo. |
| `974e645` | §5.6: S6 niega exactamente la condición de S5 (dos no dominados y chunk aplicable) | Con tres o más no dominados, S6 abre el `tie` como siempre. |
| `974e645` | §5.5c.2: la cercanía se aplica a todo candidato que no es una acción sin movimiento y tiene coste `baix`, también con Δ dentro de la tolerancia | Era lo que hacía el código, y lo que necesita el argumento de §6.2. |
| `974e645` | §11.4: C1 usa `umbral-olvido` = −100; la transferencia es 0 por construcción y la generalización se prueba con una variante | Solo la viña (sensibilidad `mitja`) puede tener estrés `mitja` tras el ajuste, así que solo s3 empata. |
| cierre | §11.2: nota del δ y del n con la σ_d real de C0 − C1 | Segundo pendiente de I3. |
| `a4bb375` | §2.3.8, §5.10, §6.2, §8 y §11.4: la activación base mide el tiempo en ciclos de decisión (Δt = 5 min, `?*minutos-por-ciclo*`, mínimo 1 ciclo), y no en horas; §6.3: dos diferencias más con Soar (aproximación de Petrov y referencias simultáneas); §7: el `reject` de R1–R5 cumple el papel del `prohibit` | Contraste con el manual (cap. 2) y el kernel de Soar: `time_forward` avanza una vez por ciclo de decisión. El caso 80 pasa a probar el límite de 55 ciclos (t=270 conserva el chunk y t=275 lo olvida). |

### Experimento: piloto del aprendizaje, 10 semillas × 7 días (§11.4)
Las mismas semillas para las cinco configuraciones (diseño pareado). Hay 0 violaciones de decisión en todas. La activación mide el tiempo en ciclos de decisión de 5 min (`a4bb375`). C0 y C1 no dependen de la activación y no se repitieron (`--reutilizar C0 C1`); C2 y el barrido sí. La primera ejecución, con el tiempo en horas, está al final de esta sección.

| Configuración | `tie` por cada 100 decisiones: mediana (IQR) | Chunks vivos: máx. / final (medianas) | Compilados / olvidados (medianas) | Fidelidad frente a C0 |
|---|---|---|---|---|
| C0 (sin aprendizaje) | 1,596 (1,339–1,881) | — | — | — |
| C1 (umbral −100) | 0,174 (0,153–0,182) | 10,5 / 10,5 | 10,5 / 0 | 10/10 (IC 95 % [0,692; 1]) |
| C2 (umbral −2) | 0,223 (0,215–0,281) | 8 / 6 | 13,5 / 7 | 10/10 |
| umbral −1 | 0,306 (0,285–0,393) | 6,5 / 2 | 18,5 / 17,5 | 10/10 |
| umbral −3 | 0,198 (0,169–0,215) | 10 / 7,5 | 12 / 3,5 | 10/10 |

- **H1:** C0 − C1 tiene una mediana de diferencias de 1,414 (IC 95 % por bootstrap [1,108; 1,935]; Wilcoxon unilateral, d > δ, p = 0,0137). C0 − C2 tiene 1,331 ([1,042; 1,794]; p = 0,0186). Las dos superan δ = 0,798. Es un piloto: el contraste con n semillas es de I5.
- **Contabilidad exacta:** en las 10 semillas y en todas las configuraciones con aprendizaje, `tie`(C0) = `tie`(Cx) + usos de chunk(Cx), y los `tie` que quedan son exactamente las compilaciones: uno por chunk nuevo o vuelto a aprender. Todos los usos se confirmaron `ok`.
- **H2:** las órdenes son idénticas a las de C0 en las 10 semillas y en las cuatro configuraciones con aprendizaje. Por tanto, energía, estrés y movimientos coinciden.
- **H3:** se cumple en el piloto.
  - Con el umbral −2, un chunk con una sola referencia se olvida tras 55 ciclos sin uso (unas 4,6 h), así que los chunks de un día de calor suelen olvidarse durante la noche.
  - C2 mantiene menos chunks vivos que C1 (máximo 8 frente a 10,5 y final 6 frente a 10,5) y olvida una mediana de 7.
  - A cambio, el reaprendizaje aumenta los `tie` en 0,058 por cada 100 decisiones (C2 − C1, IC 95 % [0,033; 0,116]; unos 3,5 por semilla), muy por debajo de δ = 0,798.
- **Barrido del umbral:**
  - −1 olvida casi todo (17,5 de 18,5) y casi duplica las compilaciones;
  - −3 olvida 3,5 y queda cerca de C1;
  - **se mantiene −2**, el valor por defecto de Soar: está entre los dos y su coste en `tie` es pequeño.
- **Transferencia:** 0, como se esperaba (§11.4).
- **Coste:** las reglas por ciclo prácticamente no cambian (C0 181,04; C1 180,81; C2 180,84). La CPU por ciclo no permite comparar: C0 y C1 se midieron a la vez que A1 en bucle cerrado (10,9 y 11,9 ms) y C2 y el barrido, en solitario (10,7–10,9 ms).

**Primera ejecución, con el tiempo en horas** (antes de `a4bb375`; resultados en `resultats/i4_aprenentatge_horas/`): un chunk se olvidaba a las ~55 h.
- C2 dio un `tie` de 0,182 y olvidó una mediana de 1 chunk.
- El aumento frente a C1 fue de 0,008 (IC [0; 0,033]).
- El barrido dio −1 → 0,215 y −3 → igual que C1.
- H3 apenas se distinguía en 7 días.

El cambio a ciclos de decisión, tras contrastarlo con el kernel de Soar, es lo que hace visible el olvido. La duración y el escenario no se cambiaron.

### Análisis de potencia con la σ_d real (segundo pendiente de I3)
| Métrica | σ_d (C0 − C1) | δ | n |
|---|---|---|---|
| `tie` por cada 100 decisiones | 0,642 | 0,798 | 30 |
| Energía (kWh) | 0 | 457,9 | 30 |
| Horas de estrés por sector y día | 0 | 1,0 | 30 |
| Movimientos por sector y día | 0 | 2,0 | 30 |
| Reglas por ciclo | 0,130 | 9,05 | 30 |
| CPU por ciclo (ms) | 0,685 | 1,09 | 30 |

Con la fidelidad del 100 %, las métricas de dominio de C0 y C1 son idénticas y su σ_d es 0. El n = 70 de la energía venía de la cota √2·σ y desaparece. Para H3, σ_d(C2 − C1) de `tie` es 0,051. **n = 30 para todo en I5.**

### A1 y A2 con el aprendizaje activo (§11.3)
| Experimento | Unidad | Estrategias frente a la referencia | Resultado |
|---|---|---|---|
| A1 sobre la batería (ref. `depth`) | 82 casos, 114 ciclos | 6 | 114/114 multiconjunto, órdenes, episodios y traza iguales en cada una; 0/114 secuencias iguales; 15 145 disparos |
| A2 sobre la batería (`complexity` frente a `simplicity`) | 82 casos, 114 ciclos | 1 | 114/114 |
| A1 en bucle cerrado (ref. `depth`) | 10 semillas × 7 días | 6 | 0/10 discrepancias en cada una (IC 95 % [0; 0,308]); 0/20 160 ciclos con la secuencia igual |

APRENENTATGE no depende del orden de disparo: la invariancia se mantiene con el aprendizaje activo, en la batería y en bucle cerrado.

### Estado al cierre
- 0 anomalías en la verificación, 343 tests y 82/82 casos en verde.
- Las únicas reglas no disparadas son las de la reserva de escalado.
- A1 y A2 son invariantes con el aprendizaje activo.
- En el piloto, H1 supera δ, H2 se cumple en las 10 semillas y H3 se cumple: C2 mantiene menos chunks que C1 con un aumento de `tie` de 0,058, menor que δ.

---

## I5. Congelación: experimentos completos y casos no vistos

El conocimiento del núcleo (`clips/01…11`, el TTL y la base generada) no cambia en I5.

### Qué se implementó (pasos L0–L6)
- **L0 (`0326cd7`):** especificación de I5 (tabla siguiente).
- **L1 (`44ff6a4`):**
  - `metricas` añade las rachas de `diagnosticar` (número, la más larga y las de 30 min o más por causa) y los empates por tipo de día;
  - `bucle` guarda el `loadavg` y el número de CPU de cada ejecución, guarda las reglas de cada ciclo como huellas del multiconjunto y de la secuencia, y `cargar` lee una ejecución guardada;
  - `experiments` añade la correlación biserial de rangos, Holm y Friedman con Wilcoxon por pares.
- **L2 (`9d564be`):** variante A3s (`clips/variants/a3s.clp`) y carga de variantes en `pont_clips` (`VARIANTES`), `bucle` y `executar_casos`. `tests/test_variantes.py` comprueba que cada regla copiada es textualmente igual a la de producción salvo el `declare`, y que el código de producción no tiene salience.
- **L3 (`4de6ca8`):** línea base B0 (`clips/variants/b0.clp`), con tests: copias de R1–R5 y de `descartar-resto`, salience = 6 − la prioridad del TTL, viento `alt` no crítico (caso 05: `posicio-seguretat`, igual que el núcleo), R1 (caso 42), empate del caso 54 decidido por salience sin impasse ni criterio, y la batería entera sin errores.
- **L4 (`c7e7a7b`):** `experiments.py i5`, en serie y reanudable, con las etapas aprendizaje → B0 → A3 → A1/A2. Un caché compartido (`resultats/i5/ejecuciones/<estrategia>-<base>-<variante>/semilla_n`) guarda cada ejecución con una clave que incluye la huella del código que la produce; C0 y C2 con `depth` sirven a todas las etapas.
- **L5 (`37b98dc`):** seis casos no vistos en `casos_no_vistos/` y `executar_casos.py --no-vistos`.
- **L6:** cierre: verificación (0 anomalías), 364 tests y 82/82 casos; las únicas reglas no disparadas son las de la reserva de escalado.

### Decisiones que cambiaron el roadmap
| Commit | Cambio | Motivo |
|---|---|---|
| `0326cd7` | §10.2 y §13: la validación con expertos pasa a trabajo futuro; en su lugar, casos no vistos de los testimonios sin salida esperada, que el equipo valora a posteriori | Decisión del equipo al planificar I5. |
| `0326cd7` | §11.2: semillas confirmatorias 10–39 en I5; CPU en serie, sin otras cargas y con el `loadavg` registrado | Que el contraste no reutilice los datos que fijaron δ y σ_d; incidencia de la CPU ruidosa de I4. |
| `0326cd7` | §11.3: definición de A3s y de B0. B0 tiene las mismas condiciones de §5.4 y las mismas restricciones R1–R5; solo cambia la resolución del conflicto (salience = 6 − prioridad, la primera regla gana) | §11.3 no decía qué sustituye B0. Que la comparación mida conflictos, empates y trazabilidad, no seguridad. |
| `9d564be` | §11.3: salience de A3s negativa (−10 los refinamientos, −20 las restricciones) | Con valores positivos, la secuencia solo cambiaba en 3 de los 115 ciclos de la batería con `depth`; con negativos, en 34. |
| `c7e7a7b` | §11.2: en I5, el δ de `tie` es el del piloto de I4 (0,798, `simulacio.json`), sin recalcularlo con las semillas nuevas | Fijado antes de ver los resultados completos (§11.2). |

### Experimento: aprendizaje completo, semillas 10–39 × 7 días (§11.4)
`resultats/i5/aprenentatge/`. Violaciones de decisión: 0 en C0, C1 y C2.

| Medida | C0 | C1 | C2 |
|---|---|---|---|
| `tie` por 100 decisiones, mediana [IQR] | 1,091 [0,562, 1,699] | 0,132 [0,116, 0,165] | 0,190 [0,120, 0,231] |
| Chunks vivos, máximo / final (mediana) | – | 8 / 8 | 7 / 4 |

| Hipótesis | Resultado | p (Holm) | ¿Se cumple? |
|---|---|---|---|
| H1, C0 − C1 > δ = 0,798 | mediana 0,951, IC 95 % [0,587, 1,314] | 0,120 | **No** al 5 % |
| H1, C0 − C2 > δ | mediana 0,926, IC 95 % [0,579, 1,265] | 0,120 | **No** al 5 % |
| H2, órdenes idénticas a C0 | C1 y C2: 30/30, IC 95 % [0,884, 1,000] | – | Sí |
| H3, C2 − C1 < δ | mediana 0,033, IC 95 % [0,017, 0,066] | 2,4·10⁻⁶ | Sí |

- **H1 no se confirma con las semillas confirmatorias.** La mediana de la reducción (0,95) supera δ, pero el IC llega por debajo y el contraste unilateral frente a δ da p = 0,06 y 0,10 (0,12 con Holm). La reducción es claramente positiva (el IC excluye 0), pero no se puede afirmar que supere δ. σ_d = 0,80 ≈ δ, así que n = 30 era el mínimo justo; la dispersión entre semillas de `tie` en C0 (IQR 0,56–1,70) es la que manda. Se informa tal cual; no se cambia δ a posteriori.
- **Contabilidad** `tie`(C0) = `tie`(Cx) + usos(Cx): 30/30 en C1 y en C2.
- **Transferencia** (mediana, C2): 0, como se esperaba (incidencia abierta).
- **CPU por ciclo** (`loadavg` máximo 1,13 en 12 CPU, limpio): C1 gasta 0,29 ms más por ciclo que C0 (IC [0,10, 0,41], biserial 0,88) y C2 0,15 ms más (IC [0,005, 0,46]). Es el coste de emparejar los chunks, muy por debajo del δ de CPU (1,05 ms).

### Experimento: B0 frente al núcleo, 30 semillas × 7 días, base C0 (§11.3)
`resultats/i5/b0/`. Violaciones de decisión: 0 en los dos.

| Métrica (mediana) | Núcleo | B0 | d = núcleo − B0, IC 95 % | p (Holm) |
|---|---|---|---|---|
| `tie` por 100 decisiones | 1,091 | 0 | 1,091 [0,711, 1,496] | < 10⁻⁴ |
| Energía (kWh, 7 días) | 22 539 | 22 766 | −234 [−275, −166] | < 10⁻⁴ |
| Horas de estrés por sector y día | 3,00 | 3,02 | −0,002 [−0,008, 0,004] | 0,42 |
| Movimientos por sector y día | 20,2 | 34,9 | −14,9 [−15,1, −14,6] | < 10⁻⁴ |
| Escalados | 0 | 0 | 0 | 0,42 |
| Reglas por ciclo | 178,4 | 156,5 | 22,0 [20,4, 23,4] | < 10⁻⁴ |
| CPU por ciclo (ms) | 10,50 | 9,60 | 0,90 [0,84, 0,96] | < 10⁻⁴ |

- **Decisiones distintas:** 68 895 de 181 440 por acción (38 %) y 81 429 por ángulo (45 %). En los 2212 ciclos de conflicto (con `tie` en el núcleo), 1807 por acción y 1344 por ángulo.
- **Trazabilidad:** el núcleo registra un criterio determinante en el 48,5 % de los episodios (mediana); B0, en ninguno.
- **Lectura.** Con las mismas condiciones de §5.4 y las mismas restricciones, B0 no tiene ni un empate ni una violación, pero no sabe explicar por qué elige y mueve los paneles casi el doble: la regla de `produccio-energia` gana a la de `estabilitat` en cada ciclo en que hay oportunidad, porque B0 no tiene la valoración de coste del movimiento (§5.5b) ni la preferencia de mínima intervención. Así gana un 1 % de energía sin cambiar el estrés del cultivo. En la batería coincidía con el núcleo en 325/345 decisiones porque los casos son de uno o pocos pasos.

### Experimento: A1, A2 y A3s, 30 semillas × 7 días, sin (C0) y con (C2) aprendizaje (§11.3)
`resultats/i5/a1/` y `resultats/i5/a3/`.

| Comparación | Discrepancias (C0 y C2) | IC 95 % |
|---|---|---|
| A1: `breadth`, `lex`, `mea`, `complexity`, `simplicity`, `random` frente a `depth` | 0/30 cada una | [0, 0,116] |
| A2: `simplicity` frente a `complexity` | 0/30 | [0, 0,116] |
| A3s frente a `depth` | 0/30 | [0, 0,116] |

- La secuencia de reglas cambia en todos los ciclos con A1 y A2, y en 10 411 de 60 480 con A3s (en C0 y en C2, con las mismas cifras por semilla: los refinamientos que reordena A3s no dependen de los chunks). El multiconjunto, las órdenes, los episodios y la traza son iguales en todos los ciclos.
- **Batería:** A1, A2 y A3s son invariantes con C0 y con C2 en los 115 ciclos. A3s cambia la secuencia en 34 ciclos (AVALUACIO 31, ELABORACIO 4).
- **CPU por estrategia** (medianas, ms por ciclo; C0): `depth` 10,50, `breadth` 10,29, `lex` 10,42, `mea` 10,46, `complexity` 10,35, `simplicity` 10,39, `random` 10,40. Friedman p = 8·10⁻¹² (C0) y 3·10⁻¹¹ (C2). Las diferencias son de 0,2 ms como mucho (≈ 2 %), muy por debajo del δ de CPU (1,05 ms), y **parte de estas ejecuciones no se hizo sin carga**: las semillas 33–39 de C0 y 10–20 de C2 tienen `loadavg` de 1,5 a 12 (el máximo, 12,2, en la semilla 38 de C0). La conclusión es que la estrategia no cambia la CPU de forma relevante; los p de las comparaciones por pares no se deben leer como un orden entre estrategias.

### Casos no vistos (§10.2)
Informe completo, con la traza de cada paso: `resultats/i5_no_vistos/informe.md` (se regenera con `executar_casos.py --no-vistos`). Resumen de las decisiones:

| Caso | Qué pasa | Decisiones del sistema |
|---|---|---|
| 01, martes difícil | Calor en s1 con temporeros debajo; s2 con el suelo seco; precio alto; a las 10:15 se prevé una ráfaga de 55 km/h en s3 | s1 mantiene por R1 mientras hay personas y pasa a sombra cuando se van; s2 sombra; s3 producción y, con la ráfaga, `posicio-seguretat` |
| 02, noche del operador | Datos ausentes, antiguos y fallados en s1 y s3 | s1 `diagnosticar` con impasse `dades-insuficients` (R5) durante tres ciclos; s3 un `diagnosticar` aislado; luego todo mantiene |
| 03, ola de calor | s3 en zona gris durante 30 min | Dos `tie` en s3 (prioridad de objetivos y mínima intervención); después mantiene sin impasse |
| 04, pérdida de comunicación con viento | El panel de s2 deja de informar mientras sube el viento | Dos `diagnosticar` con `dades-insuficients` (R5; el segundo con R2), `posicio-seguretat` con R2, y vuelta a producción cuando se recupera |
| 05, actuador encallado | El actuador de s1 se queda a 20° durante 40 min | s1 alterna `orientar-ombra` y `diagnosticar` (R3) cada ciclo, sin escalado |
| 06, tormenta con maquinaria | Viento crítico con maquinaria en s3 | s1 y s2 `posicio-seguretat` (R2); s3 `constraint-failure` (R1 frente al `require` de R2) y escalado a una persona durante tres ciclos |

**Valoración del equipo (pendiente):**

| Caso | Paso | Discrepancia observada | Requisito o testimonio | Qué se haría |
|---|---|---|---|---|
| | | | | |

### Estado al cierre
- 0 anomalías en la verificación, 364 tests y 82/82 casos. Las únicas reglas no disparadas son las de la reserva de escalado.
- El núcleo no cambió en I5. Las variantes A3s y B0 están en `clips/variants/`, el único sitio con salience.

## Incidencias abiertas
- **Fuga `ENVRNMNT8` (§13):** CLIPS deja unos 128 bytes por cada hecho con multislot que Python leyó y una regla retractó después. Son unos 0,8 MB por ejecución de 7 días. Aparece al final de la salida, no afecta a ningún resultado y, por decisión del equipo, no se filtra.
- **`escalat` sigue siendo inalcanzable** con el conocimiento actual. Es una reserva de terminación probada con una variante de configuración (`tests/test_escalado.py`).
- **Transferencia estructuralmente 0:** solo s3 puede empatar con el TTL actual. La generalización solo se prueba con una variante (`tests/test_chunk_fidelidad.py`).
- **Empates de tres inalcanzables:** S6 con tres o más no dominados, en presencia de un chunk, solo se prueba con SELECCIO aislada (`tests/test_seleccio_chunk.py`).
- **CPU por ciclo:** cerrada para el aprendizaje y B0 (`loadavg` ≤ 1,13 en 12 CPU). En A1 en bucle cerrado, hasta 17 de las 60 ejecuciones por estrategia (30 con C0 y 30 con C2) se midieron con carga (`loadavg` hasta 12,2). Las diferencias entre estrategias son de 0,2 ms como mucho, irrelevantes frente a δ, pero si se quiere un orden fiable entre estrategias hay que repetir esas ejecuciones sin carga (borrar sus directorios del caché y relanzar `experiments.py i5 --etapas a1`).
- **Zona gris cuantificada (C0, 30 semillas):** 2145 `tie` en los 53 días de calor (≈ 40 por día), 67 en los 116 templados y 0 en los 41 nublados. Es la dispersión que impide confirmar H1.
- **`diagnosticar` repetido (C0, 30 semillas):** 1141 rachas por sector; la más larga dura 90 min; 171 duran 30 min o más (1950 ciclos), 151 por `incertesa-dades` y 20 por `fallada-actuador`. Solo hay 8 escalados, todos en la semilla 27. El caso no visto 05 muestra la misma pauta con un actuador encallado: `orientar-ombra` y `diagnosticar` alternados sin escalado. Si el equipo quiere un escalado tras k `diagnosticar` seguidos, es un cambio de especificación posterior a la congelación.
- **Modelos del simulador heurísticos:** la lechuga (umbral de 26 °C, del TTL) tiene unas 4 h de estrés también los días templados, lo que es plausible para lechuga en verano. Los parámetros meteorológicos son sintéticos y no están calibrados con datos reales.

## Siguiente paso: informe y diagramas (§12)
- El equipo valora los casos no vistos y rellena la tabla de discrepancias de I5.
- Informe y diagramas (§12) a partir de esta sección y de `resultats/i5/`.
- Decisiones pendientes del equipo, todas posteriores a la congelación: repetir sin carga las ejecuciones de A1 afectadas; un posible escalado tras k `diagnosticar`.
