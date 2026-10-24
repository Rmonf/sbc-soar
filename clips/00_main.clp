;;; 00_main.clp: módulo MAIN con las plantillas, las deffunction y las reglas de control (roadmap §4.3, §8).
;;; Plantillas del conocimiento estático (§3.1) y de las cinco familias de hechos dinámicos
;;; (§3.2); falta chunk (I4). Convenciones de §2.3.

(defmodule MAIN (export ?ALL))

;;; ---------------------------------------------------------------------------
;;; Conocimiento estático (§3.1). Los hechos los genera python/ontologia.py
;;; en config/base_coneixement.clp.
;;; ---------------------------------------------------------------------------

;; Sector de la instalación, con su cultivo y su seguidor (§3.1).
(deftemplate MAIN::sector
   (slot id (type SYMBOL))
   (slot tiene-cultivo (type SYMBOL))
   (slot tiene-seguidor (type SYMBOL)))

;; Parámetros agronómicos del cultivo de un sector (§3.1).
(deftemplate MAIN::cultivo
   (slot id (type SYMBOL))
   (slot nombre-cultivo (type SYMBOL))
   (slot fase-fenologica (type SYMBOL))
   (slot sensibilidad (type SYMBOL) (allowed-symbols baix mitja alt critic))
   (slot umbral-temp-estres (type NUMBER))
   (slot umbral-humedad-critica (type NUMBER)))

;; Límites mecánicos y de desgaste del seguidor de un sector (§3.1).
(deftemplate MAIN::seguidor-solar
   (slot id (type SYMBOL))
   (slot angulo-minimo (type NUMBER))
   (slot angulo-maximo (type NUMBER))
   (slot angulo-defensa-viento (type NUMBER))
   (slot umbral-viento-critico (type NUMBER))
   (slot max-movimientos-hora (type INTEGER))
   (slot tolerancia-angulo (type NUMBER)))

;; Objetivo de la política de prioridades: 1 es el más prioritario (§3.1).
(deftemplate MAIN::objetivo-activo
   (slot nombre-objetivo (type SYMBOL)
      (allowed-symbols seguretat-persones integritat-mecanica proteccio-cultiu
                       produccio-energia estabilitat))
   (slot prioridad (type INTEGER))
   (slot tipo-restriccion (type SYMBOL) (allowed-symbols dura tova)))

;; Variable que se debe observar y nivel de incertidumbre si falta (§3.1, §5.1).
(deftemplate MAIN::dato-requerido
   (slot variable (type SYMBOL)
      (allowed-symbols radiacio temp-cultiu temp-ambient humitat-sol vent vent-previst
                       pluja pluja-prevista preu-energia produccio moviment
                       angle-captacio angle-ombra))
   (slot nivel (type SYMBOL) (allowed-symbols baix mitja alt critic)))

;; Fila de la tabla de fases: módulo que la ejecuta y fase siguiente (§4.1).
(deftemplate MAIN::definicion-fase
   (slot fase (type SYMBOL)
      (allowed-symbols espera percepcio monitoratge elaboracio proposta avaluacio
                       seleccio deliberacio aplicacio explicacio aprenentatge neteja))
   (slot modulo (type SYMBOL)
      (allowed-symbols PERCEPCIO MONITORATGE ELABORACIO PROPOSTA AVALUACIO SELECCIO
                       DELIBERACIO APLICACIO EXPLICACIO APRENENTATGE NETEJA))
   (slot siguiente (type SYMBOL)
      (allowed-symbols espera percepcio monitoratge elaboracio proposta avaluacio
                       seleccio deliberacio aplicacio explicacio aprenentatge neteja)))

;; Intervalo [limite-inferior, limite-superior) que da un nivel a una variable;
;; un límite nil es infinito (§3.1, §5.3).
(deftemplate MAIN::umbral
   (slot variable (type SYMBOL)
      (allowed-symbols radiacio temp-cultiu temp-ambient humitat-sol vent vent-previst
                       pluja pluja-prevista preu-energia produccio moviment
                       angle-captacio angle-ombra))
   (slot nivel (type SYMBOL) (allowed-symbols baix mitja alt critic))
   (slot limite-inferior (type NUMBER SYMBOL) (allowed-symbols nil) (default nil))
   (slot limite-superior (type NUMBER SYMBOL) (allowed-symbols nil) (default nil))
   (slot referencia (type SYMBOL) (allowed-symbols absoluta cultiu seguidor)))

