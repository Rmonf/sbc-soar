# La ontología agrovoltaica-SOAR, explicada

Este documento explica qué representa cada elemento del fichero `agrovoltaica-soar.ttl`. Está pensado para que cualquiera pueda entenderlo desde cero.

## 1. Contexto

**La instalación.** Una instalación **agrovoltaica** combina cultivo y producción solar en el mismo terreno. Tiene tres **sectores** (`s1`, `s2`, `s3`), y cada uno tiene un cultivo y un **seguidor solar**: una fila de paneles que gira sobre un eje.

**Por qué importa el ángulo.** El ángulo de los paneles decide un compromiso:
- orientados al sol producen más energía;
- girados pueden dar sombra al cultivo cuando hace demasiado calor o falta agua;
- con viento fuerte deben ir a una posición de seguridad.

**El sistema.** Un programa en CLIPS (un lenguaje de reglas) decide cada pocos minutos qué hacer con los paneles de cada sector. Su funcionamiento imita la arquitectura cognitiva **SOAR**:
1. percibe los datos;
2. interpreta la situación;
3. propone opciones;
4. las evalúa;
5. elige una;
6. la ejecuta;
7. explica la decisión;
8. aprende de ella.

Cuando no sabe elegir entre opciones (un **impasse**), delibera aparte. Lo que concluye ahí lo puede guardar como regla aprendida (un **chunk**) para la próxima vez.

**Qué es la ontología.** Es el vocabulario de todo lo anterior: qué tipos de cosas existen y qué datos tiene cada una.

### Términos básicos

| Término | Significado |
|---|---|
| **Clase** | Un tipo de cosa (p. ej., *Cultivo*). En CLIPS cada clase concreta se convierte en una plantilla de hechos. |
| **Individuo** | Un ejemplar concreto de una clase (p. ej., el cultivo de tomate del sector 1). |
| **Object property** | Una relación entre dos cosas (p. ej., un sector *tiene* un cultivo). |
| **Data property** | Un dato de una cosa: un número, un texto, un sí/no o un valor de una lista cerrada. |
| **Enumeración** | Lista cerrada de valores permitidos. Los valores están en catalán. |
| **Ciclo** | Una ronda completa de decisión. El tiempo se mide en minutos desde el inicio de la simulación. |
| **Nivel** | Escala cualitativa usada en todo el sistema: `baix` (bajo) < `mitja` (medio) < `alt` (alto) < `critic` (crítico). |

Las **cinco acciones** que puede tomar un sector son:
- `orientar-produccio`: orientar los paneles para producir energía;
- `orientar-ombra`: orientarlos para dar sombra al cultivo;
- `posicio-seguretat`: llevarlos a la posición de defensa contra el viento;
- `mantenir-posicio`: dejarlos como están;
- `diagnosticar`: no moverlos y pedir una inspección.

Las dos últimas son **acciones sin movimiento**.

Un dato que falta **no se inventa**: si no hay medida, el sistema lo trata como desconocido y actúa con prudencia.

---

## 2. Clases

Las 28 clases se agrupan bajo seis clases raíz. Las raíces solo sirven para clasificar y no se usan directamente.

### 2.1 Conocimiento del dominio (datos fijos de la instalación)

Se cargan al arrancar y no cambian durante la ejecución.

| Clase | Qué representa |
|---|---|
| `ConocimientoDominio` | Raíz: todo lo que es configuración fija. |
| `Sector` | Una parcela de la instalación, con su cultivo y su seguidor. |
| `Cultivo` | El cultivo de un sector: especie, fase de crecimiento, sensibilidad y umbrales a partir de los cuales sufre calor o sequía. |
| `SeguidorSolar` | Los paneles de un sector: límites de giro, posición de defensa contra el viento, viento máximo tolerado y movimientos permitidos por hora. |
| `ObjetivoActivo` | Uno de los cinco objetivos del sistema, con su prioridad (1 = la más alta) y si es obligatorio (`dura`) o deseable (`tova`). Orden de prioridad: seguridad de las personas, integridad mecánica, protección del cultivo, producción de energía y estabilidad. |
| `DatoRequerido` | Una medida que debe llegar en cada ciclo, junto con lo grave que es que falte. |
| `Umbral` | Un tramo de valores de una variable al que se asigna un nivel (p. ej., viento de 50 a 70 km/h = `alt`). Sirve para pasar de números a niveles. |
| `DefinicionFase` | Una fila de la tabla del ciclo: qué módulo ejecuta cada fase y cuál es la siguiente. |
| `ParametrosAprendizaje` | Ajustes del aprendizaje: si está activado, a qué ritmo se olvidan las reglas aprendidas y a partir de qué punto se borran. |

