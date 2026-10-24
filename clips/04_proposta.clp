;;; 04_proposta.clp: módulo PROPOSTA, creación de operadores candidatos (roadmap §5.4).
;;; I1: posicio-seguretat y mantenir-posicio. Los ids salen del sector y la acción
;;; (un candidato por acción y sector en cada ciclo), no del orden de disparo.

(defmodule PROPOSTA (import MAIN ?ALL))

;; Riesgo mecánico ≥ alt: se propone ir al ángulo de defensa del seguidor (§5.4).
(defrule PROPOSTA::proponer-posicio-seguretat
   (estado-soar (id S0) (fase proposta))
   (diagnostico (sector ?s) (tipo-diagnostico risc-mecanic)
                (nivel ?n&:(>= (nivel-num ?n) (nivel-num alt))))
   (sector (id ?s) (tiene-seguidor ?sg))
   (seguidor-solar (id ?sg) (angulo-defensa-viento ?a))
   =>
   (assert (operador-candidato (id (sym-cat ?s "-posicio-seguretat")) (en-estado S0) (sector ?s)
                               (accion posicio-seguretat) (angulo-objetivo ?a)
                               (estado-candidato candidat)
                               (motivos (sym-cat risc-mecanic ":" ?n)))))

;; Sin incertidumbre ≥ mitja ni fallada del actuador: se propone mantener el ángulo actual (§5.4).
(defrule PROPOSTA::proponer-mantenir-posicio
   (estado-soar (id S0) (fase proposta))
   (observacion-panel (sector ?s) (angulo-actual ?a))
   (not (diagnostico (sector ?s) (tipo-diagnostico incertesa-dades)
                     (nivel ?n&:(>= (nivel-num ?n) (nivel-num mitja)))))
   (not (diagnostico (sector ?s) (tipo-diagnostico fallada-actuador)))
   =>
   (assert (operador-candidato (id (sym-cat ?s "-mantenir-posicio")) (en-estado S0) (sector ?s)
                               (accion mantenir-posicio) (angulo-objetivo ?a)
                               (estado-candidato candidat))))
