;;; 05_avaluacio.clp: AVALUACIO. Restricciones duras (reject), valoración y preferencias better.

(defmodule AVALUACIO (import MAIN ?ALL))

;; SOAR: preferencia reject (restricción dura R1). Personas o maquinaria: no mover.
(defrule AVALUACIO::r1-personas
   (estado-soar (id S0) (fase avaluacio))
   (diagnostico (sector ?s) (tipo-diagnostico risc-persones))
   (operador-candidato (id ?c) (sector ?s) (accion ?a&:(not (accion-sin-movimiento ?a))))
   =>
   (assert (preferencia (sector ?s) (tipo-preferencia reject) (operador-referencia ?c)
                        (criterio seguretat-persones) (origen regla) (restriccion R1))))

;; SOAR: preferencia reject (restricción dura R2). Viento crítico: ni producción ni sombra.
(defrule AVALUACIO::r2-viento-critico
   (estado-soar (id S0) (fase avaluacio))
   (diagnostico (sector ?s) (tipo-diagnostico risc-mecanic) (nivel critic))
   (operador-candidato (id ?c) (sector ?s) (accion orientar-produccio|orientar-ombra))
   =>
   (assert (preferencia (sector ?s) (tipo-preferencia reject) (operador-referencia ?c)
                        (criterio integritat-mecanica) (origen regla) (restriccion R2))))

;; SOAR: preferencia reject (restricción dura R3). Actuador fallado ahora o en la última hora.
(defrule AVALUACIO::r3-actuador-fallado
   (estado-soar (id S0) (fase avaluacio))
   (ciclo-temporal (instante ?t))
   (operador-candidato (id ?c) (sector ?s) (accion ?a&:(not (accion-sin-movimiento ?a))))
   (test (fallada-reciente ?s ?t))
   =>
   (assert (preferencia (sector ?s) (tipo-preferencia reject) (operador-referencia ?c)
                        (criterio integritat-mecanica) (origen regla) (restriccion R3))))

;; SOAR: preferencia reject (restricción dura R4). Máximo de movimientos por hora, salvo ir a defensa.
(defrule AVALUACIO::r4-max-movimientos
   (estado-soar (id S0) (fase avaluacio))
   (ciclo-temporal (instante ?t))
   (operador-candidato (id ?c) (sector ?s) (accion ?a&~posicio-seguretat&:(not (accion-sin-movimiento ?a))))
   (sector (id ?s) (tiene-seguidor ?g))
   (seguidor-solar (id ?g) (max-movimientos-hora ?max))
   (test (>= (movimientos-recientes ?s ?t) ?max))
   =>
   (assert (preferencia (sector ?s) (tipo-preferencia reject) (operador-referencia ?c)
                        (criterio integritat-mecanica) (origen regla) (restriccion R4))))

;; SOAR: preferencia reject (restricción dura R5). No se sabe dónde está el panel: no mover.
(defrule AVALUACIO::r5-panel-desconocido
   (estado-soar (id S0) (fase avaluacio))
   (operador-candidato (id ?c) (sector ?s) (accion ?a&:(not (accion-sin-movimiento ?a))))
   (not (observacion-panel (sector ?s)))
   =>
   (assert (preferencia (sector ?s) (tipo-preferencia reject) (operador-referencia ?c)
                        (criterio seguretat-persones) (origen regla) (restriccion R5))))

;; SOAR: elaboración de operador (valoración). Beneficio de cada candidato en los tres criterios y
;; desplazamiento. Sin panel o sin un dato crítico no se valora: decide el impasse dades-insuficients.
(defrule AVALUACIO::valorar
   (estado-soar (id S0) (fase avaluacio))
   (operador-candidato (id ?c) (sector ?s) (accion ?a) (angulo-objetivo ?obj))
   (observacion-panel (sector ?s) (angulo-actual ?x))
   (not (diagnostico (sector ?s) (tipo-diagnostico incertesa-dades) (nivel critic)))
   =>
   (assert (valoracion (evalua-operador ?c) (desplazamiento (abs (- ?obj ?x)))
                       (beneficio-mecanico (beneficio ?s ?a posicio-seguretat))
                       (beneficio-cultivo (beneficio ?s ?a orientar-ombra))
                       (beneficio-energia (beneficio ?s ?a orientar-produccio)))))

