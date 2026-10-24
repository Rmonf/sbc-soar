;;; 08_aplicacio.clp: módulo APLICACIO, orden al actuador (roadmap §5.8).
;;; escalado-humano es TRUE si el sector tuvo un impasse constraint-failure o uno cerrado como
;;; escalat: la decisión se deriva a una persona (enunciado 3.7.3).

(defmodule APLICACIO (import MAIN ?ALL))

;; ¿Se deriva a una persona la decisión del sector? (§5.8). Los impasses no cambian en APLICACIO.
(deffunction APLICACIO::escalado (?sector)
   (if (> (length$ (find-fact ((?i impasse))
                      (and (eq ?i:sector ?sector)
                           (or (eq ?i:tipo-impasse constraint-failure)
                               (eq ?i:estrategia-resolucion escalat)))))
          0)
      then TRUE else FALSE))

;; El seleccionado genera la orden-actuador (ángulo = angulo-objetivo) y pasa a aplicat (§5.8).
(defrule APLICACIO::aplicar-seleccionado
   (estado-soar (id S0) (fase aplicacio))
   (ciclo-temporal (instante ?t))
   ?f <- (operador-candidato (sector ?s) (accion ?a) (angulo-objetivo ?ang)
                             (estado-candidato seleccionat))
   =>
   (assert (orden-actuador (id (sym-cat orden- ?s "-" ?t)) (sector ?s) (accion ?a)
                           (angulo-ordenado ?ang) (instante ?t) (escalado-humano (escalado ?s))))
   (modify ?f (estado-candidato aplicat)))