;; Parámetros de la memoria de chunks (§5.10, §6.2).
(deftemplate MAIN::parametros-aprendizaje
   (slot aprendizaje-activo (type SYMBOL) (allowed-symbols TRUE FALSE))
   (slot tasa-decaimiento (type NUMBER))
   (slot umbral-olvido (type NUMBER))
   (slot max-referencias (type INTEGER)))

;;; ---------------------------------------------------------------------------
;;; Familia 3: control (§3.2). S0 viene de la configuración generada.
;;; ---------------------------------------------------------------------------

;; Estado raíz S0 o subestado de deliberación (§3.2, §4.2, §5.7).
(deftemplate MAIN::estado-soar
   (slot id (type SYMBOL))
   (slot estado-padre (type SYMBOL) (default nil))
   (slot fase (type SYMBOL)
      (allowed-symbols espera percepcio monitoratge elaboracio proposta avaluacio
                       seleccio deliberacio aplicacio explicacio aprenentatge neteja))
   (slot subfase (type SYMBOL) (allowed-symbols pendent feta))
   (slot impasse-asociado (type SYMBOL) (default nil)))

;; Conflicto del procedimiento de decisión que se resuelve en un subestado (§3.2, §5.6, §5.7).
(deftemplate MAIN::impasse
   (slot id (type SYMBOL))
   (slot en-estado (type SYMBOL))
   (slot sector (type SYMBOL))
   (slot tipo-impasse (type SYMBOL) (allowed-symbols tie dades-insuficients constraint-failure))
   (multislot operadores-en-conflicto (type SYMBOL))
   (slot resuelto (type SYMBOL) (allowed-symbols TRUE FALSE))
   (slot estrategia-resolucion (type SYMBOL)
      (allowed-symbols minima-intervencio prioritat-objectius posicio-preventiva demanar-dades
                       restriccio-prioritaria escalat nil)
      (default nil)))

;;; ---------------------------------------------------------------------------
;;; Familia 1: observados (§3.2). Solo los aserta el simulador.
;;; ---------------------------------------------------------------------------

;; Marca de tiempo del ciclo, en minutos desde el inicio (§2.3.8).
(deftemplate MAIN::ciclo-temporal
   (slot instante (type INTEGER)))

;; Lectura de un sensor de un sector (§3.3).
(deftemplate MAIN::observacion-sensor
   (slot id (type SYMBOL))
   (slot sector (type SYMBOL))
   (slot variable (type SYMBOL)
      (allowed-symbols radiacio temp-cultiu temp-ambient humitat-sol vent vent-previst
                       pluja pluja-prevista preu-energia produccio moviment
                       angle-captacio angle-ombra))
   (slot valor (type NUMBER))
   (slot instante (type INTEGER))
   (slot calidad (type SYMBOL) (allowed-symbols ok degradat fallada)))

;; Estado observado del seguidor de un sector (§3.3).
(deftemplate MAIN::observacion-panel
   (slot sector (type SYMBOL))
   (slot angulo-actual (type NUMBER))
   (slot estado-mecanico (type SYMBOL) (allowed-symbols operatiu bloquejat alarma))
   (slot ocupacion (type SYMBOL) (allowed-symbols lliure persones maquinaria))
   (slot instante (type INTEGER)))

;; Previsión de una variable; sector nil = magnitud global, como el precio (§2.3.7, §3.3).
(deftemplate MAIN::prediccion
   (slot sector (type SYMBOL) (default nil))
   (slot variable (type SYMBOL)
      (allowed-symbols radiacio temp-cultiu temp-ambient humitat-sol vent vent-previst
                       pluja pluja-prevista preu-energia produccio moviment
                       angle-captacio angle-ombra))
   (slot valor (type NUMBER))
   (slot instante (type INTEGER)))

;;; ---------------------------------------------------------------------------
;;; Familia 2: derivados (§3.2).
;;; ---------------------------------------------------------------------------

