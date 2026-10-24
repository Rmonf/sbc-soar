;;; 05_avaluacio.clp: módulo AVALUACIO, restricciones, valoración y preferencias (roadmap §5.5).
;;; Cada valoracion se aserta completa en una sola regla, sin modificaciones posteriores, para
;;; que ninguna preferencia vea una valoración a medias. Cada acción que mueve solo tiene
;;; beneficio en su propio criterio; la acción sin movimiento hereda los beneficios de los
;;; candidatos que la posición actual ya sirve (coste baix, §5.5b).
;;; Las restricciones no rechazan nunca una acción sin movimiento, así que nunca quedan todos
;;; los candidatos rechazados (§5.5a).

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

;; Nivel de coste de un desplazamiento según el umbral moviment (§5.5b).
(deffunction AVALUACIO::coste-de (?delta)
   (fact-slot-value
      (nth$ 1 (find-fact ((?u umbral))
                 (and (eq ?u:variable moviment) (dins-interval ?delta ?u:limite-inferior ?u:limite-superior))))
      nivel))

;; Beneficio que hereda la acción sin movimiento en un criterio: el mayor beneficio propio de
;; los candidatos que mueven con coste baix desde el panel vigente, porque la posición actual
;; ya los sirve; baix sin panel vigente (§5.5b). Candidatos y diagnósticos no cambian aquí.
(deffunction AVALUACIO::beneficio-heredado (?criterio ?sector)
   (bind ?actual (angulo-observado ?sector))
   (bind ?nivel baix)
   (if (eq ?actual nil) then (return ?nivel))
   (do-for-all-facts ((?c operador-candidato))
         (and (eq ?c:sector ?sector) (not (accion-sin-movimiento ?c:accion))
              (eq (coste-de (abs (- ?c:angulo-objetivo ?actual))) baix))
      (bind ?nivel (nivel-max ?nivel (beneficio ?c:accion ?criterio ?sector))))
   ?nivel)

;;; --- (a) Restricciones duras (§5.5a) ----------------------------------------

;; R1: con personas o maquinaria debajo, se rechaza todo candidato que mueva (§5.5a).
(defrule AVALUACIO::r1-rechazar-con-personas
   (estado-soar (id S0) (fase avaluacio))
   (diagnostico (sector ?s) (tipo-diagnostico risc-persones))
   (operador-candidato (id ?c) (sector ?s) (accion ?a) (angulo-objetivo ?o))
   (test (candidato-mueve ?a ?o ?s))
   =>
   (assert (preferencia (en-estado S0) (sector ?s) (tipo-preferencia reject)
                        (operador-referencia ?c) (criterio seguretat-persones)
                        (origen regla) (restriccion R1))))

;; R2: con riesgo mecánico crítico, se rechazan orientar-produccio y orientar-ombra (§5.5a).
(defrule AVALUACIO::r2-rechazar-orientar
   (estado-soar (id S0) (fase avaluacio))
   (diagnostico (sector ?s) (tipo-diagnostico risc-mecanic) (nivel critic))
   (operador-candidato (id ?c) (sector ?s) (accion orientar-produccio|orientar-ombra))
   =>
   (assert (preferencia (en-estado S0) (sector ?s) (tipo-preferencia reject)
                        (operador-referencia ?c) (criterio integritat-mecanica)
                        (origen regla) (restriccion R2))))

;; R3: con fallada del actuador, se rechaza todo candidato que mueva (§5.5a).
(defrule AVALUACIO::r3-rechazar-con-fallada
   (estado-soar (id S0) (fase avaluacio))
   (diagnostico (sector ?s) (tipo-diagnostico fallada-actuador))
   (operador-candidato (id ?c) (sector ?s) (accion ?a) (angulo-objetivo ?o))
   (test (candidato-mueve ?a ?o ?s))
   =>
   (assert (preferencia (en-estado S0) (sector ?s) (tipo-preferencia reject)
                        (operador-referencia ?c) (criterio integritat-mecanica)
                        (origen regla) (restriccion R3))))

