;;; 05_avaluacio.clp: módulo AVALUACIO, restricciones, valoración y preferencias (roadmap §5.5).
;;; Cada valoracion se aserta completa en una sola regla, sin modificaciones posteriores, para
;;; que ninguna preferencia vea una valoración a medias. Por el invariante de §5.5b, cada acción
;;; solo tiene beneficio en su propio criterio.
;;; Pendiente en I2: R1, R3, R4, R5 y el reject de R2 a orientar-* llegan en P3.

(defmodule AVALUACIO (import MAIN ?ALL))

;; Beneficio de una acción en un criterio: el nivel de lo que la motiva en el sector si es su
;; propio criterio, baix si no (§5.5b).
(deffunction AVALUACIO::beneficio (?accion ?criterio ?sector)
   (switch ?criterio
      (case mecanico then
         (if (eq ?accion posicio-seguretat) then (nivel-diagnostico ?sector risc-mecanic) else baix))
      (case cultivo then
         (if (eq ?accion orientar-ombra)
             then (nivel-max (nivel-diagnostico ?sector estres-termic)
                             (nivel-diagnostico ?sector estres-hidric))
             else baix))
      (case energia then
         (if (eq ?accion orientar-produccio)
             then (nivel-diagnostico ?sector oportunitat-energetica) else baix))))

;; Objetivo de mayor prioridad (objetivo-activo) entre los que sirve una valoración con
;; beneficio ≥ mitja (§5.5c.3).
(deffunction AVALUACIO::criterio-servido (?mecanico ?cultivo ?energia)
   (bind ?mejor nil)
   (bind ?prioridad 0)
   (foreach ?par (create$ integritat-mecanica ?mecanico proteccio-cultiu ?cultivo produccio-energia ?energia)
      (if (= (mod ?par-index 2) 1) then (bind ?objetivo ?par)
       else (if (>= (nivel-num ?par) (nivel-num mitja)) then
               (bind ?p (fact-slot-value
                           (nth$ 1 (find-fact ((?o objetivo-activo)) (eq ?o:nombre-objetivo ?objetivo)))
                           prioridad))
               (if (or (eq ?mejor nil) (< ?p ?prioridad)) then
                  (bind ?mejor ?objetivo)
                  (bind ?prioridad ?p)))))
   ?mejor)

;;; --- (a) Restricciones duras (§5.5a) ----------------------------------------

;; R2: con riesgo mecánico crítico se requiere posicio-seguretat (§5.5a).
(defrule AVALUACIO::r2-requerir-seguretat
   (estado-soar (id S0) (fase avaluacio))
   (diagnostico (sector ?s) (tipo-diagnostico risc-mecanic) (nivel critic))
   (operador-candidato (id ?c) (sector ?s) (accion posicio-seguretat))
   =>
   (assert (preferencia (en-estado S0) (sector ?s) (tipo-preferencia require)
                        (operador-referencia ?c) (criterio integritat-mecanica)
                        (origen regla) (restriccion R2))))

;;; --- (b) Valoración (§5.5b) -------------------------------------------------

