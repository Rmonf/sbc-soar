;;; 11_neteja.clp: NETEJA. Limpia la memoria de trabajo para el ciclo siguiente. Conserva S0, el
;;; conocimiento estático, las órdenes del ciclo, los episodios de la última hora y los chunks.

(defmodule NETEJA (import MAIN ?ALL))

;; SOAR: retirada de los elementos efímeros de la memoria de trabajo al acabar el ciclo.
(defrule NETEJA::limpiar
   (estado-soar (id S0) (fase neteja))
   ?ct <- (ciclo-temporal (instante ?t))
   =>
   (do-for-all-facts ((?f observacion-sensor observacion-panel prediccion abstraccion diagnostico
                          operador-candidato valoracion preferencia impasse)) TRUE
      (retract ?f))
   (do-for-all-facts ((?f estado-soar)) (neq ?f:id S0) (retract ?f))
   (do-for-all-facts ((?f episodio)) (< ?f:instante (- ?t ?*ventana-episodica*)) (retract ?f))
   (retract ?ct))
