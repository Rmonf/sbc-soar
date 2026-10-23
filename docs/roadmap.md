# Roadmap 3.0: sistema agrovoltaico inspirado en SOAR (CLIPS + Python)

**Asignatura:** Sistemes Basats en Coneixement (GIA, UPC)
**Ontología:** `ontologia/agrovoltaica-soar.ttl` v3.0 (esquema + individuos del conocimiento estático)
**Motor:** CLIPS 6.4.x a través de `clipspy`
**Versión:** 3.0. Sustituye a `implementación.md` v2.2. Los cambios están en `Cambios3.0.md`.

Este documento es la especificación para empezar a escribir los ficheros CLIPS. Sigue el principio KISS: cada mecanismo existe porque lo pide el enunciado, la rúbrica, el profesor o una fuente citada.

---

## 0. Fuentes

| Fuente | Qué aporta |
|---|---|
| `Enunciado.pdf` | Requisitos, rúbrica, lliurables, anexos A (control) y B (traza) |
| Presentación de SOAR (Sangüesa, 2026) | Principios 1–11, correspondencia SOAR–CLIPS, riesgos del patrón híbrido |
| *CLIPS User's Guide*, *CLIPS Code Snippets* (Béjar), `auto.clp` | Plantillas, hechos de control, agenda y estrategias, salience, módulos |
| `testimonios.pdf` | Requisitos de los actores (§1.2) |
| Mensaje del profesor (octubre 2026) | Chunking: cómo compila y dónde guarda; gestión de memoria de Soar: refuerzo y olvido; experimentación iterativa y estadísticamente correcta; V&V con una perspectiva de la literatura |
| Batarseh y Gonzalez (2015), *Validation of knowledge-based systems: a reassessment of the field*, Artif. Intell. Rev. 43(4), 485–500 | Perspectiva de verificación y validación (§10) |
| Manual de Soar 9.6 (cap. 4 *Procedural Knowledge Learning*, cap. 5 *Reinforcement Learning*), referencia de los comandos `chunk`, `rl`, `wm` y `smem`, y el código del kernel (`SoarGroup/Soar`) | Chunking (EBC), RL, activación base y olvido (§6.1) |
| Derbinsky y Laird (2013), *Effective and efficient forgetting of learned knowledge in Soar's working and procedural memories*, Cognitive Systems Research 24, 104–113; Laird (2021), *An Analysis and Comparison of ACT-R and Soar* | Olvido por activación base en la memoria de trabajo y en la procedimental |

---

## 1. Alcance

| Bloque | Estado | Motivo |
|---|---|---|
| Ciclo SOAR por fases, 5 familias de hechos, proposta/avaluacio/seleccio/aplicacio separadas | Núcleo | Enunciado 3.6, 3.9 |
| Restricciones duras + preferencias graduadas + política de prioridades | Núcleo | Enunciado 3.4, 3.7.2 |
| Impasses `tie`, `dades-insuficients`, `constraint-failure` con deliberación en subestado | Núcleo | Enunciado 3.7.3 (mínimo dos) |
| Memoria episódica (`episodio`) usada en una restricción y en una deliberación | Núcleo | Enunciado 3.6 |
| Explicación con vista agronómica y vista energética | Núcleo | Enunciado 3.1 |
| Simulador Python heurístico en bucle cerrado | Núcleo | Enunciado 3.5; Python calcula, no decide |
| Experimento de agenda (estrategias, especificidad, salience) | Núcleo | Enunciado 3.7.2, 3.9 |
| Verificación y validación según Batarseh y Gonzalez (2015) | Núcleo | Profesor; rúbrica D |
| Experimentación iterativa con análisis estadístico | Núcleo | Profesor; rúbrica D (avaluació) |
| **Chunking con refuerzo y olvido (módulo APRENENTATGE)** | **Única extensión** | Profesor; enunciado 3.9 (extensión evaluada con hipótesis y línea base) |
| Ontología en Protégé, SHACL, generación de plantillas | Fuera de alcance | Sustituida por el chunking |
| RL numérico de Soar (valores Q con recompensa), activación de la memoria de trabajo, persistencia de chunks entre ejecuciones | Fuera de alcance | KISS; se discuten como trabajo futuro (§13) |
| COOL, PROV-O, pvlib, multiagente | Fuera de alcance | Sin puntos asociados |

### 1.1 Tipos de conocimiento (enunciado 2)

- **Declarativo:** los individuos del TTL (sectores, cultivos, seguidores, umbrales, objetivos, datos requeridos).
- **Procedural:** las reglas de elaboración, proposta, avaluació, selecció, aplicació, explicació y monitoratge (§5).
- **De control:** la tabla de fases, el hecho S0 y las reglas de MAIN (§4).
- **Aprendido:** los hechos `chunk`, conocimiento procedimental compilado a partir de la deliberación (§6).

### 1.2 Requisitos de los testimonios

| Testimonio | Requisito | Dónde se cubre |
|---|---|---|
| Agricultor | No mover con personas debajo; razón breve de cada movimiento; aprender sin experimentar con el cultivo | R1, R5; traza (§5.9); los chunks solo repiten decisiones ya deliberadas (§6.2) |
| Agrónoma | No imputar en silencio datos ausentes; evidencia y supuesto visibles | Ausente = desconocido (R5, ángulo nil); `evidencias` |
| Ingeniera energética | Restricciones activas visibles; comportamiento seguro conocido ante fallos | Vista energética, `restricciones-activas`; `posicio-seguretat` / `diagnosticar` |
| Operador | Un incidente, no veinte alarmas; cambios de comportamiento con aviso | Un diagnóstico por sector y tipo; la traza anuncia cada chunk compilado u olvidado |
| Operador, abogado | Derivación a persona trazable; registro auditable | `escalado-humano`; `episodio` |
| Supervisora | No negociar indefinidamente | Terminación garantizada (§4.2, §5.6) |

---

## 2. Ontología y convenciones

### 2.1 Contenido del TTL

- **TBox.** 28 clases: 6 raíces abstractas y 22 con plantilla. Además, 11 propiedades de objeto, 69 de datos y 21 enumeraciones.
- **ABox.** 66 individuos:
  - 3 sectores, 3 cultivos y 3 seguidores;
  - 5 objetivos y 4 datos requeridos;
  - 11 filas de la tabla de fases;
  - 35 umbrales;
  - 1 juego de parámetros de aprendizaje;
  - el estado raíz `S0`.
- **Solo esquema para los hechos dinámicos.** Observaciones, diagnósticos, candidatos, episodios y chunks no tienen individuos: los crea la ejecución.

### 2.2 De la ontología a CLIPS

- `python/ontologia.py` (con `rdflib`) hace dos cosas:
  1. **Genera** `config/base_coneixement.clp`: un `deffacts MAIN::` con un hecho por individuo del TTL. Es la única fuente de esos datos: el `.clp` no se edita a mano.
  2. **Verifica** la base de conocimiento (§10.1).
- Las variantes de un experimento (p. ej., aprendizaje desactivado) se generan con sobrescrituras explícitas (`ontologia.py --set aprendizaje-activo=FALSE`), y cada ejecución guarda la configuración usada en `resultats/`.
- Las plantillas (`deftemplate`) se escriben a mano en `clips/00_main.clp` siguiendo §2.3. La verificación compara sus slots con el TTL.

### 2.3 Convenciones (se citan como §2.3.n)

