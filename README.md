# Sistema agrovoltaico inspirado en SOAR (CLIPS + Python)

Práctica de Sistemes Basats en Coneixement (GIA, UPC). Es un sistema basado en reglas en **CLIPS** que, cada pocos minutos, decide cómo orientar los paneles solares de una instalación agrovoltaica de tres sectores. Tiene en cuenta la seguridad mecánica, el estrés del cultivo y la producción de energía. Su organización está inspirada en la arquitectura cognitiva **SOAR**: un ciclo de once fases, operadores candidatos, preferencias, impasses con deliberación, memoria episódica y aprendizaje por chunking con refuerzo y olvido. El conocimiento estático sale de una ontología OWL (`ontologia/agrovoltaica-soar.ttl`). Python (clipspy) simula el entorno, conecta los componentes y ejecuta los experimentos, pero **no decide**. El diseño completo está en `docs/roadmap.md` y el registro de iteraciones y resultados, en `docs/iteraciones.md`.

## Requisitos

- **Python 3.14** (`.python-version`).
- **[uv](https://docs.astral.sh/uv/)** (recomendado): instala la versión de Python y las dependencias fijadas en `uv.lock`.
- Como alternativa, **pip** con `requirements.txt`. Este fichero se genera a partir de `uv.lock` y tiene las mismas versiones; no se edita a mano.

Las dependencias son clipspy (que incluye CLIPS 6.4), rdflib, numpy, scipy y pytest.

## Instalación desde un clon limpio

Con uv:

```bash
git clone <url-del-repositorio> sbc
cd sbc
uv sync
```

Con pip:

```bash
git clone <url-del-repositorio> sbc
cd sbc
python3.14 -m venv .venv
source .venv/bin/activate          # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

En el resto del documento, los comandos se escriben con `uv run`. Con pip, activa el entorno y quita `uv run` (por ejemplo, `python python/ontologia.py`).

> **Aviso sobre `[ENVRNMNT8]`.** Al final de la salida de casi todos los comandos aparecen, una o varias veces, las líneas `[ENVRNMNT8] Environment data not fully deallocated.`, `[ENVRNMNT8] MemoryAmount = …` y `[ENVRNMNT8] MemoryCalls = …`. Es una fuga de memoria conocida de CLIPS al liberar un `Environment` desde clipspy (roadmap §13). No es un error y no afecta a los resultados ni al código de salida.

## Base de conocimiento

`config/base_coneixement.clp` contiene el conocimiento estático (umbrales, cultivos, seguidores, sectores…) y se genera a partir del TTL. Ya viene generado en el repositorio. Si cambia el TTL o alguna plantilla de `clips/00_main.clp`, hay que regenerarlo. **No se edita a mano.**

```bash
uv run python python/ontologia.py              # regenera config/base_coneixement.clp
uv run python python/ontologia.py --verificar  # verificación de la base de conocimiento (§10.1)
```

La verificación comprueba que el TTL, las plantillas y las reglas son coherentes entre sí. Termina con `0 anomalías, 1 avisos`. El aviso indica que las reglas no disparadas las informa la batería de casos.

Las variantes de configuración de los experimentos se generan en otro fichero; el original no se toca:

```bash
uv run python python/ontologia.py --set aprendizaje-activo=FALSE --salida resultats/C0.clp
```

## Casos de prueba

La batería (`casos/caso_*.json`, §10.2) ejecuta cada caso en un `Environment` nuevo. Por cada paso compara las órdenes, los episodios, la traza y los chunks con lo esperado. Al final escribe `PASS`/`FAIL` por caso, el total y las reglas que no se ha disparado en ningún caso:

```bash
uv run python python/executar_casos.py
uv run python python/executar_casos.py --estrategia breadth   # con otra estrategia de agenda
```

Los mismos casos y los tests de los componentes se ejecutan también con pytest:

```bash
uv run pytest
```

### Un caso suelto con su traza

`--caso` ejecuta solo los casos cuyo id empieza por el texto indicado. Por cada paso escribe la orden de cada sector y la traza de la explicación: hechos de entrada, diagnóstico, candidatos, descartes, impasse, decisión y criterio, la orden, y las vistas agronómica y energética. Termina con el resultado `PASS`/`FAIL`:

```bash
uv run python python/executar_casos.py --caso caso_08    # ejemplo del anexo B del enunciado
```

### Casos no vistos

Los escenarios de `casos_no_vistos/` salen de los testimonios y no tienen salida esperada, así que no forman parte de la regresión. Este comando escribe la decisión y la traza de cada paso en `resultats/i5_no_vistos/informe.md`:

```bash
uv run python python/executar_casos.py --no-vistos
```

## Ejecución en bucle cerrado

El simulador heurístico (`python/simulador.py`, configurado en `config/simulacio.json`) genera la meteorología, el estado del cultivo y de los paneles, y los fallos. En cada paso de 5 minutos, CLIPS decide y el simulador aplica las órdenes:

```bash
uv run python python/bucle.py --semilla 0 --dias 1
```

Opciones: `--semilla N`, `--dias D` (7 por defecto), `--estrategia <estrategia de agenda>` y `--salida <carpeta>` (`resultats/prova` por defecto). La ejecución queda en `resultats/prova/semilla_0/`:

| Fichero | Contenido |
|---|---|
| `traza.txt` | traza de explicación de cada decisión |
| `ordenes.jsonl`, `episodios.jsonl`, `chunks.jsonl` | lo que Python lee de CLIPS en cada paso |
| `ciclos.jsonl`, `estado.jsonl` | reglas disparadas y CPU de cada ciclo; estado simulado (meteorología, cultivo y paneles) |
| `metricas.json` | métricas de la ejecución (energía, estrés, movimientos, escalados…) |
| `configuracion.json` | configuración, semilla y `loadavg` |

Un día simulado (288 pasos) tarda unos 3 segundos.

## Experimentos

Todos los experimentos están en `python/experiments.py`. Cada uno escribe `resumen.txt` (legible) y `resultados.json` (completo) en su carpeta de `resultats/`. Las ejecuciones en bucle cerrado guardan además una subcarpeta por semilla o por configuración. Si no se dice otra cosa, se usan las semillas 0–9 de `config/simulacio.json` y 7 días por semilla. Los que admiten `--semillas`, `--dias` y `--salida` permiten cambiarlo.

| Comando | Qué hace | Resultados |
|---|---|---|
| `uv run python python/experiments.py a1` | Agenda A1 (§11.3) sobre la batería: las 7 estrategias de CLIPS dan las mismas decisiones | `resultats/i2_a1/` |
| `uv run python python/experiments.py a2` | Agenda A2: especificidad, `complexity` frente a `simplicity` | `resultats/i2_a2/` |
| `uv run python python/experiments.py piloto` | Piloto del núcleo en bucle cerrado y análisis de potencia (§11.2) | `resultats/i3_piloto/` |
| `uv run python python/experiments.py a1-bucle` | A1 en bucle cerrado sobre las semillas | `resultats/i3_a1/` |
| `uv run python python/experiments.py aprenentatge` | Aprendizaje (§11.4): C0 sin aprendizaje, C1 sin olvido, C2 por defecto y barrido del umbral de olvido | `resultats/i4_aprenentatge/` |
| `uv run python python/experiments.py a3s --base C0` | A3s sobre la batería: `depth` frente a `depth` con salience (`clips/variants/a3s.clp`), sin aprendizaje (`C0`) o con él (`C2`, por defecto) | `resultats/i5_a3s/` |
| `uv run python python/experiments.py i5` | Experimentos completos de I5 (semillas 10–39 × 7 días): etapas `aprenentatge`, `b0` (línea base por salience), `a3` y `a1` | `resultats/i5/` |

Notas:

- `a1` y `a2` tardan poco (la batería se ejecuta una vez por estrategia). Los experimentos en bucle cerrado tardan del orden de 3 s por semilla, día y configuración: `piloto` tarda unos minutos y `aprenentatge` y `a1-bucle`, unas decenas de minutos. `i5` tarda horas.
- `aprenentatge --reutilizar C0 C1` lee de la carpeta de salida las ejecuciones ya guardadas de esas configuraciones en lugar de repetirlas.
- `i5` mide la CPU por ciclo, así que hay que lanzarlo **sin otras cargas en la máquina** (cada ejecución guarda su `loadavg`). Se puede reanudar: cada ejecución se guarda en `resultats/i5/ejecuciones/` y, al relanzarlo con el mismo código, se lee de ahí. `--etapas aprenentatge b0` elige las etapas que se ejecutan. `--procesos N` llena el caché en N procesos; después, C0 y C2 con `depth` se ejecutan en serie, cada una cuando el `loadavg` de 1 minuto baja de 1, y son las únicas con una CPU válida.
- El código devuelve 0 si se cumplen los invariantes del experimento (sin violaciones de decisión, sin discrepancias de agenda donde no debe haberlas) y 1 si no.

## Dónde quedan los resultados

Todo lo que se genera va a `resultats/`, que git ignora y que se puede borrar y regenerar con los comandos anteriores. Los resultados de referencia de cada iteración, con sus tablas e interpretación, están en `docs/iteraciones.md`.

## Estructura del repositorio

| Ruta | Contenido |
|---|---|
| `clips/` | Módulos CLIPS: `00_main.clp` (plantillas y control) y `01_percepcio.clp` … `11_neteja.clp` (una fase cada uno) |
| `clips/variants/` | Variantes del experimento de agenda: `a3s.clp` y `b0.clp` |
| `config/` | `base_coneixement.clp` (generado) y `simulacio.json` (simulador, semillas, fallos, δ) |
| `ontologia/` | Ontología OWL, la fuente del conocimiento estático |
| `python/` | Generador y verificador (`ontologia.py`), puente con CLIPS (`pont_clips.py`), simulador, bucle, métricas, batería y experimentos |
| `casos/`, `casos_no_vistos/` | Casos de prueba con salida esperada y casos no vistos |
| `tests/` | Tests de pytest |
| `docs/` | Roadmap (especificación), registro de iteraciones y ontología explicada |
| `fuentes/` | Enunciado, testimonios y material de clase |
