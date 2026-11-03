# Plan de simplificación

## 0. Por qué y qué

El profesor ha dejado claro qué valora: que se vea que el sistema **funciona como SOAR y aprende**. El volumen de código y la documentación técnica no suman. La versión actual (unas 6.500 líneas de código, 1.700 de documentación, 84 casos, verificador, análisis de potencia, variantes…) es difícil de explicar y de mantener.

**Objetivo:** reescribir el sistema con la menor cantidad de reglas, funciones y ficheros que demuestre, de forma legible, el ciclo de SOAR, los impasses con deliberación y el chunking con refuerzo y olvido. Además, debe cumplir los mínimos obligatorios del enunciado (§3.9 y §3.10).

**Reglas de juego:**
- **`README.md` es la especificación** del sistema final: lo que dice el README es lo que el sistema debe hacer. Este plan detalla el cómo.
- **La ontología no se toca:** `ontologia/agrovoltaica-soar.ttl` queda tal cual. El sistema puede usar solo una parte de su vocabulario.
- **La versión actual se conserva en git** con la etiqueta `v-roadmap3`. Se puede consultar (`git show v-roadmap3:<ruta>`) para reutilizar ideas, pero no para copiar su complejidad.
- **La demo será en un portátil con Windows 11 recién instalado:** nada que dependa de Linux.

---

## 1. Principios de escritura

1. **Una regla, una idea.** Cada regla lleva una línea de comentario que dice qué hace y qué concepto de SOAR implementa (p. ej., `;; SOAR: preferencia reject (restricción dura R1)`).
2. **Las condiciones van en patrones,** no escondidas en funciones. Solo se permiten las deffunctions de la lista de §3.1; cualquier otra hay que justificarla en el resumen.
3. **Salience 0 en todo el sistema,** salvo en `clips/b0.clp`, que existe precisamente para mostrar la decisión por salience.
4. **Sin código defensivo ni generalidad que no se use:** nada de opciones, métricas o parámetros que no aparezcan en el README.
5. **Presupuesto orientativo** (si se pasa mucho, revisa qué sobra):

| | Antes | Objetivo |
|---|---|---|
| CLIPS (sin contar `b0.clp`) | ~2.300 líneas | ≤ 650 |
| Python | ~2.700 líneas | ≤ 500 |
| Tests | ~1.450 líneas | ≤ 150 |
| Casos | 84 + 6 | 11 |
| Documentación | ~1.750 líneas | README + `ontologia-explicada.md` |

---

## 2. Qué se conserva y qué se elimina

| Se conserva | Se elimina |
|---|---|
| `ontologia/agrovoltaica-soar.ttl` (intacto) | `docs/roadmap.md`, `docs/iteraciones.md` (quedan en la etiqueta `v-roadmap3`) |
| `docs/ontologia-explicada.md` | Verificador de la base de conocimiento y prueba por mutación |
| `fuentes/` | `config/base_coneixement.clp` generado: el TTL se carga directamente en CLIPS |
| Las 11 fases y sus módulos (las define el TTL) | Análisis de potencia, Holm, Friedman, bootstrap, medidas de CPU, `loadavg` |
| Chunking con refuerzo y olvido (activación base de Soar, tiempo en ciclos) | Variante A3s, reanudación por hash, ejecución en paralelo |
| R1–R5 y la memoria episódica (R3, R4, deliberación) | Impasse `constraint-failure`, preferencia `require`, `escalar-impasse` y S7 (inalcanzables o innecesarios) |
| Experimento de agenda con B0 (mínimo obligatorio del enunciado 3.7.2) | Refinamientos de ELABORACIO (sensibilidad, lluvia, precio) y predicciones de viento y lluvia |
| Simulador, en versión pequeña | Lecturas antiguas y degradadas, falsos positivos, casos no vistos como carpeta aparte |
| `pyproject.toml`, `uv.lock`, `.gitignore` | `requirements.txt` actual (se regenera al final) |