1. **Clase → `deftemplate`** en kebab-case (`OperadorCandidato` → `operador-candidato`); las siglas cuentan como una palabra (`EstadoSOAR` → `estado-soar`). Las 6 raíces no tienen plantilla.
2. **Propiedad → slot con el mismo nombre.** Una propiedad con `rdfs:domain` pertenece a la plantilla de esa clase. Las compartidas no tienen dominio y su uso se lista en §3.3.
3. **Enumeración → `allowed-symbols`.** Toda comparación simbólica usa solo esos valores.
4. **Idioma:** nombres en castellano; valores enumerados en catalán, salvo los términos de SOAR (`tie`, `constraint-failure`, `reject`, `require`, `better`), los módulos y `R1`–`R5`.
5. **Escala ordinal** `baix < mitja < alt < critic`; `deffunction nivel-num` la convierte a 0–3.
6. **Propiedades de objeto → `SYMBOL`** con el id. En los individuos, el id es el nombre local (`:s1` → `(id s1)`).
7. **Valores opcionales:** en OWL, ausencia de la propiedad; en CLIPS, `(default nil)`, con `nil` en `allowed-symbols` si el slot es enumerado. Son opcionales:
   - `estado-padre` e `impasse-asociado` (S0);
   - `operador-comparado` y `restriccion` (según el tipo de preferencia);
   - `chunk-aplicado`;
   - `sector` (predicciones globales);
   - `estrategia-resolucion` (impasse abierto);
   - `angulo-objetivo`, `angulo-ordenado` y `angulo-previo` (sin observación de panel);
   - `tipo-impasse` en `episodio`;
   - `limite-inferior` y `limite-superior` (intervalos abiertos).
8. **Tiempo:** `instante` en minutos desde el inicio; "la última hora" es `instante ≥ t − 60`. La activación de los chunks usa horas (§6.2).
9. **Números:** los reales son `xsd:decimal` en OWL (el tipo de un literal `30.0` en Turtle) y `NUMBER` en CLIPS. Los enteros son `xsd:integer` y `INTEGER`.
10. **Un diagnóstico por sector y tipo:** la regla que lo crea comprueba que no exista; si existe, añade evidencia y eleva el nivel.
11. **Multislots como conjuntos:** su orden depende del orden de disparo; las comparaciones entre ejecuciones los tratan como conjuntos.

---

## 3. Memoria de trabajo

### 3.1 Conocimiento estático (individuos del TTL)

| Plantilla | Slots | Individuos |
|---|---|---|
| `sector` | `id`, `tiene-cultivo`, `tiene-seguidor` | s1, s2, s3 |
| `cultivo` | `id`, `nombre-cultivo`, `fase-fenologica`, `sensibilidad`, `umbral-temp-estres`, `umbral-humedad-critica` | tomate (floracion, alt, 30 °C, 45 %), lechuga (desarrollo, critic, 26 °C, 55 %), viña (maduracion, mitja, 35 °C, 30 %) |
| `seguidor-solar` | `id`, `angulo-minimo`, `angulo-maximo`, `angulo-defensa-viento`, `umbral-viento-critico`, `max-movimientos-hora`, `tolerancia-angulo` | Los tres: [−60°, 60°], defensa 0°, 70 km/h, 4 mov/h, 2° |
| `objetivo-activo` | `nombre-objetivo`, `prioridad`, `tipo-restriccion` | seguretat-persones (1, dura), integritat-mecanica (2, dura), proteccio-cultiu (3, tova), produccio-energia (4, tova), estabilitat (5, tova) |
| `dato-requerido` | `variable`, `nivel` | vent (critic); radiacio, temp-cultiu, humitat-sol (alt) |
| `definicion-fase` | `fase`, `modulo`, `siguiente` | Tabla de §4.1 |
| `umbral` | `variable`, `nivel`, `limite-inferior`, `limite-superior`, `referencia` | Tabla siguiente |
| `parametros-aprendizaje` | `aprendizaje-activo`, `tasa-decaimiento`, `umbral-olvido`, `max-referencias` | TRUE, 0.5, −2.0, 10 (valores por defecto de Soar) |

**Umbrales** (intervalos `[inferior, superior)`; los valores son provisionales y su fuente se justifica en el informe, enunciado 3.3):

| Variable | Referencia | baix | mitja | alt | critic | Lectura |
|---|---|---|---|---|---|---|
| `radiacio` (W/m²) | absoluta | <200 | 200–500 | 500–800 | ≥800 | intensidad |
| `temp-cultiu` (°C) | cultiu: valor − umbral-temp-estres | <−3 | −3–0 | 0–4 | ≥4 | estrés |
| `humitat-sol` (%) | cultiu: valor − umbral-humedad-critica | ≥10 | 0–10 | −10–0 | <−10 | déficit |
| `vent`, `vent-previst` (km/h) | seguidor: valor − umbral-viento-critico | <−40 | −40– −20 | −20–0 | ≥0 | severidad mecánica |
| `pluja`, `pluja-prevista` (mm/h) | absoluta | <0.5 | 0.5–2 | 2–10 | ≥10 | intensidad |
| `preu-energia` (€/MWh) | absoluta | <50 | 50–100 | 100–180 | ≥180 | intensidad |
| `moviment` (\|Δ\|, °) | absoluta | <5 | 5–20 | ≥20 | — | coste de mover |

`temp-ambient` y `produccio` se observan (enunciado 3.3) pero no se discretizan: no intervienen en decisiones y solo alimentan métricas y explicaciones.

### 3.2 Las cinco familias de hechos dinámicos

| Familia | Plantilla | Slots | Persistencia | Escribe |
|---|---|---|---|---|
| 1 Observados | `ciclo-temporal` | `instante` | efímera | simulador |
| | `observacion-sensor` | `id`, `sector`, `variable`, `valor`, `instante`, `calidad` | efímera | simulador |
| | `observacion-panel` | `sector`, `angulo-actual`, `estado-mecanico`, `ocupacion`, `instante` | efímera | simulador |
| | `prediccion` | `sector`, `variable`, `valor`, `instante` | efímera | simulador |
| 2 Derivados | `abstraccion` | `sector`, `variable`, `nivel` | efímera | ELABORACIO |
| | `diagnostico` | `id`, `sector`, `tipo-diagnostico`, `nivel`, `evidencias` (multi) | efímera | PERCEPCIO, MONITORATGE, ELABORACIO |
| 3 Control | `estado-soar` | `id`, `estado-padre`, `fase`, `subfase`, `impasse-asociado` | S0 persistente; subestados efímeros | config (S0), MAIN, DELIBERACIO, NETEJA |
| | `impasse` | `id`, `en-estado`, `sector`, `tipo-impasse`, `operadores-en-conflicto` (multi), `resuelto`, `estrategia-resolucion` | efímera | SELECCIO, DELIBERACIO, MAIN |
| 4 Candidatos | `operador-candidato` | `id`, `en-estado`, `sector`, `accion`, `angulo-objetivo`, `estado-candidato`, `motivos` (multi) | efímera | PROPOSTA, SELECCIO, APLICACIO |
| | `valoracion` | `evalua-operador`, `beneficio-mecanico`, `beneficio-cultivo`, `beneficio-energia`, `coste-movimiento`, `desplazamiento` | efímera | AVALUACIO |
| | `preferencia` | `en-estado`, `sector`, `tipo-preferencia`, `operador-referencia`, `operador-comparado`, `criterio`, `origen`, `restriccion`, `chunk-aplicado` | efímera | AVALUACIO, SELECCIO (chunk), DELIBERACIO |
| 5 Resultados | `orden-actuador` | `id`, `sector`, `accion`, `angulo-ordenado`, `instante`, `escalado-humano` | un ciclo | APLICACIO; la retracta MONITORATGE |
| | `episodio` | `id`, `sector`, `instante`, `situacion`, `alternativas`, `descartes`, `restricciones-activas` (multi), `criterio-determinante`, `accion`, `angulo-previo`, `angulo-ordenado`, `beneficio-cultivo`, `beneficio-energia`, `perdida-cultivo`, `perdida-energia`, `tipo-impasse`, `chunk-aplicado`, `escalado-humano`, `resultado` | persistente (ventana de 60 min) | EXPLICACIO, MONITORATGE, NETEJA |
| | `chunk` | `id`, `accion-preferida`, `beneficio-preferida`, `accion-descartada`, `beneficio-descartada`, `relacion-delta`, `criterio`, `estrategia-resolucion`, `instante`, `referencias` (multi) | persistente | APRENENTATGE |

