;;; 00_main.clp: módulo MAIN. Plantillas de la memoria de trabajo (vocabulario de
;;; ontologia/agrovoltaica-soar.ttl), funciones comunes y las reglas de control del ciclo.

(defmodule MAIN (export ?ALL))

;;; ---------------------------------------------------------------------------
;;; Conocimiento estático: lo carga python/ontologia.py desde el TTL. Nadie lo modifica.
;;; ---------------------------------------------------------------------------

(deftemplate sector
   (slot id) (slot tiene-cultivo) (slot tiene-seguidor))

(deftemplate cultivo
   (slot id) (slot umbral-temp-estres (type NUMBER)) (slot umbral-humedad-critica (type NUMBER)))

(deftemplate seguidor-solar
   (slot id) (slot angulo-minimo (type NUMBER)) (slot angulo-maximo (type NUMBER))
   (slot angulo-defensa-viento (type NUMBER)) (slot umbral-viento-critico (type NUMBER))
   (slot max-movimientos-hora (type INTEGER)) (slot tolerancia-angulo (type NUMBER)))

;; Política de prioridades: 1 es la más alta.
(deftemplate objetivo-activo
   (slot nombre-objetivo (allowed-symbols seguretat-persones integritat-mecanica proteccio-cultiu
                                          produccio-energia estabilitat))
   (slot prioridad (type INTEGER)))

;; Variable que debe observarse y nivel de incertidumbre si falta.
(deftemplate dato-requerido
   (slot variable) (slot nivel (allowed-symbols baix mitja alt critic)))

;; Tabla de fases: qué módulo ejecuta cada fase y cuál es la siguiente.
(deftemplate definicion-fase
   (slot fase) (slot modulo) (slot siguiente))

;; Intervalo [limite-inferior, limite-superior) que da un nivel; nil es infinito.
(deftemplate umbral
   (slot variable) (slot nivel (allowed-symbols baix mitja alt critic))
   (slot limite-inferior (default nil)) (slot limite-superior (default nil))
   (slot referencia (allowed-symbols absoluta cultiu seguidor)))

(deftemplate parametros-aprendizaje
   (slot aprendizaje-activo (allowed-symbols TRUE FALSE)) (slot tasa-decaimiento (type NUMBER))
   (slot umbral-olvido (type NUMBER)) (slot max-referencias (type INTEGER)))

;;; ---------------------------------------------------------------------------
;;; Control: el estado S0 (persiste) y los subestados e impasses (efímeros).
;;; ---------------------------------------------------------------------------

(deftemplate estado-soar
   (slot id) (slot estado-padre (default nil))
   (slot fase (allowed-symbols espera percepcio monitoratge elaboracio proposta avaluacio
                               seleccio deliberacio aplicacio explicacio aprenentatge neteja))
   (slot subfase (allowed-symbols pendent feta)) (slot impasse-asociado (default nil)))

(deftemplate impasse
   (slot id) (slot en-estado) (slot sector)
   (slot tipo-impasse (allowed-symbols tie dades-insuficients))
   (multislot operadores-en-conflicto) (slot resuelto (allowed-symbols FALSE TRUE))
   (slot estrategia-resolucion (default nil)))

;;; ---------------------------------------------------------------------------
;;; Observados: los aserta Python al empezar cada ciclo.
;;; ---------------------------------------------------------------------------

(deftemplate ciclo-temporal (slot instante (type INTEGER)))

(deftemplate observacion-sensor
   (slot sector) (slot variable) (slot valor (type NUMBER))
   (slot calidad (allowed-symbols ok degradat fallada)))

(deftemplate observacion-panel
   (slot sector) (slot angulo-actual (type NUMBER))
   (slot estado-mecanico (allowed-symbols operatiu bloquejat alarma))
   (slot ocupacion (allowed-symbols lliure persones maquinaria)))

;; Ángulos objetivo que calcula el simulador: angle-captacio y angle-ombra.
(deftemplate prediccion (slot sector) (slot variable) (slot valor (type NUMBER)))