;; Nivel cualitativo de una variable observada (§5.3).
(deftemplate MAIN::abstraccion
   (slot sector (type SYMBOL))
   (slot variable (type SYMBOL)
      (allowed-symbols radiacio temp-cultiu temp-ambient humitat-sol vent vent-previst
                       pluja pluja-prevista preu-energia produccio moviment
                       angle-captacio angle-ombra))
   (slot nivel (type SYMBOL) (allowed-symbols baix mitja alt critic)))

;; Riesgo, necesidad u oportunidad de un sector; uno por sector y tipo (§2.3.10, §5.3).
(deftemplate MAIN::diagnostico
   (slot id (type SYMBOL))
   (slot sector (type SYMBOL))
   (slot tipo-diagnostico (type SYMBOL)
      (allowed-symbols estres-termic estres-hidric risc-mecanic risc-persones
                       oportunitat-energetica fallada-actuador incertesa-dades))
   (slot nivel (type SYMBOL) (allowed-symbols baix mitja alt critic))
   (multislot evidencias (type SYMBOL)))

;;; ---------------------------------------------------------------------------
;;; Familia 4: candidatos (§3.2).
;;; ---------------------------------------------------------------------------

;; Operador propuesto para un sector (§5.4).
(deftemplate MAIN::operador-candidato
   (slot id (type SYMBOL))
   (slot en-estado (type SYMBOL))
   (slot sector (type SYMBOL))
   (slot accion (type SYMBOL)
      (allowed-symbols orientar-produccio orientar-ombra posicio-seguretat mantenir-posicio
                       diagnosticar))
   (slot angulo-objetivo (type NUMBER SYMBOL) (allowed-symbols nil) (default nil))
   (slot estado-candidato (type SYMBOL) (allowed-symbols candidat descartat seleccionat aplicat))
   (multislot motivos (type SYMBOL)))

;; Valoración de un candidato por criterio (§5.5b).
(deftemplate MAIN::valoracion
   (slot evalua-operador (type SYMBOL))
   (slot beneficio-mecanico (type SYMBOL) (allowed-symbols baix mitja alt critic))
   (slot beneficio-cultivo (type SYMBOL) (allowed-symbols baix mitja alt critic))
   (slot beneficio-energia (type SYMBOL) (allowed-symbols baix mitja alt critic))
   (slot coste-movimiento (type SYMBOL) (allowed-symbols baix mitja alt critic))
   (slot desplazamiento (type NUMBER)))

;; Preferencia sobre candidatos: reject, require o better (§5.5, §5.6).
(deftemplate MAIN::preferencia
   (slot en-estado (type SYMBOL))
   (slot sector (type SYMBOL))
   (slot tipo-preferencia (type SYMBOL) (allowed-symbols reject require better))
   (slot operador-referencia (type SYMBOL))
   (slot operador-comparado (type SYMBOL) (default nil))
   (slot criterio (type SYMBOL)
      (allowed-symbols seguretat-persones integritat-mecanica proteccio-cultiu
                       produccio-energia estabilitat))
   (slot origen (type SYMBOL) (allowed-symbols regla deliberacio chunk))
   (slot restriccion (type SYMBOL) (allowed-symbols R1 R2 R3 R4 R5 nil) (default nil))
   (slot chunk-aplicado (type SYMBOL) (default nil)))

;;; ---------------------------------------------------------------------------
;;; Familia 5: resultados (§3.2).
;;; ---------------------------------------------------------------------------

;; Orden para el actuador de un sector; nil en angulo-ordenado = no mover (§5.8).
(deftemplate MAIN::orden-actuador
   (slot id (type SYMBOL))
   (slot sector (type SYMBOL))
   (slot accion (type SYMBOL)
      (allowed-symbols orientar-produccio orientar-ombra posicio-seguretat mantenir-posicio
                       diagnosticar))
   (slot angulo-ordenado (type NUMBER SYMBOL) (allowed-symbols nil) (default nil))
   (slot instante (type INTEGER))
   (slot escalado-humano (type SYMBOL) (allowed-symbols TRUE FALSE)))