**Dato ausente = desconocido.** Un dato ausente se representa por la ausencia del hecho, nunca por un valor por defecto. Sin `observacion-panel`, el ángulo y la ocupación son desconocidos y R5 impide mover.

### 3.3 Significado de los slots

Persistencia y escritor están en §3.2; aquí van el significado y el dominio (enunciado 3.7). Las propiedades compartidas se usan en las plantillas indicadas en §3.2.

| Plantilla | Slots: significado (dominio) |
|---|---|
| `observacion-sensor` | `valor` (número, unidades de §3.1); `calidad` (`ok`, `degradat`, `fallada`) |
| `observacion-panel` | `angulo-actual` (°); `estado-mecanico` (`operatiu`, `bloquejat`, `alarma`); `ocupacion` (`lliure`, `persones`, `maquinaria`) |
| `prediccion` | `sector` (nil si es global); `variable` (`vent-previst`, `pluja-prevista`, `angle-captacio`, `angle-ombra`, `preu-energia`); `instante` al que se refiere |
| `diagnostico` | `tipo-diagnostico`; `nivel`; `evidencias` (`variable:nivel`, `observacio-panel:absent`, `ordre-incomplerta`, `moviment-no-ordenat`) |
| `estado-soar` | `id` (`S0` o generado); `estado-padre` (solo subestados); `fase`; `subfase` (`pendent`, `feta`); `impasse-asociado` (solo subestados) |
| `impasse` | `en-estado`; `tipo-impasse`; `operadores-en-conflicto` (ids); `resuelto`; `estrategia-resolucion` (§5.7) |
| `operador-candidato` | `accion`; `angulo-objetivo` (°; nil en acción sin movimiento sin panel); `estado-candidato` (`candidat`, `descartat`, `seleccionat`, `aplicat`); `motivos` |
| `valoracion` | beneficios y coste (Nivel); `desplazamiento` (Δ en °, 0 en acciones sin movimiento) |
| `preferencia` | `tipo-preferencia`; `operador-referencia`; `operador-comparado` (solo `better`); `criterio` (NombreObjetivo); `origen` (`regla`, `deliberacio`, `chunk`); `restriccion` (R1–R5, solo §5.5a); `chunk-aplicado` (solo origen `chunk`) |
| `orden-actuador` | `angulo-ordenado` (°; nil = mantener sin mover); `escalado-humano` |
| `episodio` | `situacion` (`tipo:nivel`); `alternativas`; `descartes` (`accion:criterio`); `restricciones-activas`; `criterio-determinante`; `angulo-previo` (° al decidir); beneficios y pérdidas (vistas, §5.9); `tipo-impasse` (nil si no hubo); `chunk-aplicado`; `resultado` (`pendent`, `ok`, `fallada-actuador`) |
| `chunk` | `accion-preferida`, `accion-descartada`; `beneficio-preferida`, `beneficio-descartada` (mayor beneficio de cada acción); `relacion-delta` (`menor`, `similar`); `criterio`; `estrategia-resolucion` (de la que se aprendió); `instante` (creación); `referencias` (instantes de creación y de usos confirmados) |

---

## 4. Ciclo de control

### 4.1 Secuencia y tabla de fases

```
espera ─(Python aserta ciclo-temporal)→ percepcio → monitoratge → elaboracio → proposta → avaluacio
       → seleccio ─(impasse abierto)→ deliberacio → seleccio
                  └─(sin impasses abiertos)→ aplicacio → explicacio → aprenentatge → neteja → espera
```

| `fase` | `modulo` | `siguiente` |
|---|---|---|
| `percepcio` | `PERCEPCIO` | `monitoratge` |
| `monitoratge` | `MONITORATGE` | `elaboracio` |
| `elaboracio` | `ELABORACIO` | `proposta` |
| `proposta` | `PROPOSTA` | `avaluacio` |
| `avaluacio` | `AVALUACIO` | `seleccio` |
| `seleccio` | `SELECCIO` | `aplicacio` |
| `deliberacio` | `DELIBERACIO` | `seleccio` |
| `aplicacio` | `APLICACIO` | `explicacio` |
| `explicacio` | `EXPLICACIO` | `aprenentatge` |
| `aprenentatge` | `APRENENTATGE` | `neteja` |
| `neteja` | `NETEJA` | `espera` |

`espera` no tiene fila: solo la abandona `iniciar-ciclo`.

**MONITORATGE va después de PERCEPCIO**, no al final como en la lista del enunciado 3.7.1, que pide una "seqüència justificada". Verifica la orden de t−1 con la observación de t antes de decidir, de modo que una fallada influye en la decisión del mismo ciclo (enunciado 3.8, paso 8).

**APRENENTATGE va después de EXPLICACIO:** aprende de impasses que todavía están en memoria y refuerza con los resultados que MONITORATGE acaba de verificar.

### 4.2 Mecanismo

- **Fuente de verdad:** S0 (`fase`, `subfase`), creado por `(reset)` desde la configuración generada.
- **Un módulo por fase.** Cada regla de un módulo empieza por `(estado-soar (id S0) (fase <su fase>))`, como en el anexo A del enunciado. Esto tiene dos efectos:
  - por refracción, las reglas se reevalúan en cada ciclo, porque MAIN modifica S0;
  - la agenda de un módulo no acumula activaciones de otras fases.
- **Cinco reglas en MAIN**, que localizan S0 por `(id S0)` y son mutuamente excluyentes:
  1. `iniciar-ciclo`: S0 en `espera` y existe `ciclo-temporal` → `percepcio pendent`.
  2. `ejecutar-fase`: S0 `pendent` y `definicion-fase (fase ?f) (modulo ?m)` → `feta` y `(focus ?m)`.
  3. `avanzar-fase`: S0 `feta`, `definicion-fase (siguiente ?g)` y **no hay impasses abiertos** → `?g pendent`.
  4. `abrir-deliberacio`: S0 `seleccio feta` y hay un impasse con `resuelto FALSE` → `deliberacio pendent`.
  5. `escalar-impasse`: S0 `deliberacio feta` y hay un impasse con `resuelto FALSE` → `resuelto TRUE`, estrategia `escalat`. Es la reserva cuando la deliberación no llega a un resultado único (enunciado 3.7.3: derivar a una persona).
- **Quiescencia:** cuando la agenda del módulo enfocado se vacía, el foco vuelve a MAIN.
- **Salience 0** en todo el código de producción; solo la usan las variantes del experimento de agenda (§11.3).
- **Terminación:** cada impasse se abre una vez por ciclo y siempre se cierra, por DELIBERACIO o por `escalar-impasse`.

### 4.3 Módulos

- `MAIN` define plantillas, `deffunction` y reglas de control, con `(export ?ALL)`.
- Cada módulo hace `(defmodule X (import MAIN ?ALL))` en la primera línea de su fichero.
- La estrategia de agenda se fija al cargar (`set-strategy`, desde `simulacio.json`).

---

## 5. Conocimiento por fase

**Definiciones.**
- **Δ** = \|`angulo-objetivo` − `angulo-actual`\|, guardado en `valoracion.desplazamiento`. Es 0 para las acciones sin movimiento (`mantenir-posicio`, `diagnosticar`).
- **Candidato que mueve:** el que no es una acción sin movimiento y tiene Δ > `tolerancia-angulo`, o Δ desconocido.

### 5.1 PERCEPCIO (validación de datos)

- Por sector y `dato-requerido`: si la variable falta, tiene `calidad fallada` o `instante` menor que el actual, se crea o actualiza el `diagnostico incertesa-dades` con el nivel del dato y la variable en `evidencias`.
- Sin `observacion-panel`, la incertesa es `critic` (`observacio-panel:absent`).
- `calidad degradat` crea una incertesa `baix`, solo informativa.