### 2.2 Hechos observados (lo que llega del exterior)

Los envía el simulador en cada ciclo y se borran al final del ciclo.

| Clase | Qué representa |
|---|---|
| `HechoObservado` | Raíz: datos que vienen de fuera. |
| `CicloTemporal` | La señal de que empieza un ciclo nuevo, con el instante actual. |
| `ObservacionSensor` | Una lectura numérica de un sensor (radiación, temperatura, humedad, viento, lluvia…) y su calidad. |
| `ObservacionPanel` | El estado de los paneles de un sector: ángulo actual, si funcionan bien y si hay personas o maquinaria debajo. |
| `Prediccion` | Un valor previsto o calculado por un servicio externo: viento y lluvia previstos, ángulo ideal para producir, ángulo ideal para dar sombra y precio de la energía. |

### 2.3 Hechos derivados (la interpretación de la situación)

| Clase | Qué representa |
|---|---|
| `HechoDerivado` | Raíz: conclusiones que el sistema saca de los datos. |
| `Abstraccion` | Una medida traducida a nivel (p. ej., "viento `alt` en el sector 2"). |
| `Diagnostico` | Un problema u oportunidad detectado en un sector, con su gravedad y las pruebas que lo apoyan. Los tipos son: estrés térmico, estrés hídrico, riesgo mecánico, riesgo para personas, oportunidad energética, datos insuficientes y fallo del actuador. |

### 2.4 Hechos de control (en qué punto del razonamiento está el sistema)

| Clase | Qué representa |
|---|---|
| `HechoControl` | Raíz: el estado interno del razonamiento. |
| `EstadoSOAR` | El estado del razonamiento. El principal (`S0`) indica en qué fase del ciclo está el sistema. Los secundarios se crean para deliberar sobre un impasse. |
| `Impasse` | Una situación en la que el sistema no puede elegir. Hay tres tipos: empate entre opciones (`tie`), faltan datos para decidir (`dades-insuficients`) y las restricciones se contradicen (`constraint-failure`). |

### 2.5 Candidatos (las opciones y cómo se comparan)

| Clase | Qué representa |
|---|---|
| `HechoCandidato` | Raíz: las opciones del ciclo y lo que se opina de ellas. |
| `OperadorCandidato` | Una acción propuesta para un sector, con el ángulo al que llevaría los paneles y su estado (propuesta, descartada, seleccionada o aplicada). |
| `Valoracion` | La evaluación de una opción: cuánto beneficia a la mecánica, al cultivo y a la energía, cuánto cuesta moverse y cuántos grados habría que girar. |
| `Preferencia` | Una opinión sobre una opción: prohibirla (`reject`), exigirla (`require`) o preferirla a otra (`better`). Incluye el objetivo que la justifica y quién la emitió. |

### 2.6 Resultados (lo que queda de cada decisión)

| Clase | Qué representa |
|---|---|
| `HechoResultado` | Raíz: lo que produce o recuerda el sistema. |
| `OrdenActuador` | La orden enviada a los paneles: acción, ángulo y si se avisa a una persona. Se comprueba en el ciclo siguiente. |
| `Episodio` | El registro de una decisión: situación, opciones, descartes, motivo, ángulos, lo que gana o pierde el cultivo y la energía, y si la orden se cumplió. Sirve de memoria (se guarda una hora) y de explicación. |
| `Chunk` | Una regla aprendida de un empate ya resuelto: "si vuelven a empatar estas dos acciones en las mismas condiciones, elige esta". Se refuerza cada vez que funciona y se olvida si deja de usarse. |

---

## 3. Object properties (relaciones entre cosas)