;; Registro auditable de una decisión: memoria episódica (§3.3, §5.9).
(deftemplate MAIN::episodio
   (slot id (type SYMBOL))
   (slot sector (type SYMBOL))
   (slot instante (type INTEGER))
   (multislot situacion (type SYMBOL))
   (multislot alternativas (type SYMBOL)
      (allowed-symbols orientar-produccio orientar-ombra posicio-seguretat mantenir-posicio
                       diagnosticar))
   (multislot descartes (type SYMBOL))
   (multislot restricciones-activas (type SYMBOL) (allowed-symbols R1 R2 R3 R4 R5))
   (slot criterio-determinante (type SYMBOL))
   (slot accion (type SYMBOL)
      (allowed-symbols orientar-produccio orientar-ombra posicio-seguretat mantenir-posicio
                       diagnosticar))
   (slot angulo-previo (type NUMBER SYMBOL) (allowed-symbols nil) (default nil))
   (slot angulo-ordenado (type NUMBER SYMBOL) (allowed-symbols nil) (default nil))
   (slot beneficio-cultivo (type SYMBOL) (allowed-symbols baix mitja alt critic))
   (slot beneficio-energia (type SYMBOL) (allowed-symbols baix mitja alt critic))
   (slot perdida-cultivo (type SYMBOL) (allowed-symbols baix mitja alt critic))
   (slot perdida-energia (type SYMBOL) (allowed-symbols baix mitja alt critic))
   (slot tipo-impasse (type SYMBOL)
      (allowed-symbols tie dades-insuficients constraint-failure nil)
      (default nil))
   (slot chunk-aplicado (type SYMBOL) (default nil))
   (slot escalado-humano (type SYMBOL) (allowed-symbols TRUE FALSE))
   (slot resultado (type SYMBOL) (allowed-symbols pendent ok fallada-actuador)))

;;; ---------------------------------------------------------------------------
;;; Defglobals (§8): constantes de convención del diseño, no umbrales del dominio.
;;; ---------------------------------------------------------------------------

;; Ventana de la memoria episódica en minutos: "la última hora" es instante ≥ t − 60 (§2.3.8).
(defglobal MAIN ?*ventana-episodica* = 60)

;;; ---------------------------------------------------------------------------
;;; Deffunctions (§8).
;;; ---------------------------------------------------------------------------

;; Escala ordinal baix < mitja < alt < critic convertida a 0-3 (§2.3.5).
(deffunction MAIN::nivel-num (?nivel)
   (switch ?nivel
      (case baix then 0)
      (case mitja then 1)
      (case alt then 2)
      (case critic then 3)))

;; ¿Está ?x en [?inferior, ?superior)? Un límite nil es infinito (§5.3).
(deffunction MAIN::dins-interval (?x ?inferior ?superior)
   (and (or (eq ?inferior nil) (>= ?x ?inferior))
        (or (eq ?superior nil) (< ?x ?superior))))

;; Nivel desplazado ?delta posiciones en la escala, dentro de baix…critic (refinamientos, §5.3).
(deffunction MAIN::nivel-desplazado (?nivel ?delta)
   (nth$ (+ 1 (max 0 (min 3 (+ (nivel-num ?nivel) ?delta)))) (create$ baix mitja alt critic)))

;; Nivel del diagnóstico tipo del sector, o baix si no existe (§5.5b). Los diagnósticos no
;; cambian después de ELABORACIO.
(deffunction MAIN::nivel-diagnostico (?sector ?tipo)
   (bind ?d (find-fact ((?f diagnostico)) (and (eq ?f:sector ?sector) (eq ?f:tipo-diagnostico ?tipo))))
   (if (= (length$ ?d) 0) then baix else (fact-slot-value (nth$ 1 ?d) nivel)))

;; Ángulo recortado al intervalo mecánico del seguidor (§5.4).
(deffunction MAIN::recortar-angulo (?angulo ?minimo ?maximo)
   (max ?minimo (min ?maximo ?angulo)))

;; El mayor de dos niveles de la escala ordinal (§2.3.5, §2.3.10).
(deffunction MAIN::nivel-max (?a ?b)
   (if (>= (nivel-num ?a) (nivel-num ?b)) then ?a else ?b))