Son las producciones de monitoratge de datos insuficientes (enunciado 3.7, punto 5), en PERCEPCIO porque el paso 1 del ciclo es "rebre i validar observacions".

### 5.2 MONITORATGE (verificación de t−1)

Para cada `orden-actuador` con `observacion-panel` del mismo sector:
- si `angulo-ordenado` es nil, el resultado queda `pendent`;
- si \|actual − ordenado\| ≤ tolerancia, el episodio de esa orden pasa a `ok`;
- si no, pasa a `fallada-actuador`, con diagnóstico `fallada-actuador alt`. La evidencia es `ordre-incomplerta` si la orden movía y `moviment-no-ordenat` si no.

Después se retracta la orden. Sin observación de panel, el resultado queda `pendent`. Como toda decisión genera orden, cualquier movimiento no ordenado aparece como discrepancia ("canvis inesperats", enunciado 3.7).

### 5.3 ELABORACIO (abstracción → asociación → refinamiento)

**Abstracción.** Tres reglas genéricas, una por `referencia`. Calculan `delta = valor − referencia` y asertan `abstraccion` si el delta cae en el intervalo del `umbral`; `deffunction dins-interval` trata los límites nil como infinitos. No hay umbrales escritos en las reglas.

**Diagnóstico.** Se crea si la abstracción de partida es ≥ `mitja` y el nivel final tras el refinamiento sigue siendo ≥ `mitja`:

| Diagnóstico | Origen | Refinamiento |
|---|---|---|
| `estres-termic` | `temp-cultiu` | +1 nivel (máx. `critic`) si `sensibilidad` ≥ `alt` |
| `estres-hidric` | `humitat-sol` | Igual; −1 nivel si `pluja` o `pluja-prevista` ≥ `alt` |
| `risc-mecanic` | máx(`vent`, `vent-previst`) ≥ `alt` | — |
| `risc-persones` | `ocupacion` observada ≠ `lliure` | Siempre `critic` |
| `oportunitat-energetica` | `radiacio` | +1 nivel si `preu-energia` global ≥ `alt` |
| `fallada-actuador` | `estado-mecanico` ≠ `operatiu` | Siempre `alt`; si ya existe, solo añade evidencia |

### 5.4 PROPOSTA

| Operador | Se propone si | `angulo-objetivo` |
|---|---|---|
| `orientar-produccio` | hay `oportunitat-energetica` | `angle-captacio` recortado a [min, max] |
| `orientar-ombra` | hay `estres-termic` o `estres-hidric` | `angle-ombra` recortado |
| `posicio-seguretat` | `risc-mecanic` ≥ `alt`, o `incertesa-dades` ≥ `mitja` | `angulo-defensa-viento` |
| `mantenir-posicio` | ni `incertesa-dades` ≥ `mitja` ni `fallada-actuador` | `angulo-actual` |
| `diagnosticar` | `incertesa-dades` ≥ `mitja` o `fallada-actuador` | `angulo-actual`; nil sin observación de panel |

Siempre se propone exactamente una acción sin movimiento. PROPOSTA no filtra: AVALUACIO rechaza.

### 5.5 AVALUACIO

**(a) Restricciones duras** (`reject`/`require`, `origen regla`, con `criterio` y `restriccion`):

| Id | Condición | Efecto | Criterio |
|---|---|---|---|
| R1 | `risc-persones` | `reject` a todo candidato que mueva | `seguretat-persones` |
| R2 | `risc-mecanic critic` | `require posicio-seguretat`; `reject` a `orientar-produccio` y `orientar-ombra` | `integritat-mecanica` |
| R3 | `fallada-actuador` | `reject` a todo candidato que mueva | `integritat-mecanica` |
| R4 | episodios del sector en `[t−60, t)` con movimiento (\|angulo-ordenado − angulo-previo\| > tolerancia) ≥ `max-movimientos-hora` | `reject` a todo candidato que mueva, excepto `posicio-seguretat` | `integritat-mecanica` |
| R5 | no hay `observacion-panel` | `reject` a todo candidato que mueva | `seguretat-persones` |

Ninguna restricción rechaza una acción sin movimiento, así que nunca quedan todos los candidatos rechazados. R4 es el uso de la memoria episódica en una decisión (enunciado 3.6).

**(b) Valoración** de cada candidato con Δ calculable:
- `desplazamiento` = Δ; `coste-movimiento` = nivel de Δ según el umbral `moviment`.
- `beneficio-mecanico` = nivel de `risc-mecanic` si la acción es `posicio-seguretat`; `beneficio-cultivo` = mayor estrés del sector si es `orientar-ombra`; `beneficio-energia` = nivel de `oportunitat-energetica` si es `orientar-produccio`. El resto, `baix`.
- Si `coste-movimiento = baix` (< 5°), todos los beneficios son `baix`. Las acciones sin movimiento tienen, por tanto, todos los beneficios a `baix`.
- **Invariante:** cada acción solo tiene beneficio en su propio criterio, así que la acción y su mayor beneficio determinan la valoración entera (lo usa el chunk, §6.2).

**(c) Preferencias blandas** (cinco reglas genéricas):
1. **Criterios ordenados** (una regla por criterio: `integritat-mecanica` → `proteccio-cultiu` → `produccio-energia`), solo entre dos candidatos que no sean acciones sin movimiento:
   - con niveles iguales, se pasa al siguiente criterio;
   - si difieren y el mayor es ≥ `alt`, `better(mayor, menor)`;
   - si difieren y el mayor es `mitja`, no hay preferencia y no se miran más criterios (**zona gris**).
2. **Estabilidad**, entre dos candidatos cualesquiera: con los tres beneficios iguales y Δ que difieren más que la tolerancia, `better` el de menor Δ (criterio `estabilitat`).
3. **Acción útil:** un candidato que no es acción sin movimiento y tiene un beneficio ≥ `mitja` es `better` que la acción sin movimiento, con criterio el objetivo de mayor prioridad que sirve.

**Independencia del orden de disparo.** (b) y (c) no consultan los `reject`, y SELECCIO no cuenta los `better` cuyo `operador-referencia` está rechazado. Por tanto, el conjunto de preferencias que cuentan no depende del orden en que se asertaron.

**Sin ciclos.** Todo `better` de AVALUACIO respeta el orden lexicográfico estricto (mecánico, cultivo, energía, −Δ). Los `better` de DELIBERACIO y de los chunks salen de un candidato no dominado hacia otro empatado con él, así que tampoco pueden cerrar un ciclo. Por eso no hace falta el impasse `conflict`.

**Empate real:** estrés `mitja` tras el ajuste por sensibilidad (con los datos actuales, solo en s3) frente a oportunidad energética.

### 5.6 SELECCIO (procedimiento de decisión, por sector *s*)

**Definiciones:**
- *rechazado*: tiene algún `reject`;
- *dominado*: hay un `better` sobre él emitido por un candidato no rechazado;
- *no dominado*: ni rechazado ni dominado;
- **B(s)**: hay `incertesa-dades critic`, o un candidato con `require` y `reject`, o dos candidatos con `require`;
- **empate de dos** E(A, B): A y B son los únicos no dominados, ningún no rechazado tiene `require`, no hay B(s) y no hay impasse en *s*.

Todas las reglas exigen que no haya un `seleccionat` en *s* (una selección por ciclo):

| Regla | Condición | Efecto |
|---|---|---|
| S1 `dades-insuficients` | `incertesa-dades critic`; sin impasse en *s* | impasse |
| S2 `constraint-failure` | B(s) por `require`/`reject` o por dos `require`; sin `incertesa-dades critic`; sin impasse en *s* | impasse |
| S3 requerido | exactamente un candidato con `require` no rechazado; no B(s), o hay un impasse de *s* resuelto y no `escalat` | `seleccionat` |
| S4 único no dominado | ningún no rechazado con `require`; exactamente un no dominado; no B(s), o hay un impasse de *s* resuelto y no `escalat` | `seleccionat` |
| S5 aplicar chunk | E(A, B) y existe un `chunk` aplicable (§6.2) | `better(preferida, descartada)`, `origen chunk`, `chunk-aplicado`; después S4 selecciona |
| S6 `tie` | dos o más no dominados, ningún no rechazado con `require`, no B(s), sin impasse en *s*, y **no** hay chunk aplicable | impasse con `operadores-en-conflicto` |
| S7 escalado | impasse de *s* con estrategia `escalat` | se selecciona la acción sin movimiento |

