# CLAUDE.md

Práctica de Sistemes Basats en Coneixement (GIA, UPC). Es un sistema basado en reglas en **CLIPS** que decide cada pocos minutos cómo orientar los paneles solares de una instalación agrovoltaica de tres sectores. Su organización está inspirada en la arquitectura cognitiva **SOAR**: fases, operadores candidatos, preferencias, impasses con deliberación, memoria episódica y aprendizaje por chunking. Python (clipspy) simula el entorno y conecta los componentes, pero **no decide**.

## Mapa del repositorio

| Ruta | Contenido |
|---|---|
| `docs/roadmap.md` | **Especificación del diseño.** Léela antes de escribir código. Se cita como §n. |
| `docs/iteraciones.md` | **Registro de iteraciones:** qué se hizo en cada una, decisiones que cambiaron el roadmap (commit y motivo), resultados de los experimentos, incidencias abiertas y siguiente paso. Léelo para retomar el trabajo. |
| `docs/ontologia-explicada.md` | Resumen en lenguaje llano de cada clase y propiedad del TTL. |
| `ontologia/agrovoltaica-soar.ttl` | Ontología OWL: esquema de la memoria de trabajo e individuos del conocimiento estático. |
| `fuentes/enunciado.md` | Enunciado oficial (en catalán). El roadmap lo cita como "enunciado 3.x". |
| `fuentes/testimonios.md` | Testimonios de los usuarios (en inglés); de ahí salen requisitos (roadmap §1.2). |
| `fuentes/*.pdf` | Material de clase (ver "Fuentes" al final). |
| `casos_no_vistos/` | Casos no vistos (§10.2): escenarios de los testimonios sin salida esperada; no entran en la regresión ni en `pytest`. |
| `clips/variants/` | Variantes del experimento de agenda (§11.3): `a3s.clp` (salience en los refinamientos y en R1–R5) y `b0.clp` (línea base por salience). Es el único sitio con salience. |

Estado tras I5: las 11 fases con los tres sectores, R1–R5, S1–S7 y DELIBERACIO, conectadas en bucle cerrado con el simulador heurístico (`python/simulador.py`, `bucle.py`, `metricas.py`; parámetros, tipos de día, semillas, fallos y δ en `config/simulacio.json`; meteorología sintética de final de primavera, §9). APRENENTATGE compila, refuerza y olvida chunks (§5.10, §6), S5 los aplica, y `experiments.py aprenentatge` compara C0, C1 y C2 (§11.4). I5 (congelación) está cerrada: experimentos completos en `experiments.py i5`, variantes A3s y B0 en `clips/variants/` y casos no vistos; resultados en `docs/iteraciones.md`. Las variantes de configuración (C0 sin aprendizaje, otros umbrales) se generan con `ontologia.generar_variante` o `--set … --salida`, nunca a mano. Cada fichero dice en su cabecera qué hace. `casos/` tiene la batería: cada caso parte de `casos/_base_tranquil.json` (los tres sectores con datos completos que mantienen la posición) e indica solo lo que cambia por sector; `null` quita una observación. Si un cambio aprobado de la especificación altera el resultado esperado de un caso, el caso lleva una clave `cambio` que lo explica. `resultats/` (ignorado por git) se regenera con los experimentos. Una excepción a §8: las dependencias van en `pyproject.toml` y `uv.lock`, no en `requirements.txt`.

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
- **Ningún umbral numérico va escrito en una regla.** La prohibición se refiere a los umbrales del dominio: se leen de los hechos `umbral` y de los slots de `cultivo` y `seguidor-solar`. Las constantes de convención del diseño (p. ej., la ventana episódica de 60 min, §2.3.8) van en un `defglobal` de `00_main.clp` que cita su sección del roadmap, nunca como literal en una regla.
- **Separación SOAR estricta:** proponer, evaluar, seleccionar y aplicar son fases y módulos distintos (§5).
- **KISS.** No añadas funcionalidad que no esté en el alcance (§1). Si algo te parece necesario y no lo está, pregúntalo antes.

