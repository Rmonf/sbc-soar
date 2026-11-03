;;; b0.clp: línea base B0 del experimento de agenda. Decide "a la antigua", por salience: sin
;;; valoraciones, preferencias better, impasses ni chunks. Sustituye a 05_avaluacio, 06_seleccio,
;;; 07_deliberacio y 10_aprenentatge; define los mismos módulos para que la tabla de fases funcione.
;;; La propuesta y las restricciones R1–R5 son las del núcleo: solo cambia cómo se elige.

(defmodule AVALUACIO (import MAIN ?ALL))
(defmodule SELECCIO (import MAIN ?ALL))
(defmodule DELIBERACIO (import MAIN ?ALL))
(defmodule APRENENTATGE (import MAIN ?ALL))

;;; R1–R5, iguales que en 05_avaluacio.clp, con la salience más alta: se prohíbe antes de elegir.

(defrule AVALUACIO::r1-personas (declare (salience 10))
   (estado-soar (id S0) (fase avaluacio))
   (diagnostico (sector ?s) (tipo-diagnostico risc-persones))
   (operador-candidato (id ?c) (sector ?s) (accion ?a&:(not (accion-sin-movimiento ?a))))
   =>
   (assert (preferencia (sector ?s) (tipo-preferencia reject) (operador-referencia ?c)
                        (criterio seguretat-persones) (origen regla) (restriccion R1))))

(defrule AVALUACIO::r2-viento-critico (declare (salience 10))
   (estado-soar (id S0) (fase avaluacio))
   (diagnostico (sector ?s) (tipo-diagnostico risc-mecanic) (nivel critic))
   (operador-candidato (id ?c) (sector ?s) (accion orientar-produccio|orientar-ombra))
   =>
   (assert (preferencia (sector ?s) (tipo-preferencia reject) (operador-referencia ?c)
                        (criterio integritat-mecanica) (origen regla) (restriccion R2))))

(defrule AVALUACIO::r3-actuador-fallado (declare (salience 10))
   (estado-soar (id S0) (fase avaluacio))
   (ciclo-temporal (instante ?t))
   (operador-candidato (id ?c) (sector ?s) (accion ?a&:(not (accion-sin-movimiento ?a))))
   (test (fallada-reciente ?s ?t))
   =>
   (assert (preferencia (sector ?s) (tipo-preferencia reject) (operador-referencia ?c)
                        (criterio integritat-mecanica) (origen regla) (restriccion R3))))

(defrule AVALUACIO::r4-max-movimientos (declare (salience 10))
   (estado-soar (id S0) (fase avaluacio))
   (ciclo-temporal (instante ?t))
   (operador-candidato (id ?c) (sector ?s) (accion ?a&~posicio-seguretat&:(not (accion-sin-movimiento ?a))))
   (sector (id ?s) (tiene-seguidor ?g))
   (seguidor-solar (id ?g) (max-movimientos-hora ?max))
   (test (>= (movimientos-recientes ?s ?t) ?max))
   =>
   (assert (preferencia (sector ?s) (tipo-preferencia reject) (operador-referencia ?c)
                        (criterio integritat-mecanica) (origen regla) (restriccion R4))))

(defrule AVALUACIO::r5-panel-desconocido (declare (salience 10))
   (estado-soar (id S0) (fase avaluacio))
   (operador-candidato (id ?c) (sector ?s) (accion ?a&:(not (accion-sin-movimiento ?a))))
   (not (observacion-panel (sector ?s)))
   =>
   (assert (preferencia (sector ?s) (tipo-preferencia reject) (operador-referencia ?c)
                        (criterio seguretat-persones) (origen regla) (restriccion R5))))

;;; Una regla por objetivo, con salience = 6 − prioridad: elige el candidato no rechazado de su
;;; acción. El primer candidato seleccionado del sector bloquea a las demás.

(defrule AVALUACIO::b0-integritat-mecanica (declare (salience 4))
   (estado-soar (id S0) (fase avaluacio))
   ?f <- (operador-candidato (id ?c) (sector ?s) (accion posicio-seguretat) (estado-candidato candidat))
   (not (preferencia (tipo-preferencia reject) (operador-referencia ?c)))
   (not (operador-candidato (sector ?s) (estado-candidato seleccionat)))
   =>
   (modify ?f (estado-candidato seleccionat)))

(defrule AVALUACIO::b0-proteccio-cultiu (declare (salience 3))
   (estado-soar (id S0) (fase avaluacio))
   ?f <- (operador-candidato (id ?c) (sector ?s) (accion orientar-ombra) (estado-candidato candidat))
   (not (preferencia (tipo-preferencia reject) (operador-referencia ?c)))
   (not (operador-candidato (sector ?s) (estado-candidato seleccionat)))
   =>
   (modify ?f (estado-candidato seleccionat)))

(defrule AVALUACIO::b0-produccio-energia (declare (salience 2))
   (estado-soar (id S0) (fase avaluacio))
   ?f <- (operador-candidato (id ?c) (sector ?s) (accion orientar-produccio) (estado-candidato candidat))
   (not (preferencia (tipo-preferencia reject) (operador-referencia ?c)))
   (not (operador-candidato (sector ?s) (estado-candidato seleccionat)))
   =>
   (modify ?f (estado-candidato seleccionat)))

(defrule AVALUACIO::b0-estabilitat (declare (salience 1))
   (estado-soar (id S0) (fase avaluacio))
   ?f <- (operador-candidato (sector ?s) (accion mantenir-posicio|diagnosticar) (estado-candidato candidat))
   (not (operador-candidato (sector ?s) (estado-candidato seleccionat)))
   =>
   (modify ?f (estado-candidato seleccionat)))

(defrule SELECCIO::descartar-resto
   (estado-soar (id S0) (fase seleccio))
   (operador-candidato (sector ?s) (estado-candidato seleccionat))
   ?f <- (operador-candidato (sector ?s) (estado-candidato candidat))
   =>
   (modify ?f (estado-candidato descartat)))