- Los demás candidatos del sector pasan a `descartat`.
- S5 y S6 se excluyen por la condición "chunk aplicable". Para comprobarla, la `deffunction chunk-aplicable` consulta los hechos `chunk` con `find-fact`.
- **Siempre queda exactamente un seleccionado:**
  - la acción sin movimiento nunca se rechaza, así que hay al menos un no dominado;
  - un empate de dos con chunk pasa por S5 y luego S4;
  - sin chunk, abre un impasse;
  - tras la deliberación queda un único requerido no rechazado (S3), un único no dominado (S4) o un impasse `escalat` (S7).

### 5.7 DELIBERACIO (subestados)

- Por cada impasse abierto se crea `estado-soar (id <gensym>) (estado-padre S0) (fase deliberacio) (impasse-asociado ?i)`.
- El resultado vuelve al padre como `preferencia (origen deliberacio)`. No se crean candidatos (enunciado 3.6).
- Las estrategias son mutuamente excluyentes y solo se aplican si dan un **resultado único**. Si ninguna se aplica, MAIN cierra el impasse como `escalat` (§4.2).

| Impasse | Estrategias, en orden |
|---|---|
| `tie` | **`minima-intervencio`:** si un único empatado tiene el menor Δ (diferencia > tolerancia), es `better` que los demás (criterio `estabilitat`; la acción más reversible, enunciado 3.7.3). **`prioritat-objectius`:** si un único empatado sirve al objetivo de mayor prioridad, es `better` que los demás (criterio: ese objetivo). |
| `dades-insuficients` | **`posicio-preventiva`:** si `posicio-seguretat` no está rechazada y, o bien la requiere R2, o bien algún episodio del sector de los últimos 60 min tenía `risc-mecanic` ≥ `alt` (consulta del historial), `require posicio-seguretat` (criterio `integritat-mecanica`). Si moverla fuera peligroso, R1, R3 o R5 ya la han rechazado. **`demanar-dades`:** si no, `require diagnosticar` (criterio `integritat-mecanica`). |
| `constraint-failure` | **`restriccio-prioritaria`:** prevalecen los `reject`. Se añade `reject` a todo requerido que mueva y `require` a la acción sin movimiento, con el criterio de mayor prioridad entre los `reject` del sector (`integritat-mecanica` si no hay). Siempre se aplica. |

**Por qué no hay histéresis en el empate.** Un resultado que depende de la memoria episódica no se puede compilar de forma correcta: Soar advierte de que lo recuperado de memoria episódica produce chunks demasiado generales (manual, cap. 4). Contra la oscilación ya actúan R4, la regla de estabilidad, la mínima intervención y el propio chunk, que repite la misma decisión cuando la situación se repite. La memoria episódica sigue usándose en R4 y en `posicio-preventiva`.

### 5.8 APLICACIO

- Cada `seleccionat` genera una `orden-actuador` (`angulo-ordenado` = `angulo-objetivo`) y pasa a `aplicat`, que es la actualización del estado (enunciado 3.6).
- `escalado-humano` es TRUE si el sector tuvo un impasse `constraint-failure` o uno cerrado como `escalat`.
- Las acciones sin movimiento también generan orden. El simulador interpreta nil como "no mover" y registra la inspección que pide `diagnosticar`.

### 5.9 EXPLICACIO

Se crea el `episodio` del sector con `resultado pendent` y `angulo-previo` = `angulo-actual`. Reglas acumulativas, protegidas con `(not (member$ ...))`, rellenan:
- `situacion`, `alternativas`, `descartes` y `restricciones-activas`;
- `beneficio-cultivo` y `beneficio-energia` de la acción elegida, y `perdida-cultivo` y `perdida-energia` (mayor beneficio entre los descartados);
- `chunk-aplicado` y `criterio-determinante` (del `require`, del `better` decisivo, del chunk o de la estrategia del impasse).

Traza en el router `traza` (formato del anexo B, más las dos vistas del enunciado 3.1 y el aprendizaje):

```
Fets d'entrada: sector=s3, temp-cultiu=37.1, radiacio=720, preu=140
Diagnosi: estres-termic=mitja, oportunitat-energetica=alt
Candidats: orientar-ombra, orientar-produccio, mantenir-posicio
Decisio: orientar-ombra (chunk-4, apres de prioritat-objectius)   Criteri: proteccio-cultiu
Ordre: sector=s3, angle=-35
Vista agronomica: estres-termic=mitja; benefici cultiu=mitja; renuncia cultiu=baix
Vista energetica: benefici energia=baix; renuncia energia=alt; restriccions actives: -
Resultat observat (t+1): angle=-34.5, ok -> chunk-4 reforcat
```

### 5.10 APRENENTATGE (extensión, §6)

Solo actúa si `parametros-aprendizaje (aprendizaje-activo TRUE)`. Tiene tres grupos de reglas, que no dependen del orden de disparo:

1. **Compilar.** Por cada impasse `tie` de este ciclo con dos operadores en conflicto, resuelto con `minima-intervencio` o `prioritat-objectius`:
   - se crea `chunk` con `accion-preferida`, `accion-descartada` y el mayor beneficio de cada una (de sus valoraciones);
   - `relacion-delta` es `menor` si la preferida tiene un Δ más de una tolerancia por debajo, y `similar` en otro caso;
   - `criterio` y `estrategia-resolucion` se toman de la deliberación;
   - `instante` = t y `referencias` = (t);
   - no se crea si ya existe un chunk con las mismas cinco condiciones (detección de duplicados).
2. **Reforzar.** Por cada `episodio` con `chunk-aplicado ?c` y `resultado ok` cuyo instante sea **posterior a la referencia más reciente** de `?c`, se añade ese instante y se conservan las `max-referencias` más recientes. Los usos son cronológicos, así que esta condición evita volver a añadir referencias ya recortadas y que la regla entre en bucle.
3. **Olvidar.** Se retracta todo `chunk` cuya activación sea menor que `umbral-olvido`, siempre que no tenga un refuerzo pendiente del grupo 2 (mismo criterio):
   - activación A = ln Σⱼ (Δtⱼ)^−d, con Δtⱼ = max(t − tⱼ, 1 min) en horas;
   - la calcula `deffunction activacio`.

Cada compilación, refuerzo u olvido se imprime en la traza.

### 5.11 NETEJA

- Retracta las familias 1, 2 y 4, los impasses y los subestados.
- Retracta los `episodio` con `instante < t − 60`, que Python ya ha exportado.
- Conserva S0, el conocimiento estático, las órdenes del ciclo, los episodios recientes y los chunks.
- Todas las plantillas son de MAIN, así que ningún hecho desaparece al cambiar de foco: la limpieza ha de ser explícita.

---

## 6. Extensión: chunking con refuerzo y olvido

### 6.1 Cómo lo hace Soar

**Compilación (chunking, EBC).** Cuando un subestado produce un resultado para el estado superior, Soar construye una regla nueva:
- recorre hacia atrás las instanciaciones que llevaron al resultado (*backtracing*);
- conserva solo las condiciones sobre elementos del estado superior;
- generaliza por identidad: los identificadores pasan a variables y las constantes se mantienen;
- añade las restricciones relacionales que se usaron.

La regla se añade **de inmediato a la memoria de producciones** (la red Rete), salvo que sea un duplicado. A partir de ahí se dispara en situaciones equivalentes y evita el impasse: "deliberació → reacció".

