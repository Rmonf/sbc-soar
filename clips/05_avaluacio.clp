;;; 05_avaluacio.clp: módulo AVALUACIO, restricciones, valoración y preferencias (roadmap §5.5).
;;; I1: R2, valoración de posicio-seguretat y de las acciones sin movimiento, acción útil
;;; (criterio mecánico) y estabilidad. Cada valoracion se aserta completa en una sola regla,
;;; sin modificaciones posteriores, para que ninguna preferencia vea una valoración a medias.

(defmodule AVALUACIO (import MAIN ?ALL))

;; R2: con riesgo mecánico crítico se requiere posicio-seguretat (§5.5a).
(defrule AVALUACIO::r2-requerir-seguretat
   (estado-soar (id S0) (fase avaluacio))
   (diagnostico (sector ?s) (tipo-diagnostico risc-mecanic) (nivel critic))
   (operador-candidato (id ?c) (sector ?s) (accion posicio-seguretat))
   =>
   (assert (preferencia (en-estado S0) (sector ?s) (tipo-preferencia require)
                        (operador-referencia ?c) (criterio integritat-mecanica)
                        (origen regla) (restriccion R2))))

;; Valoración de posicio-seguretat: Δ, coste según el umbral moviment y beneficio mecánico
;; igual al riesgo salvo que el coste sea baix (§5.5b).
(defrule AVALUACIO::valorar-posicio-seguretat
   (estado-soar (id S0) (fase avaluacio))
   (operador-candidato (id ?c) (sector ?s) (accion posicio-seguretat) (angulo-objetivo ?obj))
   (observacion-panel (sector ?s) (angulo-actual ?act))
   (diagnostico (sector ?s) (tipo-diagnostico risc-mecanic) (nivel ?riesgo))
   (umbral (variable moviment) (nivel ?coste) (limite-inferior ?inf) (limite-superior ?sup))
   (test (dins-interval (abs (- ?obj ?act)) ?inf ?sup))
   =>
   (assert (valoracion (evalua-operador ?c)
                       (beneficio-mecanico (if (eq ?coste baix) then baix else ?riesgo))
                       (beneficio-cultivo baix) (beneficio-energia baix)
                       (coste-movimiento ?coste) (desplazamiento (abs (- ?obj ?act))))))

;; Valoración de una acción sin movimiento: Δ = 0 y, por tanto, todos los beneficios baix (§5.5b).
(defrule AVALUACIO::valorar-sin-movimiento
   (estado-soar (id S0) (fase avaluacio))
   (operador-candidato (id ?c) (accion ?a&:(accion-sin-movimiento ?a)))
   (umbral (variable moviment) (nivel ?coste) (limite-inferior ?inf) (limite-superior ?sup))
   (test (dins-interval 0 ?inf ?sup))
   =>
   (assert (valoracion (evalua-operador ?c) (beneficio-mecanico baix) (beneficio-cultivo baix)
                       (beneficio-energia baix) (coste-movimiento ?coste) (desplazamiento 0.0))))

;; Acción útil: un candidato que mueve con beneficio mecánico ≥ mitja es mejor que la acción
;; sin movimiento, con criterio integritat-mecanica (§5.5c.3; en I1 solo el criterio mecánico).
(defrule AVALUACIO::preferir-accion-util
   (estado-soar (id S0) (fase avaluacio))
   (operador-candidato (id ?c) (sector ?s) (accion ?a&:(not (accion-sin-movimiento ?a))))
   (valoracion (evalua-operador ?c)
               (beneficio-mecanico ?b&:(>= (nivel-num ?b) (nivel-num mitja))))
   (operador-candidato (id ?q) (sector ?s) (accion ?aq&:(accion-sin-movimiento ?aq)))
   =>
   (assert (preferencia (en-estado S0) (sector ?s) (tipo-preferencia better)
                        (operador-referencia ?c) (operador-comparado ?q)
                        (criterio integritat-mecanica) (origen regla))))

;; Estabilidad: con los tres beneficios iguales y Δ que difieren más que la tolerancia,
;; es mejor el de menor Δ (§5.5c.2).
(defrule AVALUACIO::preferir-estabilidad
   (estado-soar (id S0) (fase avaluacio))
   (operador-candidato (id ?c) (sector ?s))
   (operador-candidato (id ?q&~?c) (sector ?s))
   (sector (id ?s) (tiene-seguidor ?sg))
   (seguidor-solar (id ?sg) (tolerancia-angulo ?tol))
   (valoracion (evalua-operador ?c) (beneficio-mecanico ?m) (beneficio-cultivo ?cu)
               (beneficio-energia ?e) (desplazamiento ?dc))
   (valoracion (evalua-operador ?q) (beneficio-mecanico ?m) (beneficio-cultivo ?cu)
               (beneficio-energia ?e) (desplazamiento ?dq&:(> (- ?dq ?dc) ?tol)))
   =>
   (assert (preferencia (en-estado S0) (sector ?s) (tipo-preferencia better)
                        (operador-referencia ?c) (operador-comparado ?q)
                        (criterio estabilitat) (origen regla))))