;; Ángulo observado del panel del sector, o nil si no hay observacion-panel: dato
;; desconocido (§3.2). Las observaciones no cambian durante el ciclo.
(deffunction MAIN::angulo-observado (?sector)
   (bind ?p (find-fact ((?o observacion-panel)) (eq ?o:sector ?sector)))
   (if (= (length$ ?p) 0) then nil else (fact-slot-value (nth$ 1 ?p) angulo-actual)))

;; ¿Es una acción sin movimiento? (definiciones de §5).
(deffunction MAIN::accion-sin-movimiento (?accion)
   (if (member$ ?accion (create$ mantenir-posicio diagnosticar)) then TRUE else FALSE))

;; Tolerancia de ángulo del seguidor del sector (§3.1).
(deffunction MAIN::tolerancia-sector (?sector)
   (bind ?s (nth$ 1 (find-fact ((?f sector)) (eq ?f:id ?sector))))
   (fact-slot-value (nth$ 1 (find-fact ((?g seguidor-solar)) (eq ?g:id (fact-slot-value ?s tiene-seguidor))))
                    tolerancia-angulo))

;; ¿Mueve el candidato? No es acción sin movimiento y Δ > tolerancia, o Δ desconocido porque
;; no se observa el panel (definiciones de §5).
(deffunction MAIN::candidato-mueve (?accion ?objetivo ?sector)
   (if (accion-sin-movimiento ?accion) then (return FALSE))
   (bind ?actual (angulo-observado ?sector))
   (if (eq ?actual nil) then (return TRUE))
   (> (abs (- ?objetivo ?actual)) (tolerancia-sector ?sector)))

;; Episodios del sector en [t − ventana, t) en los que se movió el panel: |angulo-ordenado −
;; angulo-previo| > tolerancia (R4, §5.5a). Los episodios no cambian en AVALUACIO.
(deffunction MAIN::movimientos-recientes (?sector ?t)
   (bind ?tol (tolerancia-sector ?sector))
   (bind ?n 0)
   (do-for-all-facts ((?e episodio))
         (and (eq ?e:sector ?sector) (>= ?e:instante (- ?t ?*ventana-episodica*)) (< ?e:instante ?t)
              (neq ?e:angulo-ordenado nil) (neq ?e:angulo-previo nil)
              (> (abs (- ?e:angulo-ordenado ?e:angulo-previo)) ?tol))
      (bind ?n (+ ?n 1)))
   ?n)

;;; ---------------------------------------------------------------------------
;;; Reglas de control (§4.2). Localizan S0 por (id S0) y son mutuamente excluyentes.
;;; ---------------------------------------------------------------------------

;; Llega un ciclo-temporal con S0 en espera: empieza el ciclo por percepcio (§4.2.1).
(defrule MAIN::iniciar-ciclo
   ?s <- (estado-soar (id S0) (fase espera))
   (ciclo-temporal)
   =>
   (modify ?s (fase percepcio) (subfase pendent)))

;; Fase pendiente: se marca feta y se enfoca su módulo (§4.2.2).
(defrule MAIN::ejecutar-fase
   ?s <- (estado-soar (id S0) (fase ?f) (subfase pendent))
   (definicion-fase (fase ?f) (modulo ?m))
   =>
   (modify ?s (subfase feta))
   (focus ?m))

;; Fase hecha y sin impasses abiertos: se pasa a la siguiente de la tabla (§4.2.3).
(defrule MAIN::avanzar-fase
   ?s <- (estado-soar (id S0) (fase ?f) (subfase feta))
   (definicion-fase (fase ?f) (siguiente ?g))
   (not (impasse (resuelto FALSE)))
   =>
   (modify ?s (fase ?g) (subfase pendent)))

;; Selección hecha con algún impasse abierto: se delibera (§4.2.4).
(defrule MAIN::abrir-deliberacio
   ?s <- (estado-soar (id S0) (fase seleccio) (subfase feta))
   (exists (impasse (resuelto FALSE)))
   =>
   (modify ?s (fase deliberacio) (subfase pendent)))

;; La deliberación no ha resuelto un impasse: se deriva a una persona (§4.2.5, enunciado 3.7.3).
(defrule MAIN::escalar-impasse
   (estado-soar (id S0) (fase deliberacio) (subfase feta))
   ?i <- (impasse (resuelto FALSE))
   =>
   (modify ?i (resuelto TRUE) (estrategia-resolucion escalat)))