## Entorno y comandos

El entorno lo gestiona **uv**. Ejecuta siempre con `uv run`. Añade dependencias con `uv add <paquete>` (o `uv add --dev` para las de desarrollo). No uses `pip`.

```bash
uv sync                                         # instala el entorno desde uv.lock
uv run python python/ontologia.py               # genera config/base_coneixement.clp a partir del TTL
uv run python python/ontologia.py --verificar   # verificación de la base de conocimiento (§10.1)
uv run python python/ontologia.py --set aprendizaje-activo=FALSE --salida <ruta>   # variante de experimento (§2.2)
uv run pytest                                   # casos de prueba y regresión (§10.2)
uv run python python/executar_casos.py          # batería de casos con pass/fail y reglas no disparadas (§10.1, §10.2)
uv run python python/executar_casos.py --no-vistos   # casos no vistos: decisión y traza por paso en resultats/i5_no_vistos/informe.md (§10.2)
uv run python python/experiments.py a1          # experimento de agenda A1, 7 estrategias (§11.3), salida en resultats/i2_a1/
uv run python python/experiments.py a2          # experimento A2, complexity frente a simplicity (§11.3)
uv run python python/bucle.py --semilla 0 --dias 1   # una ejecución en bucle cerrado con el simulador (§9)
uv run python python/experiments.py piloto      # piloto de 10 semillas × 7 días y potencia (§11.2), resultats/i3_piloto/
uv run python python/experiments.py a1-bucle    # A1 en bucle cerrado sobre las semillas (§11.3), resultats/i3_a1/ (--salida para otra carpeta)
uv run python python/experiments.py aprenentatge   # piloto del aprendizaje C0/C1/C2 y barrido del umbral (§11.4), resultats/i4_aprenentatge/; --reutilizar C0 C1 lee esas ejecuciones guardadas
uv run python python/experiments.py a3s --base C0  # A3s sobre la batería (clips/variants/a3s.clp), sin (C0) o con (C2) aprendizaje (§11.3)
uv run python python/experiments.py i5          # experimentos completos de I5 (semillas 10–39 × 7 días), en serie y reanudables: aprenentatge, b0, a3, a1 (--etapas para elegir); resultats/i5/
```

`experiments.py i5` mide la CPU: lánzalo sin otras cargas en la máquina (cada ejecución guarda su `loadavg`). Con `--procesos N` llena antes el caché en N procesos para las métricas de decisión; solo C0 y C2 con `depth` se ejecutan después en serie, cada una cuando el `loadavg` de 1 min baja de 1, y son las únicas con CPU válida (los resúmenes lo avisan; la serie se ejecuta en un proceso nuevo). Si se interrumpe, al relanzarlo lee del caché (`resultats/i5/ejecuciones/`) las ejecuciones ya hechas con el mismo código.

Al final de la salida de estos comandos puede aparecer `[ENVRNMNT8] Environment data not fully deallocated`. Es una fuga conocida de CLIPS, documentada en roadmap §13, y no indica ningún error: no se filtra.

Si cambia algún comando, actualiza esta sección. El generador lee las plantillas de `clips/00_main.clp`: al añadir o cambiar una plantilla, regenera y verifica.

## Forma de trabajar

- **Una iteración cada vez** (§11.1: I0 → I5). No empieces la siguiente sin que la anterior esté cerrada.
- **I1 empieza por las comprobaciones de §14** (foco, `allowed-symbols` con `nil`, `find-fact`, captura de traza, un `Environment` por ejecución). Son supuestos del diseño que todavía no se han probado.
- **Comprueba lo que escribes.** Un fichero `.clp` no está terminado hasta que se ha cargado y ejecutado sin errores en clipspy y hay al menos un caso que lo ejercita. Usa `watch rules`, `watch facts` y `watch focus` para depurar.
- **Cierre de cada iteración:**
  1. verificación (§10.1);
  2. regresión de casos (§10.2);
  3. experimento piloto (§11.2);
  4. actualizar `docs/iteraciones.md`.
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