**Variantes y ajustes** (referencia del comando `chunk`):
- ámbito del aprendizaje: `always` / `never` / `only` / `except`, con acciones `force-learn` y `dont-learn` en los subestados;
- `bottom-only`;
- límites `max-chunks` y `max-dupes`;
- `add-osk`, que incluye el conocimiento de selección de operadores;
- filtros de corrección (`allow-local-negations`, `allow-opaque`).

Soar **no aprende** si la decisión dependió de una selección probabilística o de RL. También avisa de que lo recuperado de la memoria semántica o episódica produce chunks demasiado generales. Con el aprendizaje desactivado, Soar solo construye *justificaciones* temporales.

**Refuerzo.**
- *Soar-RL* (cap. 5): las reglas RL dan preferencias numéricas cuyo valor se actualiza por diferencias temporales (Sarsa o Q-learning) con la recompensa del *reward-link*. Un chunk puede ser una regla RL.
- *Activación base* (BLA): cada uso de un elemento suma una referencia, y su activación A = ln Σ (t − tⱼ)^−d resume frecuencia y recencia. Así se "refuerza" lo que se usa.

**Olvido.**
- **Memoria procedimental:** la apoptosis (`rl --set apoptosis chunks`) elimina un chunk cuando su activación cae bajo el umbral (por defecto d = 0,5, umbral −2, historial de 10 referencias). En el kernel solo se elimina si en ese momento no está emparejado y, si es una regla RL, si su valor nunca se ha actualizado. Es decir, solo se olvida lo que se puede volver a aprender: el olvido mejora la eficiencia sin perder competencia (Derbinsky y Laird, 2013).
- **Memoria de trabajo:** la activación (`wm activation`, desactivada por defecto) puede retirar elementos recuperables de la memoria a largo plazo.
- **Memoria semántica:** no olvida; la activación solo ordena las recuperaciones.
- **Memoria episódica:** no olvida nunca.

### 6.2 Diseño en este sistema

| Aspecto | Decisión |
|---|---|
| Qué se aprende | Solo de impasses `tie` con **dos** candidatos resueltos por `minima-intervencio` o `prioritat-objectius`. Es conocimiento de selección de operadores, el caso clásico de la presentación (robot, empate, chunk). |
| Qué no se aprende | `dades-insuficients`, porque depende de la ausencia de datos (negaciones locales) y del historial (memoria episódica). `constraint-failure`, porque su resultado se deriva a una persona. Equivale a `chunk except` con `dont-learn` en esos subestados. |
| Condiciones (explicación) | El par de acciones; el mayor beneficio de cada una, que por el invariante de §5.5b determina toda su valoración y, con ella, las preferencias de AVALUACIO entre ambas (como `add-osk`); la relación de desplazamientos (`menor` o `similar`, la restricción relacional); y que formen un empate de dos (la negación "no hay otro no dominado", incluida explícitamente). |
| Generalización | Sector y operadores son variables (identidades); acciones y niveles son constantes. Un chunk aprendido en un sector sirve para otro con la misma situación. |
| Resultado | `better(preferida, descartada)`, con el criterio de la deliberación. |
| Corrección | La deliberación de un empate de dos es una función determinista exactamente de esas condiciones. Por tanto, el chunk decide lo mismo que habría decidido la deliberación: **preserva la competencia** (hipótesis H2, §11.4). |
| Dónde se guarda | Como hecho `chunk` persistente, aplicado por una regla genérica de SELECCIO (S5). Soar lo guardaría como una producción nueva. Se elige un hecho por KISS: la red Rete indexa el hecho igual que las condiciones de una regla; olvidar es un `retract`; inspeccionar y exportar es trivial; y S6 puede comprobar si hay un chunk aplicable (§5.6). No se usa `build`. |
| Cuándo | Se compila en el mismo ciclo del impasse (APRENENTATGE); está disponible desde el ciclo siguiente. |
| Refuerzo | Se añade una referencia al chunk en cada uso **confirmado** (el episodio decidido por el chunk se verifica `ok` en t+1). Es un refuerzo "quasi RL" condicionado al éxito, en lugar de la referencia por disparo de Soar. No hay valores numéricos: el RL de Soar cambiaría las decisiones y necesitaría una recompensa multiobjetivo (§13). |
| Olvido | Activación base con los parámetros de Soar (d = 0,5, umbral −2, 10 referencias) y el tiempo en horas: un chunk usado una sola vez se olvida a las e⁴ ≈ 55 h. Preserva la competencia porque el chunk se puede volver a aprender. |
| Persistencia | Durante la ejecución, como en Soar. No se guarda entre ejecuciones; Python exporta los chunks a `resultats/` para el análisis. |
| Línea base | `aprendizaje-activo FALSE`: el mismo sistema, sin APRENENTATGE efectivo. |

### 6.3 Correspondencia de variantes

| Soar | Aquí |
|---|---|
| `chunk always/never` | `aprendizaje-activo` TRUE/FALSE |
| `chunk except` + `dont-learn` | Sin aprendizaje en `dades-insuficients` y `constraint-failure` |
| `bottom-only` | No aplica: los subestados son de un solo nivel |
| Detección de duplicados, `max-dupes` | Detección por las cinco condiciones |
| `max-chunks` | No hace falta: como mucho tres chunks por ciclo (uno por sector) |
| Generalización por identidad | Sector y operadores variables; acciones y niveles constantes |
| Restricciones relacionales | `relacion-delta` |
| `add-osk` | Los beneficios del par, que fijan las preferencias de AVALUACIO entre ambos |
| `allow-local-negations` | La negación del empate de dos se incluye explícitamente |
| Sin chunk tras selección por RL o al azar | La deliberación es determinista: siempre se puede compilar |
| Recuperación de memoria episódica → chunk demasiado general | Se elimina la histéresis del empate y no se aprende de `posicio-preventiva` |
| Producción en Rete | Hecho `chunk` + regla genérica S5 |
| Apoptosis por activación base | Olvido por activación base, con los mismos parámetros por defecto |
| Referencia por disparo | Referencia por uso confirmado |
| Soar-RL, activación de la memoria de trabajo | Fuera de alcance (§13) |
| Memoria episódica sin olvido | Ventana de 60 minutos (basta para R4 y `posicio-preventiva`) |

---

## 7. Correspondencia SOAR–CLIPS

| SOAR | Implementación | Grado |
|---|---|---|
| Memoria de trabajo | 22 plantillas: 5 familias + conocimiento estático + chunks | Aproximado: hechos planos con ids, no un grafo |
| Elaboración hasta quiescencia | ELABORACIO; la agenda vacía devuelve el foco | Preservado en su función; ejecución secuencial |
| Operador | `operador-candidato`, creado solo en PROPOSTA | Preservado |
| Preferencias | `reject`, `require`, `better` | Aproximado: subconjunto |
| Procedimiento de decisión | SELECCIO S1–S7 | Preservado: una selección por sector y ciclo, o impasse |
| Impasses | `tie`, `dades-insuficients`, `constraint-failure` | Aproximado. `dades-insuficients` no existe en SOAR. `conflict` es imposible por construcción. El `no-change` de operador se aproxima con MONITORATGE + R3. La falta de candidatos no puede darse (§5.5a). |
| Subestado | `estado-soar` con `estado-padre` | Aproximado: un nivel; si no resuelve, se escala a una persona |
| Aplicación | `orden-actuador` + candidato `aplicat` | Preservado |
| Monitoratge | Datos en PERCEPCIO; efectos y movimientos no ordenados en MONITORATGE | Preservado, repartido en dos fases |
| Entrada/salida | Python aserta la familia 1; lee órdenes, episodios y chunks | Preservado |
| Memoria episódica | `episodio` en R4 y `posicio-preventiva` | Aproximado: registro de decisiones con ventana de 60 min |
| Chunking | APRENENTATGE + S5 (§6) | Aproximado: hecho + regla genérica; condiciones obtenidas de un análisis fijo en lugar de *backtracing* |
| Activación base y olvido procedimental | Activación de los chunks y olvido (§6.2) | Aproximado: referencias por uso confirmado |
| Soar-RL, memoria semántica, SVS, activación de la memoria de trabajo | — | Excluido |

