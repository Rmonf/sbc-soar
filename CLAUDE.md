# CLAUDE.md

Práctica de Sistemes Basats en Coneixement (GIA, UPC). Es un sistema basado en reglas en **CLIPS** que decide cada pocos minutos cómo orientar los paneles solares de una instalación agrovoltaica de tres sectores. Su organización está inspirada en la arquitectura cognitiva **SOAR**: fases, operadores candidatos, preferencias, impasses con deliberación, memoria episódica y aprendizaje por chunking. Python (clipspy) simula el entorno y conecta los componentes, pero **no decide**.

## Mapa del repositorio

| Ruta | Contenido |
|---|---|
| `docs/roadmap.md` | **Especificación del diseño.** Léela antes de escribir código. Se cita como §n. |
| `docs/ontologia-explicada.md` | Resumen en lenguaje llano de cada clase y propiedad del TTL. |
| `ontologia/agrovoltaica-soar.ttl` | Ontología OWL: esquema de la memoria de trabajo e individuos del conocimiento estático. |
| `fuentes/enunciado.md` | Enunciado oficial (en catalán). El roadmap lo cita como "enunciado 3.x". |
| `fuentes/testimonios.md` | Testimonios de los usuarios (en inglés); de ahí salen requisitos (roadmap §1.2). |
| `fuentes/*.pdf` | Material de clase (ver "Fuentes" al final). |

Los directorios `clips/`, `python/`, `config/`, `casos/` y `resultats/` aún no existen. Se crean siguiendo **roadmap §8**. Una excepción a §8: las dependencias van en `pyproject.toml` y `uv.lock`, no en `requirements.txt`.

## Jerarquía de fuentes

Si dos fuentes no coinciden, manda la primera de esta lista:

1. `fuentes/enunciado.md`: requisitos obligatorios y rúbrica.
2. `docs/roadmap.md`: qué se construye y cómo.
3. `ontologia/agrovoltaica-soar.ttl`: vocabulario, plantillas, slots, valores permitidos e individuos.
4. El código.

**No modifiques el TTL ni el roadmap por iniciativa propia.** Si al implementar algo encuentras un hueco, una contradicción o algo que no se puede hacer tal como está especificado, **para y explícalo**: qué dice la especificación, qué problema hay y qué propones. Cuando el cambio esté aprobado, actualiza el TTL y el roadmap juntos, en el mismo commit.

## Reglas de diseño (no negociables)

- **Python no decide** (§9). Solo aserta hechos observados (familia 1) y lee `orden-actuador`, `episodio` y `chunk`. Nunca modifica ni retracta hechos, ni elige acciones.
- **Una sola fuente del conocimiento estático.** `config/base_coneixement.clp` lo genera `python/ontologia.py` a partir del TTL. **No se edita a mano**: si cambia el TTL, se regenera.
- **Convenciones de §2.3**, en particular:
  - nombres de clase a plantilla en kebab-case;
  - cada propiedad se convierte en un slot con el mismo nombre;
  - las enumeraciones se convierten en `allowed-symbols`;
  - los valores opcionales son `nil`, con `nil` dentro de `allowed-symbols`;
  - los valores enumerados van en catalán y los nombres en castellano;
  - los reales son `NUMBER` y los enteros `INTEGER`.
- **Control** (§4.2):
  - cada regla de un módulo empieza con el patrón de fase de S0;
  - MAIN tiene solo las cinco reglas de control;
  - todo el código de producción usa **salience 0**; la salience solo aparece en `clips/variants/`, para el experimento de agenda (§11.3).
- **Un dato ausente es desconocido.** Se representa por la ausencia del hecho, nunca por un valor por defecto.
- **Ningún umbral numérico va escrito en una regla.** Los umbrales se leen de los hechos `umbral` y de los slots de `cultivo` y `seguidor-solar`.
- **Separación SOAR estricta:** proponer, evaluar, seleccionar y aplicar son fases y módulos distintos (§5).
- **KISS.** No añadas funcionalidad que no esté en el alcance (§1). Si algo te parece necesario y no lo está, pregúntalo antes.

## Entorno y comandos

El entorno lo gestiona **uv**. Ejecuta siempre con `uv run`. Añade dependencias con `uv add <paquete>` (o `uv add --dev` para las de desarrollo). No uses `pip`.

```bash
uv sync                                         # instala el entorno desde uv.lock
uv run python python/ontologia.py               # genera config/base_coneixement.clp a partir del TTL
uv run python python/ontologia.py --verificar   # verificación de la base de conocimiento (§10.1)
uv run pytest                                   # casos de prueba y regresión (§10.2)
```

Los scripts se crean en la iteración I0. Si cambia algún comando, actualiza esta sección.

## Forma de trabajar

- **Una iteración cada vez** (§11.1: I0 → I5). No empieces la siguiente sin que la anterior esté cerrada.
- **I1 empieza por las comprobaciones de §14** (foco, `allowed-symbols` con `nil`, `find-fact`, captura de traza, un `Environment` por ejecución). Son supuestos del diseño que todavía no se han probado.
- **Comprueba lo que escribes.** Un fichero `.clp` no está terminado hasta que se ha cargado y ejecutado sin errores en clipspy y hay al menos un caso que lo ejercita. Usa `watch rules`, `watch facts` y `watch focus` para depurar.
- **Cierre de cada iteración:**
  1. verificación (§10.1);
  2. regresión de casos (§10.2);
  3. experimento piloto (§11.2);
  4. resumen final para el equipo: qué se ha hecho, resultados, decisiones tomadas e incidencias.
- **Commits pequeños**, uno por paso lógico, con mensaje en castellano.
- **Comentarios del código en castellano.** Cada regla lleva una línea que explica qué hace y la sección del roadmap que implementa.

## Fuentes (consúltalas solo cuando haga falta)

Los PDF son largos. Antes de abrirlos, busca la respuesta en el roadmap o en los ficheros markdown.

| Fichero | Para qué |
|---|---|
| `fuentes/enunciado.md` | Requisitos, rúbrica, entregables y ejemplos de los anexos A y B. |
| `fuentes/testimonios.md` | Necesidades de los usuarios (agricultor, agrónoma, ingeniera, operador…). |
| CLIPS User's Guide (`usrguide.pdf`) | Sintaxis, `deftemplate`, módulos, agenda y estrategias. |
| CLIPS Code Snippets (Béjar) | Ejemplos comentados de la asignatura (factorial, ordenación, máximo, viajante, sistema experto de averías de coches): estilo de reglas, control con hechos y eficiencia del emparejamiento. |
| Ejemplo `auto.clp` (Màrquez) | Diapositivas del sistema experto de averías de coches: entorno de CLIPS, `watch`, `run 1` y estrategias `depth`/`breadth`. |
| Presentación de clase sobre SOAR | Ciclo de decisión, impasses, subestados y chunking, tal como se explicaron en clase. |
| Batarseh y Gonzalez (2015) | Perspectiva de verificación y validación que sigue §10. |