;; R4: con max-movimientos-hora movimientos en la última hora (memoria episódica), se rechaza
;; todo candidato que mueva excepto posicio-seguretat (§5.5a, enunciado 3.6).
(defrule AVALUACIO::r4-rechazar-por-desgaste
   (estado-soar (id S0) (fase avaluacio))
   (ciclo-temporal (instante ?t))
   (sector (id ?s) (tiene-seguidor ?sg))
   (seguidor-solar (id ?sg) (max-movimientos-hora ?max))
   (test (>= (movimientos-recientes ?s ?t) ?max))
   (operador-candidato (id ?c) (sector ?s) (accion ?a&~posicio-seguretat) (angulo-objetivo ?o))
   (test (candidato-mueve ?a ?o ?s))
   =>
   (assert (preferencia (en-estado S0) (sector ?s) (tipo-preferencia reject)
                        (operador-referencia ?c) (criterio integritat-mecanica)
                        (origen regla) (restriccion R4))))

;; R5: sin observacion-panel vigente (ausente o antigua), se rechaza todo candidato que mueva
;; (Δ desconocido) (§5.5a).
(defrule AVALUACIO::r5-rechazar-sin-panel
   (estado-soar (id S0) (fase avaluacio))
   (ciclo-temporal (instante ?t))
   (sector (id ?s))
   (not (observacion-panel (sector ?s) (instante ?t)))
   (operador-candidato (id ?c) (sector ?s) (accion ?a) (angulo-objetivo ?o))
   (test (candidato-mueve ?a ?o ?s))
   =>
   (assert (preferencia (en-estado S0) (sector ?s) (tipo-preferencia reject)
                        (operador-referencia ?c) (criterio seguretat-persones)
                        (origen regla) (restriccion R5))))

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
   (ciclo-temporal (instante ?t))
   (observacion-panel (sector ?s) (angulo-actual ?act) (instante ?t))
   (umbral (variable moviment) (nivel ?coste) (limite-inferior ?inf) (limite-superior ?sup))
   (test (dins-interval (abs (- ?obj ?act)) ?inf ?sup))
   =>
   (bind ?util (neq ?coste baix))
   (assert (valoracion (evalua-operador ?c)
                       (beneficio-mecanico (if ?util then (beneficio ?a mecanico ?s) else baix))
                       (beneficio-cultivo (if ?util then (beneficio ?a cultivo ?s) else baix))
                       (beneficio-energia (if ?util then (beneficio ?a energia ?s) else baix))
                       (coste-movimiento ?coste) (desplazamiento (abs (- ?obj ?act))))))

;; Valoración de una acción sin movimiento: Δ = 0 y los beneficios heredados de los candidatos
;; que la posición actual ya sirve (§5.5b).
(defrule AVALUACIO::valorar-sin-movimiento
   (estado-soar (id S0) (fase avaluacio))
   (operador-candidato (id ?c) (sector ?s) (accion ?a&:(accion-sin-movimiento ?a)))
   (umbral (variable moviment) (nivel ?coste) (limite-inferior ?inf) (limite-superior ?sup))
   (test (dins-interval 0 ?inf ?sup))
   =>
   (assert (valoracion (evalua-operador ?c) (beneficio-mecanico (beneficio-heredado mecanico ?s))
                       (beneficio-cultivo (beneficio-heredado cultivo ?s))
                       (beneficio-energia (beneficio-heredado energia ?s))
                       (coste-movimiento ?coste) (desplazamiento 0.0))))

;;; --- (c) Preferencias blandas (§5.5c) ---------------------------------------

;; Criterio mecánico entre dos candidatos cualesquiera: si difieren y el mayor es ≥ alt, better
;; el mayor; si el mayor es mitja, zona gris (§5.5c.1).
(defrule AVALUACIO::preferir-por-mecanico
   (estado-soar (id S0) (fase avaluacio))
   (operador-candidato (id ?c) (sector ?s))
   (operador-candidato (id ?q&~?c) (sector ?s))
   (valoracion (evalua-operador ?c) (beneficio-mecanico ?mc&:(>= (nivel-num ?mc) (nivel-num alt))))
   (valoracion (evalua-operador ?q) (beneficio-mecanico ?mq&:(< (nivel-num ?mq) (nivel-num ?mc))))
   =>
   (assert (preferencia (en-estado S0) (sector ?s) (tipo-preferencia better)
                        (operador-referencia ?c) (operador-comparado ?q)
                        (criterio integritat-mecanica) (origen regla))))