| Propiedad | Une | Significado |
|---|---|---|
| `tiene-cultivo` | `Sector` → `Cultivo` | El cultivo que crece en el sector. |
| `tiene-seguidor` | `Sector` → `SeguidorSolar` | Los paneles que hay en el sector. |
| `sector` | casi todos los hechos → `Sector` | El sector al que se refiere el dato o la decisión. Falta solo en predicciones generales, como el precio de la energía. |
| `en-estado` | `Impasse`, `OperadorCandidato`, `Preferencia` → `EstadoSOAR` | El estado de razonamiento en el que se creó. |
| `estado-padre` | `EstadoSOAR` → `EstadoSOAR` | En un estado de deliberación, el estado principal del que cuelga. |
| `impasse-asociado` | `EstadoSOAR` → `Impasse` | En un estado de deliberación, el impasse que intenta resolver. |
| `operadores-en-conflicto` | `Impasse` → `OperadorCandidato` | Las opciones entre las que no se ha podido elegir (varias). |
| `evalua-operador` | `Valoracion` → `OperadorCandidato` | La opción a la que corresponde la evaluación. |
| `operador-referencia` | `Preferencia` → `OperadorCandidato` | La opción sobre la que opina la preferencia (la prohibida, la exigida o la preferida). |
| `operador-comparado` | `Preferencia` → `OperadorCandidato` | Solo en `better`: la opción que queda por detrás. |
| `chunk-aplicado` | `Preferencia`, `Episodio` → `Chunk` | La regla aprendida que produjo la preferencia o que se usó en la decisión. |

---

## 4. Data properties (datos de cada cosa)

En la columna de valores, "nivel" es la escala `baix` < `mitja` < `alt` < `critic`. "Acción" es una de las cinco acciones de §1.

### 4.1 Datos comunes a varias clases

| Propiedad | Se usa en | Valores | Significado |
|---|---|---|---|
| `id` | la mayoría de hechos e individuos | texto | Identificador único. |
| `instante` | observaciones, predicciones, órdenes, episodios, chunks, ciclo | entero (minutos) | Cuándo ocurrió. En un chunk, cuándo se aprendió. |
| `variable` | observaciones, predicciones, abstracciones, umbrales, datos requeridos | `radiacio`, `temp-ambient`, `temp-cultiu`, `humitat-sol`, `vent`, `pluja`, `produccio`, `vent-previst`, `pluja-prevista`, `angle-captacio`, `angle-ombra`, `preu-energia`, `moviment` | Qué magnitud es: radiación, temperatura, humedad del suelo, viento, lluvia, producción, previsiones, ángulos ideales, precio o giro de los paneles. |
| `valor` | `ObservacionSensor`, `Prediccion` | número | El valor medido o previsto. |
| `nivel` | `Abstraccion`, `Diagnostico`, `Umbral`, `DatoRequerido` | nivel | Gravedad o intensidad. En un dato requerido, lo grave que es que falte. |
| `accion` | `OperadorCandidato`, `OrdenActuador`, `Episodio` | acción | La acción propuesta, ordenada o tomada. |
| `angulo-ordenado` | `OrdenActuador`, `Episodio` | número (°) | Ángulo al que se manda ir. Vacío = no mover porque no se conoce el ángulo actual. |
| `beneficio-cultivo` | `Valoracion`, `Episodio` | nivel | Cuánto ayuda la acción al cultivo. |
| `beneficio-energia` | `Valoracion`, `Episodio` | nivel | Cuánto ayuda la acción a producir energía. |
| `criterio` | `Preferencia`, `Chunk` | objetivo | El objetivo que justifica la preferencia. |
| `estrategia-resolucion` | `Impasse`, `Chunk` | `minima-intervencio`, `prioritat-objectius`, `posicio-preventiva`, `demanar-dades`, `restriccio-prioritaria`, `escalat` | Cómo se resolvió el impasse: moviéndose lo mínimo, por el objetivo más prioritario, yendo a posición de seguridad, pidiendo datos, haciendo prevalecer las prohibiciones o pasando el caso a una persona. |
| `tipo-impasse` | `Impasse`, `Episodio` | `tie`, `dades-insuficients`, `constraint-failure` | Tipo de bloqueo. En un episodio, vacío si no lo hubo. |
| `escalado-humano` | `OrdenActuador`, `Episodio` | sí/no | Si la decisión se pasa a una persona para que la revise. |
| `fase` | `EstadoSOAR`, `DefinicionFase` | las 12 fases del ciclo (`percepcio` … `neteja`, más `espera`) | Fase actual del razonamiento o fase a la que se refiere la fila. |