**Por qué se quitan los refinamientos:** sin ellos, la zona gris aparece en los tres sectores, no solo en s3. Así se ven más empates y el chunk aprendido en un sector se reutiliza en otro: el aprendizaje se ve mejor.

---

## 3. Diseño

Nombres de plantillas y slots según la ontología: clase en kebab-case → `deftemplate`; propiedad → slot con el mismo nombre; enumeración → `allowed-symbols`. Las plantillas del **conocimiento estático** (`sector`, `cultivo`, `seguidor-solar`, `objetivo-activo`, `dato-requerido`, `definicion-fase`, `umbral`, `parametros-aprendizaje`) llevan todos sus slots, porque se cargan desde el TTL. Las **dinámicas** llevan solo los slots que se usan.

Escala de niveles: `baix` < `mitja` < `alt` < `critic`.

### 3.1 MAIN (`00_main.clp`)

- **Plantillas** (22, todas las clases con plantilla del TTL).
- **`defglobal`:** `?*ventana-episodica*` = 60 (minutos) y `?*minutos-por-ciclo*` = 5.
- **Deffunctions permitidas:**
  - `nivel-num` y `nivel-max` (escala);
  - `dins-interval` (umbral con límites nil = infinito);
  - `accion-sin-movimiento`;
  - `no-dominados` (candidatos del sector no rechazados ni dominados);
  - `chunk-aplicable`;
  - `activacio` (activación base de Soar);
  - `fallada-reciente` (R3), `movimientos-recientes` (R4) y `riesgo-reciente` (deliberación): memoria episódica;
  - `beneficio-heredado` (§3.6);
  - las de formato de la traza, en EXPLICACIO.
- **Control** (4 reglas):
  - `iniciar-ciclo`: S0 en `espera` + `ciclo-temporal` → `percepcio pendent`;
  - `ejecutar-fase`: S0 `pendent` → `feta` + `(focus <módulo de la tabla de fases>)`;
  - `avanzar-fase`: S0 `feta` y ningún impasse abierto → siguiente fase de la tabla;
  - `abrir-deliberacio`: S0 en `seleccio feta` con un impasse abierto → `deliberacio`.

  No hay `escalar-impasse`: toda deliberación termina siempre (§3.8).

Cada regla de un módulo empieza con el patrón `(estado-soar (id S0) (fase <su fase>))`.

### 3.2 PERCEPCIO
- `dato-ausente`: por cada sector y `dato-requerido`, si no hay observación o tiene `calidad fallada` → `diagnostico incertesa-dades` con el nivel del dato y la evidencia `variable:absent`. Un diagnóstico por variable: no hace falta fusionarlos.
- `panel-ausente`: sector sin `observacion-panel` → `incertesa-dades critic` (`observacio-panel:absent`).

Las lecturas `degradat` se tratan como `ok`.

### 3.3 MONITORATGE
Por cada `orden-actuador` del ciclo anterior (3 reglas que retractan la orden ellas mismas):
- `orden-cumplida`: hay panel y |actual − ordenado| ≤ tolerancia → episodio `ok`;
- `orden-fallada`: hay panel y la diferencia es mayor → episodio `fallada-actuador` + `diagnostico fallada-actuador alt`;
- `orden-sin-verificar`: orden con ángulo nil o sin panel → el episodio queda `pendent`.

### 3.4 ELABORACIO
- **Abstracción,** una regla por referencia (`absoluta`, `cultiu`, `seguidor`), solo con observaciones `calidad` ≠ `fallada`: el nivel es el del `umbral` en cuyo intervalo cae el valor (o la diferencia con el umbral del cultivo o del seguidor).
- **Diagnósticos,** una regla cada uno, sin refinamientos:

| Diagnóstico | Origen |
|---|---|
| `risc-mecanic` | nivel de `vent` ≥ `alt` |
| `estres-termic` | nivel de `temp-cultiu` ≥ `mitja` |
| `estres-hidric` | nivel de `humitat-sol` ≥ `mitja` |
| `oportunitat-energetica` | nivel de `radiacio` ≥ `mitja` |
| `risc-persones` | `ocupacion` ≠ `lliure` (`critic`) |
| `fallada-actuador` | `estado-mecanico` ≠ `operatiu` (`alt`) |

Las únicas predicciones que se usan son los ángulos objetivo (`angle-captacio` y `angle-ombra`), que da el simulador.

### 3.5 PROPOSTA
Un candidato por acción y sector, con id `<sector>-<acción>`:
- `posicio-seguretat`: `risc-mecanic` ≥ `alt` o `incertesa-dades critic`. Ángulo: `angulo-defensa-viento`.
- `orientar-ombra`: algún estrés. Ángulo: `angle-ombra` recortado a los límites del seguidor.
- `orientar-produccio`: `oportunitat-energetica`. Ángulo: `angle-captacio` recortado.
- `diagnosticar`: `incertesa-dades` ≥ `mitja` o `fallada-actuador`. Ángulo: el actual, o nil sin panel.
- `mantenir-posicio`: si no se propone `diagnosticar`. Ángulo: el actual.

**"Ya está ahí":** una acción que se mueve no se propone si su ángulo objetivo está a menos del límite `baix` del umbral `moviment` (5°) del ángulo actual. En su lugar, la acción sin movimiento hereda su beneficio (§3.6). Esto evita el vaivén entre posiciones.

### 3.6 AVALUACIO
- **Restricciones duras** (`reject`, con `restriccion` y `criterio`): las cinco de la tabla del README. R3 usa `fallada-reciente`: el diagnóstico del ciclo, o un episodio de la última hora con `resultado fallada-actuador` cuya orden pedía mover. R4 usa `movimientos-recientes`. R1, R3 y R5 rechazan los candidatos que mueven.
- **Valoración** (una regla, sin modificaciones posteriores):
  - cada acción que se mueve tiene beneficio solo en su criterio: mecánico (`posicio-seguretat`: nivel de `risc-mecanic`, o `baix`), cultivo (`orientar-ombra`: el mayor estrés) o energía (`orientar-produccio`: `oportunitat-energetica`);
  - la acción sin movimiento tiene los beneficios **heredados** (`beneficio-heredado`) de las acciones que no se propusieron por "ya está ahí";
  - Δ = |objetivo − actual|; sin panel, no hay valoración.
- **Preferencias `better`:**
  - `preferir-mecanico`, `preferir-cultivo` y `preferir-energia`: orden lexicográfico. En el primer criterio en que dos candidatos difieren, si el mayor es ≥ `alt`, es `better`. Si el mayor es `mitja`, no hay preferencia y no se miran más criterios (**zona gris**).
  - `preferir-util`: un candidato que se mueve con algún beneficio ≥ `mitja` es `better` que la acción sin movimiento con todos los beneficios a `baix`.

### 3.7 SELECCIO
"No dominado" = ni rechazado ni con un `better` en contra emitido por un candidato no rechazado.
- `s1-dades-insuficients`: `incertesa-dades critic` y sin impasse en el sector → `impasse dades-insuficients`.
- `s4-elegir`: un único no dominado, y (sin `incertesa critic` o con un impasse del sector resuelto) → `seleccionat`.
- `s5-aplicar-chunk`: exactamente dos no dominados, sin `incertesa critic` ni impasse, y un chunk aplicable → `better` con `origen chunk` y `chunk-aplicado`. Después decide `s4-elegir`.
- `s6-tie`: dos o más no dominados, sin `incertesa critic` ni impasse, y no es el caso de S5 → `impasse tie` con los no dominados.
- `descartar-resto`.