;; Criterio de cultivo entre dos candidatos cualesquiera, con el mecánico igual (§5.5c.1).
(defrule AVALUACIO::preferir-por-cultivo
   (estado-soar (id S0) (fase avaluacio))
   (operador-candidato (id ?c) (sector ?s))
   (operador-candidato (id ?q&~?c) (sector ?s))
   (valoracion (evalua-operador ?c) (beneficio-mecanico ?m)
               (beneficio-cultivo ?cc&:(>= (nivel-num ?cc) (nivel-num alt))))
   (valoracion (evalua-operador ?q) (beneficio-mecanico ?m)
               (beneficio-cultivo ?cq&:(< (nivel-num ?cq) (nivel-num ?cc))))
   =>
   (assert (preferencia (en-estado S0) (sector ?s) (tipo-preferencia better)
                        (operador-referencia ?c) (operador-comparado ?q)
                        (criterio proteccio-cultiu) (origen regla))))

;; Criterio de energía entre dos candidatos cualesquiera, con el mecánico y el de cultivo
;; iguales (§5.5c.1).
(defrule AVALUACIO::preferir-por-energia
   (estado-soar (id S0) (fase avaluacio))
   (operador-candidato (id ?c) (sector ?s))
   (operador-candidato (id ?q&~?c) (sector ?s))
   (valoracion (evalua-operador ?c) (beneficio-mecanico ?m) (beneficio-cultivo ?cu)
               (beneficio-energia ?ec&:(>= (nivel-num ?ec) (nivel-num alt))))
   (valoracion (evalua-operador ?q) (beneficio-mecanico ?m) (beneficio-cultivo ?cu)
               (beneficio-energia ?eq&:(< (nivel-num ?eq) (nivel-num ?ec))))
   =>
   (assert (preferencia (en-estado S0) (sector ?s) (tipo-preferencia better)
                        (operador-referencia ?c) (operador-comparado ?q)
                        (criterio produccio-energia) (origen regla))))

;; Acción útil: un candidato que mueve con algún beneficio ≥ mitja es mejor que la acción sin
;; movimiento si esta no hereda ningún beneficio, con el objetivo de mayor prioridad que sirve
;; (§5.5c.3).
(defrule AVALUACIO::preferir-accion-util
   (estado-soar (id S0) (fase avaluacio))
   (operador-candidato (id ?c) (sector ?s) (accion ?a&:(not (accion-sin-movimiento ?a))))
   (valoracion (evalua-operador ?c) (beneficio-mecanico ?m) (beneficio-cultivo ?cu)
               (beneficio-energia ?e))
   (test (neq (criterio-servido ?m ?cu ?e) nil))
   (operador-candidato (id ?q) (sector ?s) (accion ?aq&:(accion-sin-movimiento ?aq)))
   (valoracion (evalua-operador ?q) (beneficio-mecanico baix) (beneficio-cultivo baix)
               (beneficio-energia baix))
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

;; Cercanía: la acción sin movimiento es mejor que un candidato que mueve con coste baix, cuyo
;; objetivo la posición actual ya sirve (§5.5c.2, tercer punto).
(defrule AVALUACIO::preferir-sin-movimiento-cercano
   (estado-soar (id S0) (fase avaluacio))
   (operador-candidato (id ?q) (sector ?s) (accion ?aq&:(accion-sin-movimiento ?aq)))
   (operador-candidato (id ?c) (sector ?s) (accion ?a&:(not (accion-sin-movimiento ?a))))
   (valoracion (evalua-operador ?q))
   (valoracion (evalua-operador ?c) (coste-movimiento baix))
   =>
   (assert (preferencia (en-estado S0) (sector ?s) (tipo-preferencia better)
                        (operador-referencia ?q) (operador-comparado ?c)
                        (criterio estabilitat) (origen regla))))