---

## 8. Estructura del proyecto

```text
proyecto-sbc-agrovoltaica/
├── ontologia/agrovoltaica-soar.ttl     # TBox + individuos (única fuente del conocimiento estático)
├── config/
│   ├── base_coneixement.clp            # GENERADO por python/ontologia.py (no editar)
│   └── simulacio.json                  # Δt, días simulados, semillas, estrategia de agenda, Kc
├── clips/
│   ├── 00_main.clp                     # deftemplates, deffunctions, control (MAIN)
│   ├── 01_percepcio.clp  02_monitoratge.clp  03_elaboracio.clp  04_proposta.clp
│   ├── 05_avaluacio.clp  06_seleccio.clp     07_deliberacio.clp 08_aplicacio.clp
│   ├── 09_explicacio.clp 10_aprenentatge.clp 11_neteja.clp
│   └── variants/                       # salience del experimento de agenda (A3s, B0)
├── python/
│   ├── ontologia.py                    # genera la configuración y verifica la base de conocimiento (§10.1)
│   ├── simulador.py                    # sectores, meteorología, geometría heurística, humedad, fallos inyectables
│   ├── pont_clips.py                   # carga, aserción, ejecución, lectura, captura de traza
│   ├── executar_casos.py               # casos de prueba (§10.2)
│   └── experiments.py                  # experimentos y análisis estadístico (§11)
├── casos/caso_XX.json                  # entradas por paso, salida esperada, requisito que cubre
├── resultats/                          # trazas, episodios, chunks, métricas, configuración usada
├── requirements.txt                    # versiones fijadas (clipspy, rdflib, numpy, scipy)
└── README.md                           # instalación y ejecución desde entorno limpio
```

**Deffunctions de MAIN:**
- `nivel-num` y `recortar-angulo`;
- `dins-interval`: límites nil = infinito;
- `relacio-delta`: `menor`, `similar` o `major`;
- `activacio`: activación base de un chunk;
- `chunk-aplicable`: busca con `find-fact` el chunk que encaja con un par.

Orden de carga: `00_main` → `config/base_coneixement.clp` → `01…11`.

---

## 9. Integración Python

**Contrato.** Python solo **aserta** hechos de la familia 1 y **lee** `orden-actuador`, `episodio` y `chunk`. Nunca modifica, retracta ni decide. Se hace un único `reset()` por ejecución, que crea S0 y el conocimiento estático.

Por cada paso t:
1. El simulador calcula el estado de los sectores y las predicciones.
2. Python aserta las observaciones y las predicciones (las globales sin sector) y luego `ciclo-temporal (instante t)`, con valores numéricos como `float`.
3. Python ejecuta `env.run()` y registra el número de reglas disparadas.
4. Aplica las órdenes de instante t al simulador, que puede inyectar fallos; nil = no mover.
5. Exporta episodios, chunks vivos y métricas del ciclo a `resultats/`.

**Geometría:** el simulador calcula `angle-captacio` y `angle-ombra` (supuesto documentado: cultivo entre filas). Qué ángulo se ordena lo decide CLIPS.

---

## 10. Verificación y validación

