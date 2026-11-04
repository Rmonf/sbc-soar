# Sistema agrovoltaico inspirado en SOAR (CLIPS + Python)

Práctica de Sistemes Basats en Coneixement (GIA, UPC).

Una instalación agrovoltaica tiene tres sectores con cultivo y paneles solares orientables. Cada 5 minutos, un sistema de reglas en **CLIPS** decide cómo orientar los paneles de cada sector: protegerlos del viento, dar sombra al cultivo o producir energía. El sistema razona como **SOAR**: propone operadores, los compara con preferencias, delibera cuando no sabe elegir y **aprende de esa deliberación** (chunking) para no tener que repetirla. Lo que aprende se refuerza con el uso y se olvida si deja de usarse.

El código es deliberadamente pequeño: cada regla hace una sola cosa y lleva un comentario que dice qué parte de SOAR implementa.

- **CLIPS decide.** Toda la interpretación, la propuesta, la evaluación, la selección, la deliberación y el aprendizaje son reglas de CLIPS.
- **Python no decide.** Lee la ontología, simula el entorno, introduce las observaciones y muestra los resultados.

---

## 1. Cómo se corresponde con SOAR

| SOAR | En este sistema |
|---|---|
| Memoria de trabajo | Hechos de CLIPS (`deftemplate`), con el vocabulario de la ontología `ontologia/agrovoltaica-soar.ttl` |
| Ciclo de decisión | 11 fases, una por módulo de CLIPS; MAIN las encadena con `focus` |
| Elaboración | ELABORACIO: lecturas y previsión de viento → niveles (`baix` < `mitja` < `alt` < `critic`) → diagnósticos (riesgo, estrés, oportunidad) |
| Operadores | PROPOSTA: un `operador-candidato` por acción aplicable |
| Preferencias | AVALUACIO: `reject` (restricciones duras R1–R5) y `better` (comparación de beneficios) |
| Procedimiento de decisión | SELECCIO: si queda un único candidato no dominado, se elige; si no, se produce un impasse |
| Impasse y subestado | `tie` (empate) y `dades-insuficients` (faltan datos). DELIBERACIO abre un subestado, decide y devuelve una preferencia |
| Chunking | APRENENTATGE convierte cada empate resuelto en un `chunk`. La próxima vez, SELECCIO aplica el chunk y **no hay impasse** |
| Refuerzo y olvido | Activación base de Soar, A = ln Σ Δt⁻ᵈ (d = 0,5, umbral −2, tiempo en ciclos): cada uso confirmado refuerza el chunk; sin uso, se olvida |
| Memoria episódica | `episodio`: una decisión por sector y ciclo, guardada una hora. La consultan R3, R4, la deliberación y la valoración (sombra reciente) |
| Entrada y salida | Python introduce observaciones y lee la `orden-actuador` |

Diferencias con Soar: los chunks son hechos aplicados por una regla genérica, no producciones nuevas; las condiciones del chunk salen de un análisis fijo, no del *backtracing*; los subestados tienen un solo nivel. Se explican en el informe.

---

## 2. El ciclo de decisión

```
espera ──(llega un ciclo)──► percepcio ► monitoratge ► elaboracio ► proposta ► avaluacio ► seleccio
                                                                                             │  ▲
                                                                              impasse abierto ▼  │ resuelto
                                                                                         deliberacio
        seleccio ► aplicacio ► explicacio ► aprenentatge ► neteja ► espera
```

| Fase | Qué hace |
|---|---|
| PERCEPCIO | Marca los datos que faltan o están fallados (`incertesa-dades`) |
| MONITORATGE | Comprueba si la orden anterior se cumplió; si no, diagnostica un fallo del actuador |
| ELABORACIO | Pasa las lecturas y la previsión de viento a niveles con los umbrales de la ontología y crea diagnósticos |
| PROPOSTA | Propone las acciones aplicables: `orientar-produccio`, `orientar-ombra`, `posicio-seguretat`, `mantenir-posicio` o `diagnosticar` |
| AVALUACIO | Prohíbe lo peligroso (R1–R5) y compara los demás candidatos |
| SELECCIO | Elige, aplica un chunk o declara un impasse |
| DELIBERACIO | Resuelve el impasse en un subestado |
| APLICACIO | Crea la orden para los paneles |
| EXPLICACIO | Guarda el episodio y escribe la traza |
| APRENENTATGE | Crea, refuerza u olvida chunks |
| NETEJA | Limpia la memoria de trabajo para el ciclo siguiente |

**Restricciones duras** (siempre ganan a cualquier objetivo productivo):

| | Si… | …se prohíbe |
|---|---|---|
| R1 | hay personas bajo los paneles | cualquier movimiento |
| R2 | el viento es crítico, o se prevé que lo sea en 30 minutos | orientar a producción o a sombra |
| R3 | el actuador ha fallado (en este ciclo o en la última hora) | cualquier movimiento |
| R4 | ya se ha movido el máximo de veces en la última hora | cualquier movimiento salvo ir a defensa |
| R5 | no se sabe dónde está el panel | cualquier movimiento |