;;; ---------------------------------------------------------------------------
;;; Derivados (ELABORACIO) y candidatos (PROPOSTA, AVALUACIO, SELECCIO).
;;; ---------------------------------------------------------------------------

(deftemplate abstraccion
   (slot sector) (slot variable) (slot nivel (allowed-symbols baix mitja alt critic)))

(deftemplate diagnostico
   (slot sector)
   (slot tipo-diagnostico (allowed-symbols estres-termic estres-hidric risc-mecanic risc-persones
                                           oportunitat-energetica fallada-actuador incertesa-dades))
   (slot nivel (allowed-symbols baix mitja alt critic)) (multislot evidencias))

(deftemplate operador-candidato
   (slot id) (slot sector)
   (slot accion (allowed-symbols orientar-produccio orientar-ombra posicio-seguretat
                                 mantenir-posicio diagnosticar))
   (slot angulo-objetivo (default nil))
   (slot estado-candidato (allowed-symbols candidat seleccionat descartat aplicat)))

(deftemplate valoracion
   (slot evalua-operador)
   (slot beneficio-mecanico (allowed-symbols baix mitja alt critic))
   (slot beneficio-cultivo (allowed-symbols baix mitja alt critic))
   (slot beneficio-energia (allowed-symbols baix mitja alt critic))
   (slot desplazamiento (type NUMBER)))

;; reject (operador-referencia prohibido) o better (referencia mejor que comparado).
(deftemplate preferencia
   (slot sector) (slot tipo-preferencia (allowed-symbols reject better))
   (slot operador-referencia) (slot operador-comparado (default nil))
   (slot criterio (allowed-symbols seguretat-persones integritat-mecanica proteccio-cultiu
                                   produccio-energia estabilitat))
   (slot origen (allowed-symbols regla deliberacio chunk))
   (slot restriccion (allowed-symbols nil R1 R2 R3 R4 R5)) (slot chunk-aplicado (default nil)))

;;; ---------------------------------------------------------------------------
;;; Resultados: órdenes (hasta MONITORATGE del ciclo siguiente), episodios (una hora)
;;; y chunks (hasta que se olvidan).
;;; ---------------------------------------------------------------------------

(deftemplate orden-actuador
   (slot sector) (slot accion) (slot angulo-ordenado (default nil))
   (slot instante (type INTEGER)) (slot escalado-humano (allowed-symbols FALSE TRUE)))

(deftemplate episodio
   (slot sector) (slot instante (type INTEGER)) (multislot situacion) (multislot alternativas)
   (multislot descartes) (multislot restricciones-activas) (slot criterio-determinante)
   (slot accion) (slot angulo-previo) (slot angulo-ordenado)
   (slot beneficio-cultivo) (slot beneficio-energia) (slot tipo-impasse) (slot chunk-aplicado)
   (slot resultado (allowed-symbols pendent ok fallada-actuador)))

(deftemplate chunk
   (slot id) (slot accion-preferida) (slot beneficio-preferida)
   (slot accion-descartada) (slot beneficio-descartada) (slot criterio)
   (slot estrategia-resolucion) (slot instante (type INTEGER)) (multislot referencias))

;;; ---------------------------------------------------------------------------
;;; Constantes y funciones comunes.
;;; ---------------------------------------------------------------------------

(defglobal ?*ventana-episodica* = 60)    ; minutos de la memoria episódica
(defglobal ?*minutos-por-ciclo* = 5)     ; el tiempo de la activación se mide en ciclos

;; Escala ordinal baix < mitja < alt < critic.
(deffunction nivel-num (?n)
   (- (member$ ?n (create$ baix mitja alt critic)) 1))

(deffunction nivel-max (?a ?b)
   (if (>= (nivel-num ?a) (nivel-num ?b)) then ?a else ?b))

