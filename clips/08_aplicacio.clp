;;; 08_aplicacio.clp: módulo APLICACIO, orden al actuador (roadmap §5.8).
;;; I1: sin impasses, escalado-humano es siempre FALSE; la regla del escalado llega en I2.

(defmodule APLICACIO (import MAIN ?ALL))

;; El seleccionado genera la orden-actuador (ángulo = angulo-objetivo) y pasa a aplicat (§5.8).
(defrule APLICACIO::aplicar-seleccionado
   (estado-soar (id S0) (fase aplicacio))
   (ciclo-temporal (instante ?t))
   ?f <- (operador-candidato (sector ?s) (accion ?a) (angulo-objetivo ?ang)
                             (estado-candidato seleccionat))
   =>
   (assert (orden-actuador (id (sym-cat orden- ?s "-" ?t)) (sector ?s) (accion ?a)
                           (angulo-ordenado ?ang) (instante ?t) (escalado-humano FALSE)))
   (modify ?f (estado-candidato aplicat)))