**Perspectiva** (Batarseh y Gonzalez, 2015). Se sigue su recomendación de **unificar verificación y validación, integrarlas en el ciclo de desarrollo de forma incremental y automatizarlas** (Lee y O'Keefe; MAVERICK sobre CommonKADS). Se combinan sus dos categorías:

- **validación del conocimiento** (caja blanca, §10.1);
- **validación del sistema** (caja negra, con casos de prueba formales, §10.2).

Cada iteración (§11.1) ejecuta las dos y usa los resultados de la anterior para elegir los casos siguientes, como hace MAVERICK.

### 10.1 Verificación de la base de conocimiento (automática, `ontologia.py --verificar`)

| Comprobación | Anomalía que detecta |
|---|---|
| Sintaxis Turtle; términos declarados; tipos, dominios, rangos y propiedades funcionales de los individuos; pertenencia a las enumeraciones; disyunción de clases | Inconsistencia del vocabulario. En mundo cerrado, porque OWL en mundo abierto infiere en lugar de avisar. |
| Los umbrales de cada variable cubren toda la recta, sin huecos ni solapamientos, con niveles distintos y monótonos y una sola referencia | Incompletitud y conflicto en la discretización |
| La tabla de fases recorre todas las fases desde `percepcio` hasta `espera`; `deliberacio` vuelve a `seleccio`; un módulo por fase | Circularidad, fases inalcanzables |
| Las prioridades de los objetivos son 1…5 y cubren la enumeración; cada sector tiene un cultivo y un seguidor propios; cada dato requerido tiene umbrales | Incompletitud |
| Los slots de los `deftemplate` de `00_main.clp` coinciden con los de §3 | Discrepancia entre especificación e implementación |
| Reglas que no se disparan en ningún caso de la batería (estadísticas de `watch rules`) | Reglas muertas o inalcanzables, y reglas de más (sobreespecialización, SEEK) |

El propio verificador se prueba **por mutación** (Vermesan y Hogberg, citado en el artículo): se introducen errores conocidos en una copia del TTL y se comprueba que los detecta (ya hecho para esta versión; ver `Cambios3.0.md`).

### 10.2 Validación del sistema (casos de prueba formales)

- **Trazabilidad:** cada caso indica el requisito que cubre (enunciado 3.2–3.10, testimonios §1.2), como recomiendan KRFOCL y el artículo.
- **Casos positivos y negativos** (VVR, Zlatareva):
  - los positivos fijan la acción esperada;
  - los negativos fijan lo que nunca debe ocurrir: mover con personas o sin observación de panel, seleccionar un candidato rechazado, `orientar-produccio` con viento crítico, más de `max-movimientos-hora` movimientos.
- **Valores límite** en cada umbral que decide, justo por debajo y en el límite (p. ej., viento 69,9 y 70,0 km/h).
- **Cobertura mínima de la batería:**
  - cada regla disparada al menos una vez;
  - cada diagnóstico, restricción R1–R5, regla S1–S7 y estrategia de deliberación;
  - los tres impasses;
  - compilación, uso, refuerzo y olvido de un chunk;
  - un caso temporal de varios pasos.
- **Conjunto razonable de casos** (ReST, Abel y Gonzalez): de los criterios del dominio (primero la seguridad), de los usuarios (contextos de los testimonios: el "martes difícil" del agricultor, la noche del operador) y del experto. Mínimo ocho casos (enunciado 3.10).
- **Validación por un experto, al estilo del test de Turing:** al menos dos casos no usados durante el desarrollo. Dos miembros del equipo, que hacen de agrónomo y de ingeniero energético, escriben de antemano la acción esperada y su justificación desde su vista. Se mide el acuerdo entre sistema y "experto" por vista (medida de acuerdo, SHIVA) y se analizan las discrepancias.
- **Regresión:** toda la batería se ejecuta tras cada cambio (`executar_casos.py`, salida pass/fail).

---

## 11. Experimentación

### 11.1 Desarrollo iterativo (el profesor: "experimentar no es fa al final")

Cada iteración termina con:
1. verificación (§10.1);
2. regresión de los casos (§10.2);
3. experimento piloto (§11.2, 10 semillas);
4. análisis;
5. decisión de qué revisar.

| Iteración | Funcionalidad | Experimento al cerrarla |
|---|---|---|
| I0 | Ontología, generador y verificador | Prueba por mutación del verificador |
| I1 | Prototipo vertical, un sector: mantenir frente a posicio-seguretat (enunciado, semana 2) | Agenda A1 con dos estrategias |
| I2 | Las 11 fases, tres sectores, impasses | Agenda A1–A2; batería de casos inicial |
| I3 | Simulador en bucle cerrado | Pilotos de las métricas de dominio; análisis de potencia (§11.2) |
| I4 | APRENENTATGE | Piloto del aprendizaje (§11.4); ajuste del umbral de olvido |
| I5 | Congelación | Experimentos completos A1–A3 y aprendizaje; casos no vistos; informe |

### 11.2 Diseño estadístico

- **Unidad experimental:** una **ejecución** (*run*) de D días simulados con una semilla. Las decisiones de una misma ejecución no son independientes: analizarlas como muestras independientes sería pseudorreplicación.
- **Diseño pareado:** todas las configuraciones se ejecutan con las mismas semillas (números aleatorios comunes), y se comparan las diferencias por semilla.
- **Tamaño de muestra:**
  - un piloto de 10 semillas estima la desviación típica de las diferencias, σ_d;
  - n = ((z₁₋α/₂ + z₁₋β) · σ_d / δ)², con α = 0,05, potencia 0,8 y δ el efecto mínimo relevante (fijado de antemano para cada métrica);
  - mínimo 30 semillas.
- **Pruebas:**
  - *dos configuraciones, métrica numérica:* Wilcoxon de rangos con signo pareado (no se supone normalidad), tamaño del efecto (correlación biserial de rangos) e intervalo de confianza del 95 % de la mediana de las diferencias por *bootstrap*;
  - *más de dos configuraciones* (estrategias de agenda): Friedman y, si es significativo, comparaciones por pares de Wilcoxon;
  - *proporciones* (fidelidad, violaciones): intervalo de Clopper–Pearson; con cero sucesos en n ejecuciones, la cota superior al 95 % es ≈ 3/n (regla del tres);
  - *varias métricas o pares:* corrección de Holm.
- **Informe:** mediana y rango intercuartílico, efecto e intervalo de confianza, p corregida. Las hipótesis y los δ se fijan antes de ver los resultados completos.
- **Métricas:**
  - violaciones de restricciones duras (deben ser 0);
  - movimientos;
  - impasses por tipo y por cada 100 decisiones;
  - escalados;
  - reglas disparadas por ciclo (métrica principal de rendimiento, determinista);
  - tiempo de CPU por ciclo (secundaria, ruidosa);
  - chunks vivos (máximo y final);
  - energía simulada;
  - horas de estrés simulado.

### 11.3 Experimento de agenda (enunciado 3.7.2)

- **A1, estrategias:** `depth`, `breadth`, `lex`, `mea`, `complexity`, `simplicity` y `random` (con semilla).
- **A2, especificidad:** `complexity` frente a `simplicity`.
- **A3, salience (obligatorio):**
  - **A3s:** salience en los refinamientos y en R1–R5;
  - **B0:** al estilo de `auto.clp`, decisión directa por objetivo con salience igual a la prioridad.
- **Hipótesis:**
  - A1, A2 y A3s cambian el orden de disparo pero no las órdenes ni los episodios, comparados como conjuntos y sin ids (§2.3.11), con el aprendizaje desactivado y activado;
  - B0 pierde la detección de empates y la trazabilidad, y cambia decisiones en los conflictos.
- **Análisis:**
  - la invariancia se comprueba exactamente en las N semillas, informando del número de discrepancias y de la cota de Clopper–Pearson;
  - B0 frente al núcleo se compara con Wilcoxon pareado en las métricas de §11.2.

### 11.4 Experimento de la extensión: aprendizaje

| | |
|---|---|
| Configuraciones | **C0:** línea base, sin aprendizaje. **C1:** chunking sin olvido (umbral de olvido muy bajo). **C2:** chunking con olvido (valores por defecto). Las tres con las mismas semillas. |
| H1, rendimiento | C1 y C2 reducen los impasses `tie` por cada 100 decisiones y las reglas disparadas por ciclo frente a C0 (Wilcoxon unilateral). |
| H2, competencia | C1 y C2 toman las mismas decisiones que C0 en todos los pasos (fidelidad del 100 %, informada como proporción de ejecuciones idénticas con Clopper–Pearson). Las métricas de dominio no cambian. |
| H3, olvido | C2 mantiene menos chunks vivos que C1, a cambio de un aumento de impasses (reaprendizaje) menor que δ. |
| Sensibilidad | Barrido del umbral de olvido (−1, −2, −3) con d = 0,5, para elegir el valor en la iteración I4. |
| Transferencia | Proporción de usos de chunks en un sector distinto del que los aprendió. |

---

## 12. Diagramas e informe

- **Informe** (enunciado 3.10): identificación, conceptualización, formalización, implementación y prueba.
  - **Fuentes** (capítulo 8): una ficha por fuente, incluidos los umbrales, `testimonios.pdf`, Batarseh y Gonzalez (2015) y la documentación de Soar.
  - **Uso de IA** (capítulo 10): declaración con las herramientas, la finalidad, las partes y la revisión.
- **Entregables** (enunciado 3.10) y dónde se generan:

  | Entregable | Origen |
  |---|---|
  | Informe en PDF | Estructura de esta sección |
  | Diagrama de arquitectura y esquema completo de la memoria de trabajo | Diagramas 1 y 3; §3 |
  | Tabla de correspondencia SOAR–CLIPS | §7 |
  | Catálogo de operadores y reglas de proposta, aplicació y preferencia | §5.4–§5.8 |
  | Código CLIPS comentado y código del simulador | §8 |
  | Esquema de módulos, fases y transiciones | §4; diagrama 2 |
  | Experimento de agenda | §11.3 |
  | Fichero de configuración | `ontologia/agrovoltaica-soar.ttl`, `config/simulacio.json` |
  | Casos de prueba | Mínimo 8, en `casos/` (§10.2) |
  | Instalación desde entorno limpio | `README.md`, `requirements.txt` |

- **Diagramas:**
  1. arquitectura (figura 3.1 del enunciado, con APRENENTATGE);
  2. módulos, fases y transiciones (§4.1);
  3. esquema de la memoria de trabajo (§3.2);
  4. ciclo de vida de un chunk: compilar → aplicar → reforzar → olvidar.

---

## 13. Limitaciones y trabajo futuro

- **RL numérico** (Soar-RL, valores Q con recompensa) no implementado. Cambiaría las decisiones en la zona gris y exigiría una recompensa que combine cultivo y energía. Es una pregunta para la segunda parte del curso: ¿cuál es esa recompensa y quién la decide?
- **Condiciones de los chunks** obtenidas de un análisis fijo de las dos estrategias aprendibles, no de un *backtracing* general. Solo se aprende de empates de dos candidatos.
- **Chunks sin persistencia** entre ejecuciones. Episodios con ventana de 60 minutos (la memoria episódica de Soar no olvida). No hay activación de la memoria de trabajo.
- **Sin indicadores acumulados** de estrés ni confianza de las predicciones, que piden la agrónoma y la ingeniera. Sin predicción de temperatura ni de radiación.
- **Sin modo manual:** `escalado-humano` marca la derivación, pero la respuesta de la persona no se modela.
- **Objetivos siempre activos;** fase fenológica constante; subestados de un nivel.
- **Datos:** umbrales provisionales; datos sintéticos etiquetados como tales (capítulo 8).

---

## 14. A verificar al empezar el código (iteración I1)

- Que el foco vuelve a MAIN al vaciarse la agenda de un módulo (`watch focus`).
- Que CLIPS rechaza una plantilla cuyo `default` viola sus `allowed-symbols`; por eso `nil` va dentro de `allowed-symbols`.
- Que `find-fact` funciona dentro de un `test` en SELECCIO y que se reevalúa en cada ciclo gracias al patrón de fase.
- La captura de `printout` y `watch rules` con un router de clipspy, y el número de reglas disparadas que devuelve `run()`.
- Que se usa un `Environment` nuevo por ejecución.