### 4.2 Sector, cultivo y seguidor

| Propiedad | Clase | Valores | Significado |
|---|---|---|---|
| `nombre-cultivo` | `Cultivo` | texto | Especie (tomate, lechuga, viña). |
| `fase-fenologica` | `Cultivo` | texto | Etapa de crecimiento (floración, desarrollo, maduración). |
| `sensibilidad` | `Cultivo` | nivel | Lo delicado que es el cultivo. Agrava los diagnósticos de estrés. |
| `umbral-temp-estres` | `Cultivo` | número (°C) | Temperatura a partir de la cual el cultivo sufre calor. |
| `umbral-humedad-critica` | `Cultivo` | número (%) | Humedad del suelo por debajo de la cual el cultivo sufre sequía. |
| `angulo-minimo`, `angulo-maximo` | `SeguidorSolar` | número (°) | Límites de giro de los paneles. |
| `angulo-defensa-viento` | `SeguidorSolar` | número (°) | Posición segura con viento fuerte. |
| `umbral-viento-critico` | `SeguidorSolar` | número (km/h) | Viento a partir del cual peligra la estructura. |
| `max-movimientos-hora` | `SeguidorSolar` | entero | Movimientos permitidos por hora para limitar el desgaste. |
| `tolerancia-angulo` | `SeguidorSolar` | número (°) | Margen de error. Por debajo de él se considera que no hay movimiento y que una orden se cumplió. |

### 4.3 Configuración del razonamiento

| Propiedad | Clase | Valores | Significado |
|---|---|---|---|
| `nombre-objetivo` | `ObjetivoActivo` | `seguretat-persones`, `integritat-mecanica`, `proteccio-cultiu`, `produccio-energia`, `estabilitat` | Nombre del objetivo. |
| `prioridad` | `ObjetivoActivo` | entero (1–5) | Importancia; 1 es la más alta. |
| `tipo-restriccion` | `ObjetivoActivo` | `dura`, `tova` | Si el objetivo es obligatorio o solo deseable. |
| `limite-inferior` | `Umbral` | número | Inicio del tramo (incluido). Si falta, el tramo no tiene mínimo. |
| `limite-superior` | `Umbral` | número | Fin del tramo (excluido). Si falta, el tramo no tiene máximo. |
| `referencia` | `Umbral` | `absoluta`, `cultiu`, `seguidor` | Con qué se compara el valor: directamente, o como diferencia con el umbral del cultivo o del seguidor. |
| `modulo` | `DefinicionFase` | nombre de módulo (`PERCEPCIO` … `NETEJA`) | El bloque de reglas que ejecuta la fase. |
| `siguiente` | `DefinicionFase` | fase | La fase que viene después. |
| `aprendizaje-activo` | `ParametrosAprendizaje` | sí/no | Si el sistema aprende. "No" sirve como línea base para comparar en los experimentos. |
| `tasa-decaimiento` | `ParametrosAprendizaje` | número (0.5) | Rapidez con que se debilita una regla aprendida que no se usa. |
| `umbral-olvido` | `ParametrosAprendizaje` | número (−2.0) | Por debajo de esta fuerza, la regla aprendida se borra. |
| `max-referencias` | `ParametrosAprendizaje` | entero (10) | Cuántos usos recientes recuerda cada regla aprendida. |

### 4.4 Observaciones y diagnósticos

| Propiedad | Clase | Valores | Significado |
|---|---|---|---|
| `calidad` | `ObservacionSensor` | `ok`, `degradat`, `fallada` | Fiabilidad de la lectura: buena, dudosa o fallida. |
| `angulo-actual` | `ObservacionPanel` | número (°) | Ángulo medido de los paneles. |
| `estado-mecanico` | `ObservacionPanel` | `operatiu`, `bloquejat`, `alarma` | Si los paneles funcionan, están bloqueados o en alarma. |
| `ocupacion` | `ObservacionPanel` | `lliure`, `persones`, `maquinaria` | Qué hay debajo de los paneles: nada, personas o maquinaria. |
| `tipo-diagnostico` | `Diagnostico` | `estres-termic`, `estres-hidric`, `risc-mecanic`, `risc-persones`, `oportunitat-energetica`, `incertesa-dades`, `fallada-actuador` | Qué se ha detectado (lista en §2.3). |
| `evidencias` | `Diagnostico` | textos (varios) | Las pruebas del diagnóstico (p. ej., `vent:critic`). |