;; ¿?x en [?inf, ?sup)? Un límite nil es infinito.
(deffunction dins-interval (?x ?inf ?sup)
   (and (or (eq ?inf nil) (>= ?x ?inf)) (or (eq ?sup nil) (< ?x ?sup))))

(deffunction accion-sin-movimiento (?a)
   (if (member$ ?a (create$ mantenir-posicio diagnosticar)) then TRUE else FALSE))

;; Beneficio del candidato de acción ?a en el criterio de la acción que se mueve ?x: el nivel de
;; los diagnósticos que motivan ?x si ?a es ?x, o si ?a no se mueve y ?x no se propuso porque el
;; panel ya está en su ángulo (beneficio heredado). Si no, baix.
(deffunction beneficio (?s ?a ?x)
   (if (and (neq ?a ?x)
            (or (not (accion-sin-movimiento ?a))
                (any-factp ((?c operador-candidato)) (and (eq ?c:sector ?s) (eq ?c:accion ?x)))))
      then (return baix))
   (bind ?motivos (switch ?x (case posicio-seguretat then (create$ risc-mecanic))
                             (case orientar-ombra then (create$ estres-termic estres-hidric))
                             (default (create$ oportunitat-energetica))))
   (bind ?n baix)
   (do-for-all-facts ((?d diagnostico)) (and (eq ?d:sector ?s) (member$ ?d:tipo-diagnostico ?motivos))
      (bind ?n (nivel-max ?n ?d:nivel)))
   ?n)

;; Objetivo más prioritario al que sirve un candidato: el de su criterio con beneficio ≥ mitja,
;; o estabilitat (mínima intervención) si no sirve a ninguno.
(deffunction objetivo-servido (?c)
   (bind ?v (nth$ 1 (find-fact ((?f valoracion)) (eq ?f:evalua-operador ?c))))
   (if (>= (nivel-num (fact-slot-value ?v beneficio-mecanico)) 1) then (return integritat-mecanica))
   (if (>= (nivel-num (fact-slot-value ?v beneficio-cultivo)) 1) then (return proteccio-cultiu))
   (if (>= (nivel-num (fact-slot-value ?v beneficio-energia)) 1) then (return produccio-energia))
   estabilitat)

;; Candidatos del sector que no están rechazados ni tienen un better en contra de un candidato
;; no rechazado.
(deffunction no-dominados (?s)
   (bind ?r (create$))
   (do-for-all-facts ((?c operador-candidato)) (and (eq ?c:sector ?s) (eq ?c:estado-candidato candidat))
      (if (not (or (any-factp ((?p preferencia)) (and (eq ?p:tipo-preferencia reject)
                                                       (eq ?p:operador-referencia ?c:id)))
                   (any-factp ((?p preferencia))
                      (and (eq ?p:tipo-preferencia better) (eq ?p:operador-comparado ?c:id)
                           (not (any-factp ((?q preferencia))
                                   (and (eq ?q:tipo-preferencia reject)
                                        (eq ?q:operador-referencia ?p:operador-referencia))))))))
         then (bind ?r (create$ ?r ?c:id))))
   ?r)

;; Mayor de los tres beneficios de una valoración: la condición que guarda el chunk.
(deffunction beneficio-maximo (?c)
   (bind ?v (nth$ 1 (find-fact ((?f valoracion)) (eq ?f:evalua-operador ?c))))
   (nivel-max (fact-slot-value ?v beneficio-mecanico)
              (nivel-max (fact-slot-value ?v beneficio-cultivo) (fact-slot-value ?v beneficio-energia))))

;; Chunk que prefiere el candidato ?a frente a ?b (mismas acciones y beneficios), o FALSE.
(deffunction chunk-aplicable (?a ?b)
   (bind ?aa (fact-slot-value (nth$ 1 (find-fact ((?c operador-candidato)) (eq ?c:id ?a))) accion))
   (bind ?ab (fact-slot-value (nth$ 1 (find-fact ((?c operador-candidato)) (eq ?c:id ?b))) accion))
   (bind ?k (find-fact ((?k chunk))
               (and (eq ?k:accion-preferida ?aa) (eq ?k:beneficio-preferida (beneficio-maximo ?a))
                    (eq ?k:accion-descartada ?ab) (eq ?k:beneficio-descartada (beneficio-maximo ?b)))))
   (if (= (length$ ?k) 0) then FALSE else (nth$ 1 ?k)))

