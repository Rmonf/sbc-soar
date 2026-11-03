;;; 02_monitoratge.clp: MONITORATGE. Comprueba si la orden del ciclo anterior se cumplió,
;;; anota el resultado en su episodio y retracta la orden.

(defmodule MONITORATGE (import MAIN ?ALL))

;; SOAR: monitorización del efecto. El panel llegó al ángulo ordenado: episodio ok.
(defrule MONITORATGE::orden-cumplida
   (estado-soar (id S0) (fase monitoratge))
   ?o <- (orden-actuador (sector ?s) (instante ?i) (angulo-ordenado ?a&~nil))
   (observacion-panel (sector ?s) (angulo-actual ?x))
   (sector (id ?s) (tiene-seguidor ?g))
   (seguidor-solar (id ?g) (tolerancia-angulo ?tol&:(<= (abs (- ?x ?a)) ?tol)))
   ?e <- (episodio (sector ?s) (instante ?i))
   =>
   (retract ?o)
   (modify ?e (resultado ok))
   (printout traza "Monitoratge: " ?s ", ordre de t=" ?i " complerta (angle " ?x ")" crlf))

;; SOAR: monitorización del efecto. El panel no llegó: episodio y diagnóstico de fallo del actuador.
(defrule MONITORATGE::orden-fallada
   (estado-soar (id S0) (fase monitoratge))
   ?o <- (orden-actuador (sector ?s) (instante ?i) (angulo-ordenado ?a&~nil))
   (observacion-panel (sector ?s) (angulo-actual ?x))
   (sector (id ?s) (tiene-seguidor ?g))
   (seguidor-solar (id ?g) (tolerancia-angulo ?tol&:(> (abs (- ?x ?a)) ?tol)))
   ?e <- (episodio (sector ?s) (instante ?i))
   =>
   (retract ?o)
   (modify ?e (resultado fallada-actuador))
   (assert (diagnostico (sector ?s) (tipo-diagnostico fallada-actuador) (nivel alt)
                        (evidencias ordre-incomplerta)))
   (printout traza "Monitoratge: " ?s ", ordre de t=" ?i " NO complerta (ordenat " ?a
                   ", observat " ?x ")" crlf))

;; SOAR: monitorización del efecto. Orden sin ángulo o sin panel: no se puede verificar (pendent).
(defrule MONITORATGE::orden-sin-verificar
   (estado-soar (id S0) (fase monitoratge))
   ?o <- (orden-actuador (sector ?s) (angulo-ordenado ?a))
   (or (test (eq ?a nil)) (not (observacion-panel (sector ?s))))
   =>
   (retract ?o))