### 4.5 Estado del razonamiento e impasses

| Propiedad | Clase | Valores | Significado |
|---|---|---|---|
| `subfase` | `EstadoSOAR` | `pendent`, `feta` | Si la fase actual está por hacer o ya hecha. |
| `resuelto` | `Impasse` | sí/no | Si el bloqueo ya se resolvió. |

### 4.6 Opciones, valoraciones y preferencias

| Propiedad | Clase | Valores | Significado |
|---|---|---|---|
| `angulo-objetivo` | `OperadorCandidato` | número (°) | Ángulo al que llevaría la acción. Vacío si no se conoce el ángulo actual. |
| `estado-candidato` | `OperadorCandidato` | `candidat`, `descartat`, `seleccionat`, `aplicat` | En qué punto está la opción: propuesta, descartada, elegida o ya ejecutada. |
| `motivos` | `OperadorCandidato` | textos (varios) | Por qué se propuso la opción. |
| `beneficio-mecanico` | `Valoracion` | nivel | Cuánto protege la acción la estructura. |
| `coste-movimiento` | `Valoracion` | nivel | Lo que cuesta el giro (desgaste). |
| `desplazamiento` | `Valoracion` | número (°) | Grados que habría que girar; 0 si la acción no mueve. |
| `tipo-preferencia` | `Preferencia` | `reject`, `require`, `better` | Prohibir, exigir o preferir. |
| `origen` | `Preferencia` | `regla`, `deliberacio`, `chunk` | Quién la emitió: la evaluación normal, la deliberación de un impasse o una regla aprendida. |
| `restriccion` | `Preferencia` | `R1` … `R5` | Qué regla de seguridad la provocó: personas debajo (R1), viento crítico (R2), fallo del actuador (R3), demasiados movimientos en la última hora (R4) o estado de los paneles desconocido (R5). |

### 4.7 Episodios (memoria y explicación)

| Propiedad | Clase | Valores | Significado |
|---|---|---|---|
| `situacion` | `Episodio` | textos (varios) | Los diagnósticos presentes al decidir. |
| `alternativas` | `Episodio` | acciones (varias) | Las opciones que había. |
| `descartes` | `Episodio` | textos (varios) | Cada opción descartada y el objetivo por el que se descartó. |
| `restricciones-activas` | `Episodio` | `R1` … `R5` (varias) | Las reglas de seguridad que estaban actuando. |
| `criterio-determinante` | `Episodio` | texto | El motivo final de la decisión: un objetivo o la estrategia con que se resolvió un impasse. |
| `angulo-previo` | `Episodio` | número (°) | Ángulo de los paneles al decidir. Sirve para saber si hubo movimiento. |
| `perdida-cultivo` | `Episodio` | nivel | Lo que se dejó de ganar para el cultivo al descartar otras opciones. |
| `perdida-energia` | `Episodio` | nivel | Lo que se dejó de ganar en energía al descartar otras opciones. |
| `resultado` | `Episodio` | `pendent`, `ok`, `fallada-actuador` | Si la orden se cumplió: aún por comprobar, cumplida o con los paneles sin responder bien. |

### 4.8 Chunks (reglas aprendidas)

Un chunk dice: "si las acciones A y B empatan con estos beneficios y esta diferencia de giro, prefiere A".

| Propiedad | Clase | Valores | Significado |
|---|---|---|---|
| `accion-preferida` | `Chunk` | acción | La acción que hay que elegir (A). |
| `accion-descartada` | `Chunk` | acción | La acción que queda por detrás (B). |
| `beneficio-preferida` | `Chunk` | nivel | El mayor beneficio de A cuando se aprendió la regla. |
| `beneficio-descartada` | `Chunk` | nivel | El mayor beneficio de B cuando se aprendió la regla. |
| `relacion-delta` | `Chunk` | `menor`, `similar` | Si A obligaba a girar claramente menos que B, o lo mismo. |
| `referencias` | `Chunk` | enteros (varios) | Cuándo se creó la regla y cuándo funcionó. De estos instantes depende su fuerza: si se usa poco, se debilita y acaba olvidándose. |