;; Activación base de Soar: A = ln Σ Δtⱼ^−d, con Δtⱼ en ciclos (mínimo 1).
(deffunction activacio (?referencias ?t ?d)
   (bind ?suma 0.0)
   (foreach ?r ?referencias
      (bind ?suma (+ ?suma (** (max 1 (/ (- ?t ?r) ?*minutos-por-ciclo*)) (- 0 ?d)))))
   (log ?suma))

;; Memoria episódica: ¿episodio del sector en la última hora que cumple ?condicion?
(deffunction episodio-reciente-p (?e ?s ?t)
   (and (eq (fact-slot-value ?e sector) ?s) (< (fact-slot-value ?e instante) ?t)
        (>= (fact-slot-value ?e instante) (- ?t ?*ventana-episodica*))))

;; R3: fallo del actuador en este ciclo, o en la última hora al intentar mover el panel.
(deffunction fallada-reciente (?s ?t)
   (or (any-factp ((?d diagnostico)) (and (eq ?d:sector ?s) (eq ?d:tipo-diagnostico fallada-actuador)))
       (any-factp ((?e episodio)) (and (episodio-reciente-p ?e ?s ?t) (eq ?e:resultado fallada-actuador)
                                       (not (accion-sin-movimiento ?e:accion))))))

;; R4: movimientos del panel en la última hora.
(deffunction movimientos-recientes (?s ?t)
   (length$ (find-all-facts ((?e episodio))
               (and (episodio-reciente-p ?e ?s ?t) (not (accion-sin-movimiento ?e:accion))))))

;; Deliberación: ¿hubo riesgo mecánico alt o critic en el sector en la última hora?
(deffunction riesgo-reciente (?s ?t)
   (any-factp ((?e episodio)) (and (episodio-reciente-p ?e ?s ?t)
                                   (or (member$ risc-mecanic:alt ?e:situacion)
                                       (member$ risc-mecanic:critic ?e:situacion)))))

;;; ---------------------------------------------------------------------------
;;; Control del ciclo de decisión. S0 recorre la tabla de fases (definicion-fase).
;;; ---------------------------------------------------------------------------

;; SOAR: entrada. Llega un ciclo con S0 en espera: empieza por percepcio.
(defrule iniciar-ciclo
   ?s <- (estado-soar (id S0) (fase espera))
   (ciclo-temporal)
   =>
   (modify ?s (fase percepcio) (subfase pendent)))

;; SOAR: ciclo de decisión. Fase pendiente: se marca hecha y se enfoca su módulo.
(defrule ejecutar-fase
   ?s <- (estado-soar (id S0) (fase ?f) (subfase pendent))
   (definicion-fase (fase ?f) (modulo ?m))
   =>
   (modify ?s (subfase feta))
   (focus ?m))

;; SOAR: ciclo de decisión. Fase hecha sin impasses abiertos: siguiente fase de la tabla.
(defrule avanzar-fase
   ?s <- (estado-soar (id S0) (fase ?f) (subfase feta))
   (definicion-fase (fase ?f) (siguiente ?g))
   (not (impasse (resuelto FALSE)))
   =>
   (modify ?s (fase ?g) (subfase pendent)))

;; SOAR: impasse. La selección deja un impasse abierto: se delibera y se vuelve a seleccio.
(defrule abrir-deliberacio
   ?s <- (estado-soar (id S0) (fase seleccio) (subfase feta))
   (exists (impasse (resuelto FALSE)))
   =>
   (modify ?s (fase deliberacio) (subfase pendent)))
