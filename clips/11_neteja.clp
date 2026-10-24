;;; 11_neteja.clp: módulo NETEJA, limpieza explícita de la memoria de trabajo (roadmap §5.11).
;;; I1: familias 1, 2 y 4. Conserva S0, el conocimiento estático, las órdenes del ciclo y
;;; los episodios. La retirada de episodios de más de 60 min (y de impasses y subestados)
;;; llega en I2.

(defmodule NETEJA (import MAIN ?ALL))

;; Retira el ciclo-temporal: S0 queda en espera hasta el siguiente (§5.11).
(defrule NETEJA::retirar-ciclo-temporal
   (estado-soar (id S0) (fase neteja))
   ?h <- (ciclo-temporal)
   =>
   (retract ?h))

;; Retira las observaciones de sensores (familia 1, §5.11).
(defrule NETEJA::retirar-observacion-sensor
   (estado-soar (id S0) (fase neteja))
   ?h <- (observacion-sensor)
   =>
   (retract ?h))

;; Retira las observaciones de panel (familia 1, §5.11).
(defrule NETEJA::retirar-observacion-panel
   (estado-soar (id S0) (fase neteja))
   ?h <- (observacion-panel)
   =>
   (retract ?h))

;; Retira las abstracciones (familia 2, §5.11).
(defrule NETEJA::retirar-abstraccion
   (estado-soar (id S0) (fase neteja))
   ?h <- (abstraccion)
   =>
   (retract ?h))

;; Retira los diagnósticos (familia 2, §5.11).
(defrule NETEJA::retirar-diagnostico
   (estado-soar (id S0) (fase neteja))
   ?h <- (diagnostico)
   =>
   (retract ?h))

;; Retira los candidatos (familia 4, §5.11).
(defrule NETEJA::retirar-operador-candidato
   (estado-soar (id S0) (fase neteja))
   ?h <- (operador-candidato)
   =>
   (retract ?h))

;; Retira las valoraciones (familia 4, §5.11).
(defrule NETEJA::retirar-valoracion
   (estado-soar (id S0) (fase neteja))
   ?h <- (valoracion)
   =>
   (retract ?h))

;; Retira las preferencias (familia 4, §5.11).
(defrule NETEJA::retirar-preferencia
   (estado-soar (id S0) (fase neteja))
   ?h <- (preferencia)
   =>
   (retract ?h))
