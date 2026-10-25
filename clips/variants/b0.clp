;;; b0.clp: línea base B0 del experimento de agenda (roadmap §11.3). NO es código de producción.
;;; Al estilo de auto.clp: la decisión la toma directamente la salience, sin valoraciones,
;;; preferencias better, impasses, deliberación ni aprendizaje. Sustituye 05_avaluacio,
;;; 06_seleccio y 07_deliberacio (pont_clips.VARIANTES); PROPOSTA (§5.4) y el resto de fases son
;;; las de producción, así que B0 tiene exactamente las mismas condiciones de aplicabilidad y las
;;; mismas restricciones duras: solo cambia cómo se resuelve el conflicto.
;;;   - En la fase avaluacio, R1–R5 son copias textuales de las de producción con la salience más
;;;     alta (10; objetivos de prioridad 1 y 2): todas las prohibiciones se asertan antes de elegir.
;;;   - En la misma fase, una regla por objetivo con salience = 6 − prioridad selecciona el
;;;     candidato del sector que sirve a ese objetivo si no está rechazado y el sector aún no
;;;     tiene seleccionado: la primera que dispara gana.
;;;   - En la fase seleccio solo queda la copia de descartar-resto; DELIBERACIO queda vacía.
;;; tests/test_variantes.py comprueba las copias y que cada salience es 6 − la prioridad del TTL.

(defmodule AVALUACIO (import MAIN ?ALL))
(defmodule SELECCIO (import MAIN ?ALL))
(defmodule DELIBERACIO (import MAIN ?ALL))

;;; --- Restricciones duras: copias de 05_avaluacio.clp con salience 10 ---

;; Copia de AVALUACIO::r1-rechazar-con-personas (05_avaluacio.clp) con salience 10 (§5.5a, §11.3 B0).
(defrule AVALUACIO::r1-rechazar-con-personas
   (declare (salience 10))
   (estado-soar (id S0) (fase avaluacio))
   (diagnostico (sector ?s) (tipo-diagnostico risc-persones))
   (operador-candidato (id ?c) (sector ?s) (accion ?a) (angulo-objetivo ?o))
   (test (candidato-mueve ?a ?o ?s))
   =>
   (assert (preferencia (en-estado S0) (sector ?s) (tipo-preferencia reject)
                        (operador-referencia ?c) (criterio seguretat-persones)
                        (origen regla) (restriccion R1))))

;; Copia de AVALUACIO::r2-rechazar-orientar (05_avaluacio.clp) con salience 10 (§5.5a, §11.3 B0).
(defrule AVALUACIO::r2-rechazar-orientar
   (declare (salience 10))
   (estado-soar (id S0) (fase avaluacio))
   (diagnostico (sector ?s) (tipo-diagnostico risc-mecanic) (nivel critic))
   (operador-candidato (id ?c) (sector ?s) (accion orientar-produccio|orientar-ombra))
   =>
   (assert (preferencia (en-estado S0) (sector ?s) (tipo-preferencia reject)
                        (operador-referencia ?c) (criterio integritat-mecanica)
                        (origen regla) (restriccion R2))))

;; Copia de AVALUACIO::r3-rechazar-con-fallada (05_avaluacio.clp) con salience 10 (§5.5a, §11.3 B0).
(defrule AVALUACIO::r3-rechazar-con-fallada
   (declare (salience 10))
   (estado-soar (id S0) (fase avaluacio))
   (diagnostico (sector ?s) (tipo-diagnostico fallada-actuador))
   (operador-candidato (id ?c) (sector ?s) (accion ?a) (angulo-objetivo ?o))
   (test (candidato-mueve ?a ?o ?s))
   =>
   (assert (preferencia (en-estado S0) (sector ?s) (tipo-preferencia reject)
                        (operador-referencia ?c) (criterio integritat-mecanica)
                        (origen regla) (restriccion R3))))

;; Copia de AVALUACIO::r4-rechazar-por-desgaste (05_avaluacio.clp) con salience 10 (§5.5a, §11.3 B0).
(defrule AVALUACIO::r4-rechazar-por-desgaste
   (declare (salience 10))
   (estado-soar (id S0) (fase avaluacio))
   (ciclo-temporal (instante ?t))
   (sector (id ?s) (tiene-seguidor ?sg))
   (seguidor-solar (id ?sg) (max-movimientos-hora ?max))
   (test (>= (movimientos-recientes ?s ?t) ?max))
   (operador-candidato (id ?c) (sector ?s) (accion ?a&~posicio-seguretat) (angulo-objetivo ?o))
   (test (candidato-mueve ?a ?o ?s))
   =>
   (assert (preferencia (en-estado S0) (sector ?s) (tipo-preferencia reject)
                        (operador-referencia ?c) (criterio integritat-mecanica)
                        (origen regla) (restriccion R4))))

