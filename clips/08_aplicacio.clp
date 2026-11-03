;;; 08_aplicacio.clp: APLICACIO. El operador seleccionado crea la orden para los paneles.

(defmodule APLICACIO (import MAIN ?ALL))

;; SOAR: aplicación de operador (salida). La orden lleva el ángulo del candidato; se escala a una
;; persona si el sector tuvo un impasse dades-insuficients (la decisión pide inspección).
(defrule APLICACIO::aplicar
   (estado-soar (id S0) (fase aplicacio))
   (ciclo-temporal (instante ?t))
   ?c <- (operador-candidato (sector ?s) (accion ?a) (angulo-objetivo ?ang) (estado-candidato seleccionat))
   =>
   (assert (orden-actuador (sector ?s) (accion ?a) (angulo-ordenado ?ang) (instante ?t)
                           (escalado-humano (any-factp ((?i impasse)) (and (eq ?i:sector ?s)
                                                        (eq ?i:tipo-impasse dades-insuficients))))))
   (modify ?c (estado-candidato aplicat)))
