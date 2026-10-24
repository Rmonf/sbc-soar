;;; 02_monitoratge.clp: módulo MONITORATGE, verificación de las órdenes de t−1 (roadmap §5.2).
;;; I1: versión mínima, solo retira la orden anterior; la verificación del efecto
;;; (resultado del episodio y diagnóstico fallada-actuador) llega en I2.

(defmodule MONITORATGE (import MAIN ?ALL))

;; Retira la orden de un ciclo anterior, que Python ya ha leído (§3.2, §5.2).
(defrule MONITORATGE::retirar-orden-previa
   (estado-soar (id S0) (fase monitoratge))
   (ciclo-temporal (instante ?t))
   ?o <- (orden-actuador (instante ?i&:(< ?i ?t)))
   =>
   (retract ?o))