### 3.8 DELIBERACIO
- `crear-subestado`: un `estado-soar` hijo de S0 por impasse abierto (el subestado de SOAR).
- `tie-prioridad`: gana el candidato que sirve al **objetivo de mayor prioridad** (`objetivo-activo`). La acción sin movimiento sirve a lo que hereda. → `better` (`origen deliberacio`) sobre los demás; el impasse se cierra con `prioritat-objectius`.
  - **Siempre hay un ganador único:** cada objetivo lo sirve una sola acción, y la acción sin movimiento solo hereda objetivos de acciones que no se propusieron. Si aun así no lo hubiera, gana la acción sin movimiento.
- `datos-preventiva`: impasse `dades-insuficients`, `posicio-seguretat` no rechazada y `riesgo-reciente` (episodio de la última hora con `risc-mecanic` ≥ `alt`) → `better` para `posicio-seguretat` (`posicio-preventiva`).
- `datos-pedir`: si no → `better` para `diagnosticar` (`demanar-dades`).

### 3.9 APLICACIO
- `aplicar`: el seleccionado crea la `orden-actuador` (ángulo = el del candidato) y pasa a `aplicat`.
- `escalado-humano` es `TRUE` si el sector tuvo un impasse `dades-insuficients` (la decisión pide inspección).

### 3.10 EXPLICACIO
- **Una sola regla** crea el episodio y escribe la traza.
  - Calcula en el RHS, con funciones del módulo: `situacion`, `alternativas`, `descartes` (acción:criterio), `restricciones-activas`, `criterio-determinante`, `tipo-impasse`, `chunk-aplicado`, ángulos, `beneficio-cultivo`, `beneficio-energia` y `resultado pendent`.
  - El `criterio-determinante` es el del `better` sobre el elegido; se prefiere uno de deliberación o de chunk antes que uno de regla, y es nil si había un solo candidato.
  - Todo lo que lee es estable en esta fase.
- **Traza** al estilo del anexo B del enunciado, con las dos vistas (agronómica y energética), la línea del chunk si lo hay, y nada más.

### 3.11 APRENENTATGE
Solo con `parametros-aprendizaje (aprendizaje-activo TRUE)`.
- `compilar`: un impasse `tie` resuelto, con dos operadores en conflicto y sin un chunk idéntico → `chunk`.
  - Condiciones: `accion-preferida`, `beneficio-preferida`, `accion-descartada` y `beneficio-descartada` (el mayor beneficio de cada uno). `relacion-delta` no se usa: con la deliberación por prioridad, el resultado solo depende del par de acciones y de lo que hereda la acción sin movimiento, y eso lo fija el par.
  - El id se forma con las condiciones; `referencias` = (t).
  - Pon este argumento de corrección en el comentario de la regla.
- `reforzar`: episodio con `chunk-aplicado`, `resultado ok` e instante posterior a la última referencia → se añade y se conservan las `max-referencias` más recientes.
- `olvidar`: `activacio` < `umbral-olvido` y ningún refuerzo pendiente → `retract`.
- Cada una escribe su línea `Aprenentatge (t=…)` en la traza.

### 3.12 NETEJA
- **Una regla** que retracta con `do-for-all-facts`: observaciones, predicciones, abstracciones, diagnósticos, candidatos, valoraciones, preferencias, impasses, subestados, episodios fuera de la ventana y el `ciclo-temporal`.
- Conserva S0, el conocimiento estático, las órdenes del ciclo, los episodios recientes y los chunks.

### 3.13 B0 (`clips/b0.clp`)
- Sustituye a `05_avaluacio`, `06_seleccio`, `07_deliberacio` y `10_aprenentatge`. Define los mismos módulos para que la tabla de fases siga funcionando.
- R1–R5 iguales que en el núcleo, con la salience más alta.
- Después, una regla por objetivo con salience = 6 − prioridad, que elige el candidato no rechazado de su acción. Un hecho de decisión por sector bloquea el resto.
- Sin valoraciones, preferencias `better`, impasses ni chunks.
- Unas 50 líneas.