**Preferencias:** gana la acción con mayor beneficio en el criterio más prioritario (mecánico, después cultivo, después energía) cuando la diferencia es clara (nivel `alt` o más). Si los dos beneficios son solo `mitja`, la diferencia no es clara (**zona gris**) y el sistema no sabe elegir: es un **empate**. Si el panel ya está casi en el ángulo de una acción (menos de 5°), esa acción no se propone y "quedarse quieto" hereda su beneficio. Además, tras orientar a sombra, quedarse quieto conserva ese beneficio durante una hora aunque el estrés ya no se observe, porque desaparece precisamente gracias a la sombra (histéresis con la memoria episódica). Así el sistema no oscila entre posiciones. El coste de movimiento no se calcula aparte: lo cubren el umbral `moviment` en la propuesta, la restricción R4 y la histéresis (`preferir-util`) en la evaluación.

---

## 3. Cómo aprende

1. **Delibera.** En la zona gris (por ejemplo, estrés del cultivo `mitja` frente a oportunidad de energía `mitja`), SELECCIO declara un `tie`. DELIBERACIO lo resuelve en un subestado: gana la acción que sirve al objetivo más prioritario (el cultivo antes que la energía).
2. **Compila.** APRENENTATGE guarda la resolución como un `chunk`: "con esta pareja de acciones y estos beneficios, prefiere esta".
3. **Reutiliza.** Al ciclo siguiente, la misma situación ya no produce impasse: SELECCIO aplica el chunk directamente. Pasa de la deliberación a la reacción, que es la idea central del chunking de Soar.
4. **Refuerza.** Cada vez que una decisión tomada con el chunk se confirma en el ciclo siguiente (el panel llegó donde se ordenó), el chunk gana una referencia.
5. **Olvida.** Si un chunk no se usa, su activación baja. Por debajo de −2 se borra; un chunk usado una sola vez desaparece a las ~4,6 h. Lo olvidado se vuelve a aprender si la situación se repite.

**Lo que demuestra el experimento de aprendizaje:** con el aprendizaje activado, los empates (deliberaciones) bajan mucho respecto al sistema sin aprendizaje, y **las decisiones son exactamente las mismas**. El sistema aprende a decidir más rápido sin decidir peor.

En la traza se ve cada paso:
```
Aprenentatge (t=665): compilat chunk-mantenir-posicio-mitja-orientar-produccio-mitja ...
Decisio: mantenir-posicio (chunk-..., apres de prioritat-objectius)   Criteri: proteccio-cultiu
Aprenentatge (t=670): reforcat chunk-... per l'us de t=665
Aprenentatge (t=1765): oblidat chunk-..., activacio=-2.001 < -2.0
```

---

## 4. Instalación

Requisitos: **Python** (la versión de `.python-version`) y **uv** (recomendado) o pip. Funciona en Linux, macOS y Windows 11.

Descomprime el zip de la entrega y, desde la carpeta descomprimida:

```bash
uv sync
```

Con pip:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Con pip, quita `uv run` de los comandos siguientes.

> Al final de la salida puede aparecer `[ENVRNMNT8] Environment data not fully deallocated`. Es una fuga de memoria conocida de CLIPS al cerrar un entorno desde clipspy. No es un error y no afecta a los resultados.

---

## 5. Uso

Todo se ejecuta con `python/sbc.py`:

```bash
uv run python python/sbc.py demo                 # un día simulado, con la traza de cada decisión
uv run python python/sbc.py demo --sin-aprendizaje
uv run python python/sbc.py caso casos/09_empate_y_chunk.json   # un caso, paso a paso, con su traza
uv run python python/sbc.py aprendizaje          # experimento de aprendizaje (sección 3)
uv run python python/sbc.py agenda               # experimento de la agenda de CLIPS
uv run pytest                                    # todos los casos de prueba y los tests
```

`demo` y `caso` admiten `--estrategia` (`depth`, `breadth`, `lex`, `mea`, `complexity`, `simplicity`, `random`). `demo` admite `--dias` y `--semilla`.

**Experimento de la agenda.** Comprueba que la estrategia de resolución de conflictos de CLIPS cambia el **orden** en que disparan las reglas, pero no las **decisiones**: los conflictos del dominio se resuelven con preferencias, no con el orden de la agenda. Lo compara con **B0** (`clips/b0.clp`), una versión que decide "a la antigua", por `salience`, sin preferencias ni impasses: B0 se mueve mucho más y no puede explicar por qué elige.

Los resultados se guardan en `resultats/` (no se versiona).

---

## 6. Estructura

```
ontologia/agrovoltaica-soar.ttl   Ontología: vocabulario y conocimiento estático (sectores, cultivos, umbrales, objetivos, fases)
clips/00_main.clp                 Plantillas, funciones comunes y las reglas de control del ciclo
clips/01_percepcio.clp … 11_neteja.clp   Un módulo por fase
clips/b0.clp                      Variante B0 (decisión por salience) para el experimento de la agenda
python/ontologia.py               Lee el TTL y carga el conocimiento estático en CLIPS
python/simulador.py               Entorno simulado: meteorología (con lluvia y previsión de viento), cultivo, paneles, producción y fallos
python/sistema.py                 Puente con CLIPS: carga, introduce observaciones, ejecuta un ciclo y lee resultados
python/experimentos.py            Experimentos de aprendizaje y de agenda
python/sbc.py                     Punto de entrada (demo, caso, aprendizaje, agenda)
config/simulacio.json             Parámetros de la simulación y de los experimentos
casos/                            Casos de prueba, con las entradas y la decisión esperada
tests/                            Tests de pytest
docs/ontologia-explicada.md       Qué significa cada clase y propiedad de la ontología
fuentes/                          Enunciado, testimonios y material de clase
```