;; Copia de AVALUACIO::r5-rechazar-sin-panel (05_avaluacio.clp) con salience 10 (§5.5a, §11.3 B0).
(defrule AVALUACIO::r5-rechazar-sin-panel
   (declare (salience 10))
   (estado-soar (id S0) (fase avaluacio))
   (ciclo-temporal (instante ?t))
   (sector (id ?s))
   (not (observacion-panel (sector ?s) (instante ?t)))
   (operador-candidato (id ?c) (sector ?s) (accion ?a) (angulo-objetivo ?o))
   (test (candidato-mueve ?a ?o ?s))
   =>
   (assert (preferencia (en-estado S0) (sector ?s) (tipo-preferencia reject)
                        (operador-referencia ?c) (criterio seguretat-persones)
                        (origen regla) (restriccion R5))))

;; Copia de AVALUACIO::r2-requerir-seguretat (05_avaluacio.clp) con salience 10 (§5.5a, §11.3 B0).
(defrule AVALUACIO::r2-requerir-seguretat
   (declare (salience 10))
   (estado-soar (id S0) (fase avaluacio))
   (diagnostico (sector ?s) (tipo-diagnostico risc-mecanic) (nivel critic))
   (operador-candidato (id ?c) (sector ?s) (accion posicio-seguretat))
   =>
   (assert (preferencia (en-estado S0) (sector ?s) (tipo-preferencia require)
                        (operador-referencia ?c) (criterio integritat-mecanica)
                        (origen regla) (restriccion R2))))

;;; --- Elección por objetivo: salience = 6 − prioridad del objetivo (TTL) ---

;; B0, integritat-mecanica (prioridad 2): selecciona posicio-seguretat si no está rechazada,
;; propuesta por risc-mecanic ≥ alt o incertesa-dades ≥ mitja (§5.4); con el require de R2
;; también se elige aquí (§11.3 B0).
(defrule AVALUACIO::b0-elegir-integritat-mecanica
   (declare (salience 4))
   (estado-soar (id S0) (fase avaluacio))
   (objetivo-activo (nombre-objetivo integritat-mecanica))
   ?f <- (operador-candidato (id ?c) (sector ?s) (accion posicio-seguretat) (estado-candidato candidat))
   (not (preferencia (tipo-preferencia reject) (operador-referencia ?c)))
   (not (operador-candidato (sector ?s) (estado-candidato seleccionat)))
   =>
   (modify ?f (estado-candidato seleccionat)))

;; B0, proteccio-cultiu (prioridad 3): selecciona orientar-ombra si no está rechazada,
;; propuesta por estres-termic o estres-hidric (§5.4) (§11.3 B0).
(defrule AVALUACIO::b0-elegir-proteccio-cultiu
   (declare (salience 3))
   (estado-soar (id S0) (fase avaluacio))
   (objetivo-activo (nombre-objetivo proteccio-cultiu))
   ?f <- (operador-candidato (id ?c) (sector ?s) (accion orientar-ombra) (estado-candidato candidat))
   (not (preferencia (tipo-preferencia reject) (operador-referencia ?c)))
   (not (operador-candidato (sector ?s) (estado-candidato seleccionat)))
   =>
   (modify ?f (estado-candidato seleccionat)))

;; B0, produccio-energia (prioridad 4): selecciona orientar-produccio si no está rechazada,
;; propuesta por oportunitat-energetica (§5.4) (§11.3 B0).
(defrule AVALUACIO::b0-elegir-produccio-energia
   (declare (salience 2))
   (estado-soar (id S0) (fase avaluacio))
   (objetivo-activo (nombre-objetivo produccio-energia))
   ?f <- (operador-candidato (id ?c) (sector ?s) (accion orientar-produccio) (estado-candidato candidat))
   (not (preferencia (tipo-preferencia reject) (operador-referencia ?c)))
   (not (operador-candidato (sector ?s) (estado-candidato seleccionat)))
   =>
   (modify ?f (estado-candidato seleccionat)))

;; B0, estabilitat (prioridad 5): selecciona la acción sin movimiento si no está rechazada,
;; mantenir-posicio o diagnosticar, que se excluyen (§5.4); las restricciones no la rechazan
;; nunca, así que siempre hay una decisión (§11.3 B0).
(defrule AVALUACIO::b0-elegir-estabilitat
   (declare (salience 1))
   (estado-soar (id S0) (fase avaluacio))
   (objetivo-activo (nombre-objetivo estabilitat))
   ?f <- (operador-candidato (id ?c) (sector ?s) (accion mantenir-posicio|diagnosticar)
                             (estado-candidato candidat))
   (not (preferencia (tipo-preferencia reject) (operador-referencia ?c)))
   (not (operador-candidato (sector ?s) (estado-candidato seleccionat)))
   =>
   (modify ?f (estado-candidato seleccionat)))

;;; --- Selección: copia de 06_seleccio.clp ---

;; Copia de SELECCIO::descartar-resto (06_seleccio.clp) (§5.6, §11.3 B0).
(defrule SELECCIO::descartar-resto
   (estado-soar (id S0) (fase seleccio))
   (operador-candidato (sector ?s) (estado-candidato seleccionat))
   ?f <- (operador-candidato (sector ?s) (estado-candidato candidat))
   =>
   (modify ?f (estado-candidato descartat)))