---

## 4. Python

| Fichero | Contenido | Líneas |
|---|---|---|
| `ontologia.py` | Lee el TTL con rdflib y aserta un hecho por individuo (clase → plantilla, propiedad → slot). Admite sobrescribir parámetros de aprendizaje (`aprendizaje-activo` para el experimento). | ~60 |
| `simulador.py` | Con la librería estándar `random`, una semilla. Tipo de día (templado, calor, nublado), sol (ángulo de captación y de sombra), radiación, temperatura del cultivo con efecto de la sombra, humedad del suelo, viento con tormentas, ocupación en horario de trabajo, y fallos: sensor fallado, panel sin comunicación, actuador encallado. El panel ejecuta la orden con un error pequeño. **El ruido de la observación del ángulo debe ser mucho menor que la tolerancia** (≤ 0,5°), para que MONITORATGE no dé falsos fallos. Parámetros en `config/simulacio.json`. | ~120 |
| `sistema.py` | Clase `Sistema(estrategia, aprendizaje, variante)`: un `Environment` nuevo, carga de `clips/` (o de B0), `reset`, carga del TTL, router para la traza y para `watch rules`. Su `paso(t, observaciones)` aserta, ejecuta y devuelve órdenes, episodios, chunks, traza y reglas disparadas. **Python solo aserta observaciones y lee.** | ~80 |
| `experimentos.py` | `aprendizaje` y `agenda` (§6). | ~130 |
| `sbc.py` | CLI: `demo`, `caso`, `aprendizaje`, `agenda`. Los casos dan valores tranquilos por defecto a los sectores que no mencionan. | ~70 |

Dependencias: `clipspy`, `rdflib`, `scipy` y `matplotlib`; `pytest` como dependencia de desarrollo. Se quita `numpy` (lo instala scipy).

---

## 5. Casos (`casos/`) y tests (`tests/`)

**Casos.** Cada caso es un JSON (`casos/NN_nombre.json`, p. ej. `09_empate_y_chunk.json`) con `descripcion`, `requisito` (testimonio o apartado del enunciado) y `pasos` (instante, observaciones por sector y lo esperado por sector: acción y, si toca, impasse y chunk).

| # | Caso | Qué demuestra |
|---|---|---|
| 01 | Calma | Ciclo completo; `mantenir-posicio` |
| 02 | Calor alto | Elaboración → `orientar-ombra` por preferencia |
| 03 | Sol con radiación alta | `orientar-produccio` |
| 04 | Viento crítico | R2; `posicio-seguretat` (anexo B del enunciado) |
| 05 | Personas bajo el panel con viento alto | R1 gana: no se mueve |
| 06 | Panel sin comunicación | R5 + `dades-insuficients` → `demanar-dades` |
| 07 | Sensor de viento fallado tras una racha | `dades-insuficients` → `posicio-preventiva` (memoria episódica) |
| 08 | Actuador encallado, 3 pasos | Fallo detectado y R3 con memoria: no vuelve a intentarlo cada ciclo |
| 09 | Zona gris, 2 pasos | t=0: `tie` → deliberación → chunk compilado; t=5: misma situación → chunk aplicado, sin impasse, misma decisión |
| 10 | Olvido | Chunk sin uso durante horas → olvidado; vuelve a aprenderse |
| 11 | Ya en sombra | Hereda el beneficio: no sale a producir (no hay vaivén) |

**Tests** (≤ 150 líneas):
- `test_casos.py`: ejecuta todos los casos;
- `test_aprendizaje.py`: un día simulado con y sin aprendizaje da **las mismas órdenes**, y con aprendizaje hay menos `tie`;
- `test_b0.py`: B0 carga y respeta R1.

---

## 6. Experimentos (`experimentos.py`)

