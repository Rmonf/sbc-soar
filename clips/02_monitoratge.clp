;;; 02_monitoratge.clp: módulo MONITORATGE, verificación de las órdenes de t−1 (roadmap §5.2).
;;; Con observacion-panel vigente del sector (instante = t), la orden con ángulo se verifica: dentro de la tolerancia,
;;; su episodio pasa a ok; fuera, a fallada-actuador, con el diagnóstico fallada-actuador alt.
;;; Una orden nil (no mover) o sin observación de panel deja el episodio pendent. En los tres
;;; casos la orden se retracta después; las reglas de retirada son mutuamente excluyentes y la
;;; de una orden verificada espera a que el episodio deje de estar pendent.

(defmodule MONITORATGE (import MAIN ?ALL))

;; El panel está donde se ordenó: el episodio de la orden pasa a ok (§5.2).
(defrule MONITORATGE::verificar-orden-ok
   (estado-soar (id S0) (fase monitoratge))
   (ciclo-temporal (instante ?t))
   (orden-actuador (sector ?s) (instante ?i&:(< ?i ?t)) (angulo-ordenado ?a&~nil))
   (observacion-panel (sector ?s) (angulo-actual ?x) (instante ?t))
   (sector (id ?s) (tiene-seguidor ?sg))
   (seguidor-solar (id ?sg) (tolerancia-angulo ?tol))
   (test (<= (abs (- ?x ?a)) ?tol))
   ?e <- (episodio (sector ?s) (instante ?i) (resultado pendent))
   =>
   (modify ?e (resultado ok))
   (printout traza "Resultat observat (t=" ?t "): sector=" ?s ", ordre t=" ?i ", angle=" ?x
                   ", ok" crlf))

;; El panel no está donde se ordenó: fallada-actuador en el episodio y diagnóstico alt, con
;; evidencia ordre-incomplerta si la orden movía o moviment-no-ordenat si no (§5.2).
(defrule MONITORATGE::verificar-orden-fallada
   (estado-soar (id S0) (fase monitoratge))
   (ciclo-temporal (instante ?t))
   (orden-actuador (sector ?s) (instante ?i&:(< ?i ?t)) (angulo-ordenado ?a&~nil))
   (observacion-panel (sector ?s) (angulo-actual ?x) (instante ?t))
   (sector (id ?s) (tiene-seguidor ?sg))
   (seguidor-solar (id ?sg) (tolerancia-angulo ?tol))
   (test (> (abs (- ?x ?a)) ?tol))
   ?e <- (episodio (sector ?s) (instante ?i) (resultado pendent) (angulo-previo ?previo))
   =>
   (modify ?e (resultado fallada-actuador))
   (assert (diagnostico (id (sym-cat ?s "-fallada-actuador")) (sector ?s)
                        (tipo-diagnostico fallada-actuador) (nivel alt)
                        (evidencias (if (> (abs (- ?a ?previo)) ?tol)
                                        then ordre-incomplerta else moviment-no-ordenat))))
   (printout traza "Resultat observat (t=" ?t "): sector=" ?s ", ordre t=" ?i ", angle=" ?x
                   ", fallada-actuador" crlf))

;; Orden verificada (episodio ok o fallada-actuador): se retracta (§5.2).
(defrule MONITORATGE::retirar-orden-verificada
   (estado-soar (id S0) (fase monitoratge))
   (ciclo-temporal (instante ?t))
   ?o <- (orden-actuador (sector ?s) (instante ?i&:(< ?i ?t)) (angulo-ordenado ~nil))
   (observacion-panel (sector ?s) (instante ?t))
   (episodio (sector ?s) (instante ?i) (resultado ~pendent))
   =>
   (retract ?o))

;; Orden nil (no mover): no hay ángulo que verificar, el episodio queda pendent (§5.2).
(defrule MONITORATGE::retirar-orden-sin-angulo
   (estado-soar (id S0) (fase monitoratge))
   (ciclo-temporal (instante ?t))
   ?o <- (orden-actuador (instante ?i&:(< ?i ?t)) (angulo-ordenado nil))
   =>
   (retract ?o))

;; Orden con ángulo sin observación de panel vigente: no se puede verificar, el episodio queda
;; pendent (§5.2).
(defrule MONITORATGE::retirar-orden-sin-panel
   (estado-soar (id S0) (fase monitoratge))
   (ciclo-temporal (instante ?t))
   ?o <- (orden-actuador (sector ?s) (instante ?i&:(< ?i ?t)) (angulo-ordenado ~nil))
   (not (observacion-panel (sector ?s) (instante ?t)))
   =>
   (retract ?o))