;; Orden lexicográfico mecánico > cultivo > energía: en el primer criterio en que dos candidatos
;; difieren, el mayor es better si es alt o más. Si es mitja, la diferencia no es clara (zona gris):
;; no hay preferencia y no se miran los criterios siguientes.

;; SOAR: preferencia better (criterio mecánico).
(defrule AVALUACIO::preferir-mecanico
   (estado-soar (id S0) (fase avaluacio))
   (valoracion (evalua-operador ?a) (beneficio-mecanico ?ma&alt|critic))
   (operador-candidato (id ?a) (sector ?s))
   (operador-candidato (id ?b&~?a) (sector ?s))
   (valoracion (evalua-operador ?b) (beneficio-mecanico ?mb&:(> (nivel-num ?ma) (nivel-num ?mb))))
   =>
   (assert (preferencia (sector ?s) (tipo-preferencia better) (operador-referencia ?a)
                        (operador-comparado ?b) (criterio integritat-mecanica) (origen regla))))

;; SOAR: preferencia better (criterio cultivo, con el mecánico igual).
(defrule AVALUACIO::preferir-cultivo
   (estado-soar (id S0) (fase avaluacio))
   (valoracion (evalua-operador ?a) (beneficio-mecanico ?m) (beneficio-cultivo ?ca&alt|critic))
   (operador-candidato (id ?a) (sector ?s))
   (operador-candidato (id ?b&~?a) (sector ?s))
   (valoracion (evalua-operador ?b) (beneficio-mecanico ?m)
               (beneficio-cultivo ?cb&:(> (nivel-num ?ca) (nivel-num ?cb))))
   =>
   (assert (preferencia (sector ?s) (tipo-preferencia better) (operador-referencia ?a)
                        (operador-comparado ?b) (criterio proteccio-cultiu) (origen regla))))

;; SOAR: preferencia better (criterio energía, con el mecánico y el cultivo iguales).
(defrule AVALUACIO::preferir-energia
   (estado-soar (id S0) (fase avaluacio))
   (valoracion (evalua-operador ?a) (beneficio-mecanico ?m) (beneficio-cultivo ?k)
               (beneficio-energia ?ea&alt|critic))
   (operador-candidato (id ?a) (sector ?s))
   (operador-candidato (id ?b&~?a) (sector ?s))
   (valoracion (evalua-operador ?b) (beneficio-mecanico ?m) (beneficio-cultivo ?k)
               (beneficio-energia ?eb&:(> (nivel-num ?ea) (nivel-num ?eb))))
   =>
   (assert (preferencia (sector ?s) (tipo-preferencia better) (operador-referencia ?a)
                        (operador-comparado ?b) (criterio produccio-energia) (origen regla))))

;; SOAR: preferencia better (mínimo útil). Moverse con algún beneficio mitja o más es mejor que
;; quedarse quieto sin ningún beneficio.
(defrule AVALUACIO::preferir-util
   (estado-soar (id S0) (fase avaluacio))
   (operador-candidato (id ?a) (sector ?s) (accion ?x&:(not (accion-sin-movimiento ?x))))
   (valoracion (evalua-operador ?a) (beneficio-mecanico ?m) (beneficio-cultivo ?k) (beneficio-energia ?e))
   (test (>= (nivel-num (nivel-max ?m (nivel-max ?k ?e))) 1))
   (operador-candidato (id ?b) (sector ?s) (accion mantenir-posicio|diagnosticar))
   (valoracion (evalua-operador ?b) (beneficio-mecanico baix) (beneficio-cultivo baix) (beneficio-energia baix))
   =>
   (assert (preferencia (sector ?s) (tipo-preferencia better) (operador-referencia ?a)
                        (operador-comparado ?b) (origen regla)
                        (criterio (switch ?x (case posicio-seguretat then integritat-mecanica)
                                             (case orientar-ombra then proteccio-cultiu)
                                             (default produccio-energia))))))