**`aprendizaje`** (el principal):
- **Configuración:** 10 semillas × 7 días, con y sin aprendizaje, mismas semillas.
- **Por día:** empates `tie`, usos de chunk, chunks vivos y chunks olvidados.
- **Al final:**
  - tabla con media y desviación;
  - **decisiones idénticas con y sin aprendizaje** (debe ser 10/10);
  - una prueba de Wilcoxon pareada de los empates por semilla;
  - una figura con la curva de aprendizaje (`resultats/aprendizaje.png`): empates por día con y sin aprendizaje, y chunks vivos.

**`agenda`:**
- **Estrategias:** las 7 sobre los 11 casos y sobre 3 semillas × 1 día, comparadas con `depth`. Las órdenes deben ser idénticas; se informa de en cuántos ciclos cambia la secuencia de disparo y del uso de salience (ninguno en el núcleo). La especificidad la cubren `complexity` y `simplicity`.
- **B0 frente al núcleo** (3 semillas × 1 día): porcentaje de decisiones distintas, movimientos por sector y día, y porcentaje de episodios con criterio.

Los resultados se escriben como texto en la consola y en `resultats/`. Si un resultado contradice lo que dice el README (por ejemplo, decisiones distintas con aprendizaje), **para y explícalo**: no ajustes el sistema para que salga.

---

## 7. Pasos

Cada paso termina con `uv run pytest` en verde y un commit en castellano.

| Paso | Contenido | Comprobación |
|---|---|---|
| P0 | `git tag v-roadmap3` en el `main` actual y push de la etiqueta; rama `simplificacion`. Sustituye `README.md` y `CLAUDE.md` por los nuevos y añade este `PLAN.md`. Borra lo de la columna derecha de §2, junto con `clips/`, `python/`, `tests/`, `casos/` y `casos_no_vistos/`. | Quedan TTL, `fuentes/`, `docs/ontologia-explicada.md`, `config/` y la configuración del proyecto |
| P1 | `00_main.clp` (plantillas y control), `ontologia.py` y `sistema.py`, y los módulos PERCEPCIO, MONITORATGE, ELABORACIO, PROPOSTA, AVALUACIO, SELECCIO (S4 y descartar), APLICACIO, EXPLICACIO y NETEJA. DELIBERACIO y APRENENTATGE, vacíos. | Casos 01–05, 08 y 11 |
| P2 | S1, S6 y DELIBERACIO | Casos 06, 07 y el paso t=0 del 09 |
| P3 | APRENENTATGE y S5 | Casos 09 y 10; `test_aprendizaje.py` sobre los casos |
| P4 | `simulador.py` y `sbc.py demo` | Un día de demo sin errores y con la traza legible; `test_aprendizaje.py` sobre un día simulado |
| P5 | `b0.clp` y `experimentos.py` | Los dos experimentos terminan; resumen con sus cifras |
| P6 | Cierre: `uv export --no-hashes --no-dev -o requirements.txt`; recuento de líneas frente a §1; borrar `PLAN.md`; comprobar que la rueda de clipspy existe para Windows con la versión de Python fijada | Si no existe, fija la versión de Python más alta que tenga rueda para `win_amd64` y avisa |

Comprobación de Windows desde Linux:
```bash
uvx pip download clipspy --platform win_amd64 --python-version <X.Y> --only-binary=:all: -d /tmp/rueda
```

**Al final**, el resumen para el equipo debe incluir: las líneas por fichero, los 11 casos, las cifras de los dos experimentos y cualquier punto en que el sistema se haya apartado del README (con el motivo).

---

## 8. Qué no hacer

- No modificar el TTL.
- No añadir nada que no esté en el README o en este plan: verificadores, métricas extra, opciones de línea de órdenes, variantes, estadística adicional, documentación nueva.
- No usar salience fuera de `b0.clp`.
- No usar nada específico de Linux (`os.getloadavg`, descriptores de fichero, `ctypes`).
- No ajustar reglas para que un experimento salga como se espera: si algo no cuadra, parar y explicarlo.