;; Valoración de un candidato que no es acción sin movimiento, con panel observado: Δ, coste
;; según el umbral moviment y beneficio en su propio criterio, todo baix si el coste es baix.
(defrule AVALUACIO::valorar-candidato
   (estado-soar (id S0) (fase avaluacio))
   (operador-candidato (id ?c) (sector ?s) (accion ?a&:(not (accion-sin-movimiento ?a)))
                       (angulo-objetivo ?obj))
   (observacion-panel (sector ?s) (angulo-actual ?act))
   (umbral (variable moviment) (nivel ?coste) (limite-inferior ?inf) (limite-superior ?sup))
   (test (dins-interval (abs (- ?obj ?act)) ?inf ?sup))
   =>
   (bind ?util (neq ?coste baix))
   (assert (valoracion (evalua-operador ?c)
                       (beneficio-mecanico (if ?util then (beneficio ?a mecanico ?s) else baix))
                       (beneficio-cultivo (if ?util then (beneficio ?a cultivo ?s) else baix))
                       (beneficio-energia (if ?util then (beneficio ?a energia ?s) else baix))
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

;;; --- (c) Preferencias blandas (§5.5c) ---------------------------------------

;; Criterio mecánico entre dos candidatos que mueven: si difieren y el mayor es ≥ alt, better
;; el mayor; si el mayor es mitja, zona gris (§5.5c.1).
(defrule AVALUACIO::preferir-por-mecanico
   (estado-soar (id S0) (fase avaluacio))
   (operador-candidato (id ?c) (sector ?s) (accion ?a&:(not (accion-sin-movimiento ?a))))
   (operador-candidato (id ?q&~?c) (sector ?s) (accion ?aq&:(not (accion-sin-movimiento ?aq))))
   (valoracion (evalua-operador ?c) (beneficio-mecanico ?mc&:(>= (nivel-num ?mc) (nivel-num alt))))
   (valoracion (evalua-operador ?q) (beneficio-mecanico ?mq&:(< (nivel-num ?mq) (nivel-num ?mc))))
   =>
   (assert (preferencia (en-estado S0) (sector ?s) (tipo-preferencia better)
                        (operador-referencia ?c) (operador-comparado ?q)
                        (criterio integritat-mecanica) (origen regla))))

;; Criterio de cultivo, con el mecánico igual (§5.5c.1).
(defrule AVALUACIO::preferir-por-cultivo
   (estado-soar (id S0) (fase avaluacio))
   (operador-candidato (id ?c) (sector ?s) (accion ?a&:(not (accion-sin-movimiento ?a))))
   (operador-candidato (id ?q&~?c) (sector ?s) (accion ?aq&:(not (accion-sin-movimiento ?aq))))
   (valoracion (evalua-operador ?c) (beneficio-mecanico ?m)
               (beneficio-cultivo ?cc&:(>= (nivel-num ?cc) (nivel-num alt))))
   (valoracion (evalua-operador ?q) (beneficio-mecanico ?m)
               (beneficio-cultivo ?cq&:(< (nivel-num ?cq) (nivel-num ?cc))))
   =>
   (assert (preferencia (en-estado S0) (sector ?s) (tipo-preferencia better)
                        (operador-referencia ?c) (operador-comparado ?q)
                        (criterio proteccio-cultiu) (origen regla))))

;; Criterio de energía, con el mecánico y el de cultivo iguales (§5.5c.1).
(defrule AVALUACIO::preferir-por-energia
   (estado-soar (id S0) (fase avaluacio))
   (operador-candidato (id ?c) (sector ?s) (accion ?a&:(not (accion-sin-movimiento ?a))))
   (operador-candidato (id ?q&~?c) (sector ?s) (accion ?aq&:(not (accion-sin-movimiento ?aq))))
   (valoracion (evalua-operador ?c) (beneficio-mecanico ?m) (beneficio-cultivo ?cu)
               (beneficio-energia ?ec&:(>= (nivel-num ?ec) (nivel-num alt))))
   (valoracion (evalua-operador ?q) (beneficio-mecanico ?m) (beneficio-cultivo ?cu)
               (beneficio-energia ?eq&:(< (nivel-num ?eq) (nivel-num ?ec))))
   =>
   (assert (preferencia (en-estado S0) (sector ?s) (tipo-preferencia better)
                        (operador-referencia ?c) (operador-comparado ?q)
                        (criterio produccio-energia) (origen regla))))

;; Acción útil: un candidato que mueve con algún beneficio ≥ mitja es mejor que la acción sin
;; movimiento, con el objetivo de mayor prioridad que sirve (§5.5c.3).
(defrule AVALUACIO::preferir-accion-util
   (estado-soar (id S0) (fase avaluacio))
   (operador-candidato (id ?c) (sector ?s) (accion ?a&:(not (accion-sin-movimiento ?a))))
   (valoracion (evalua-operador ?c) (beneficio-mecanico ?m) (beneficio-cultivo ?cu)
               (beneficio-energia ?e))
   (test (neq (criterio-servido ?m ?cu ?e) nil))
   (operador-candidato (id ?q) (sector ?s) (accion ?aq&:(accion-sin-movimiento ?aq)))
   =>
   (assert (preferencia (en-estado S0) (sector ?s) (tipo-preferencia better)
                        (operador-referencia ?c) (operador-comparado ?q)
                        (criterio (criterio-servido ?m ?cu ?e)) (origen regla))))

;; Estabilidad: con los tres beneficios iguales y Δ que difieren más que la tolerancia,
;; es mejor el de menor Δ (§5.5c.2, primer punto).
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

;; Estabilidad: con los tres beneficios iguales y Δ dentro de la tolerancia, la acción sin
;; movimiento es mejor que la que mueve (§5.5c.2, segundo punto).
(defrule AVALUACIO::preferir-sin-movimiento-estable
   (estado-soar (id S0) (fase avaluacio))
   (operador-candidato (id ?q) (sector ?s) (accion ?aq&:(accion-sin-movimiento ?aq)))
   (operador-candidato (id ?c) (sector ?s) (accion ?a&:(not (accion-sin-movimiento ?a))))
   (sector (id ?s) (tiene-seguidor ?sg))
   (seguidor-solar (id ?sg) (tolerancia-angulo ?tol))
   (valoracion (evalua-operador ?q) (beneficio-mecanico ?m) (beneficio-cultivo ?cu)
               (beneficio-energia ?e) (desplazamiento ?dq))
   (valoracion (evalua-operador ?c) (beneficio-mecanico ?m) (beneficio-cultivo ?cu)
               (beneficio-energia ?e) (desplazamiento ?dc&:(<= (abs (- ?dc ?dq)) ?tol)))
   =>
   (assert (preferencia (en-estado S0) (sector ?s) (tipo-preferencia better)
                        (operador-referencia ?q) (operador-comparado ?c)
                        (criterio estabilitat) (origen regla))))
