;;; 07_deliberacio.clp: módulo DELIBERACIO, resolución de impasses en subestados (roadmap §5.7).
;;; Por cada impasse abierto se crea un subestado (id derivado del impasse). Las estrategias de
;;; cada tipo están en orden y son mutuamente excluyentes: una se aplica solo si da un resultado
;;; único, y la siguiente solo si la anterior no se aplica. El resultado vuelve al estado padre
;;; S0 como preferencia (origen deliberacio); no se crean candidatos. Si ninguna se aplica, MAIN
;;; cierra el impasse como escalat (§4.2). Las funciones leen valoraciones, preferencias y
;;; episodios, que no cambian durante la deliberación de un sector.

(defmodule DELIBERACIO (import MAIN ?ALL))

;; Valoración de un candidato.
(deffunction DELIBERACIO::valoracion-de (?candidato)
   (nth$ 1 (find-fact ((?v valoracion)) (eq ?v:evalua-operador ?candidato))))

;; minima-intervencio: el único candidato en conflicto cuyo Δ es menor que el de todos los demás
;; por más de la tolerancia, o nil (§5.7).
(deffunction DELIBERACIO::ganador-minima-intervencio (?candidatos ?tol)
   (foreach ?c ?candidatos
      (bind ?dc (fact-slot-value (valoracion-de ?c) desplazamiento))
      (bind ?gana TRUE)
      (foreach ?o ?candidatos
         (if (and (neq ?o ?c)
                  (<= (- (fact-slot-value (valoracion-de ?o) desplazamiento) ?dc) ?tol))
            then (bind ?gana FALSE)))
      (if ?gana then (return ?c)))
   nil)

;; Objetivo que sirve un candidato: el de mayor prioridad con beneficio ≥ mitja, o nil.
(deffunction DELIBERACIO::objetivo-de (?candidato)
   (bind ?v (valoracion-de ?candidato))
   (criterio-servido (fact-slot-value ?v beneficio-mecanico) (fact-slot-value ?v beneficio-cultivo)
                     (fact-slot-value ?v beneficio-energia)))

(deffunction DELIBERACIO::prioridad-de (?objetivo)
   (if (eq ?objetivo nil) then (return 99))
   (fact-slot-value (nth$ 1 (find-fact ((?o objetivo-activo)) (eq ?o:nombre-objetivo ?objetivo)))
                    prioridad))

;; prioritat-objectius: el único candidato en conflicto que sirve al objetivo de mayor
;; prioridad, o nil (§5.7).
(deffunction DELIBERACIO::ganador-prioritat-objectius (?candidatos)
   (bind ?mejor nil)
   (bind ?p-mejor 99)
   (bind ?empatado FALSE)
   (foreach ?c ?candidatos
      (bind ?p (prioridad-de (objetivo-de ?c)))
      (if (< ?p ?p-mejor) then (bind ?mejor ?c) (bind ?p-mejor ?p) (bind ?empatado FALSE)
       else (if (= ?p ?p-mejor) then (bind ?empatado TRUE))))
   (if (or ?empatado (= ?p-mejor 99)) then nil else ?mejor))

;; ¿Está rechazado el candidato? (§5.6)
(deffunction DELIBERACIO::rechazado (?candidato)
   (> (length$ (find-fact ((?p preferencia))
                  (and (eq ?p:tipo-preferencia reject) (eq ?p:operador-referencia ?candidato))))
      0))

;; posicio-preventiva: posicio-seguretat no rechazada, y la requiere R2 o hubo riesgo mecánico
;; ≥ alt en la última hora (historial episódico). Devuelve el candidato o nil (§5.7).
(deffunction DELIBERACIO::posicio-preventiva-aplicable (?sector ?t)
   (bind ?p (find-fact ((?c operador-candidato))
               (and (eq ?c:sector ?sector) (eq ?c:accion posicio-seguretat))))
   (if (= (length$ ?p) 0) then (return nil))
   (bind ?id (fact-slot-value (nth$ 1 ?p) id))
   (if (rechazado ?id) then (return nil))
   (if (or (> (length$ (find-fact ((?r preferencia))
                          (and (eq ?r:tipo-preferencia require) (eq ?r:operador-referencia ?id)
                               (eq ?r:restriccion R2))))
              0)
           (riesgo-mecanico-reciente ?sector ?t))
      then ?id else nil))

;; Crea el subestado de un impasse abierto, hijo de S0 (§5.7).
(defrule DELIBERACIO::crear-subestado
   (estado-soar (id S0) (fase deliberacio))
   (impasse (id ?i) (resuelto FALSE))
   (not (estado-soar (impasse-asociado ?i)))
   =>
   (assert (estado-soar (id (sym-cat sub- ?i)) (estado-padre S0) (fase deliberacio)
                        (subfase pendent) (impasse-asociado ?i))))

;; tie, minima-intervencio: el empatado con el menor Δ (diferencia > tolerancia) es better que
;; los demás, con criterio estabilitat (la acción más reversible, enunciado 3.7.3) (§5.7).
(defrule DELIBERACIO::tie-minima-intervencio
   (estado-soar (id S0) (fase deliberacio))
   (estado-soar (estado-padre S0) (impasse-asociado ?i))
   ?imp <- (impasse (id ?i) (sector ?s) (tipo-impasse tie) (resuelto FALSE)
                    (operadores-en-conflicto $?ops))
   (test (neq (ganador-minima-intervencio ?ops (tolerancia-sector ?s)) nil))
   =>
   (bind ?g (ganador-minima-intervencio ?ops (tolerancia-sector ?s)))
   (foreach ?o ?ops
      (if (neq ?o ?g) then
         (assert (preferencia (en-estado S0) (sector ?s) (tipo-preferencia better)
                              (operador-referencia ?g) (operador-comparado ?o)
                              (criterio estabilitat) (origen deliberacio)))))
   (modify ?imp (resuelto TRUE) (estrategia-resolucion minima-intervencio)))

;; tie, prioritat-objectius: si minima-intervencio no se aplica, el único empatado que sirve al
;; objetivo de mayor prioridad es better que los demás, con ese objetivo como criterio (§5.7).
(defrule DELIBERACIO::tie-prioritat-objectius
   (estado-soar (id S0) (fase deliberacio))
   (estado-soar (estado-padre S0) (impasse-asociado ?i))
   ?imp <- (impasse (id ?i) (sector ?s) (tipo-impasse tie) (resuelto FALSE)
                    (operadores-en-conflicto $?ops))
   (test (eq (ganador-minima-intervencio ?ops (tolerancia-sector ?s)) nil))
   (test (neq (ganador-prioritat-objectius ?ops) nil))
   =>
   (bind ?g (ganador-prioritat-objectius ?ops))
   (foreach ?o ?ops
      (if (neq ?o ?g) then
         (assert (preferencia (en-estado S0) (sector ?s) (tipo-preferencia better)
                              (operador-referencia ?g) (operador-comparado ?o)
                              (criterio (objetivo-de ?g)) (origen deliberacio)))))
   (modify ?imp (resuelto TRUE) (estrategia-resolucion prioritat-objectius)))

;; dades-insuficients, posicio-preventiva: require posicio-seguretat si no está rechazada y la
;; requiere R2 o hubo riesgo mecánico reciente (§5.7).
(defrule DELIBERACIO::dades-posicio-preventiva
   (estado-soar (id S0) (fase deliberacio))
   (ciclo-temporal (instante ?t))
   (estado-soar (estado-padre S0) (impasse-asociado ?i))
   ?imp <- (impasse (id ?i) (sector ?s) (tipo-impasse dades-insuficients) (resuelto FALSE))
   (test (neq (posicio-preventiva-aplicable ?s ?t) nil))
   =>
   (assert (preferencia (en-estado S0) (sector ?s) (tipo-preferencia require)
                        (operador-referencia (posicio-preventiva-aplicable ?s ?t))
                        (criterio integritat-mecanica) (origen deliberacio)))
   (modify ?imp (resuelto TRUE) (estrategia-resolucion posicio-preventiva)))

;; dades-insuficients, demanar-dades: si no, require diagnosticar (§5.7).
(defrule DELIBERACIO::dades-demanar-dades
   (estado-soar (id S0) (fase deliberacio))
   (ciclo-temporal (instante ?t))
   (estado-soar (estado-padre S0) (impasse-asociado ?i))
   ?imp <- (impasse (id ?i) (sector ?s) (tipo-impasse dades-insuficients) (resuelto FALSE))
   (test (eq (posicio-preventiva-aplicable ?s ?t) nil))
   (operador-candidato (id ?d) (sector ?s) (accion diagnosticar))
   =>
   (assert (preferencia (en-estado S0) (sector ?s) (tipo-preferencia require)
                        (operador-referencia ?d) (criterio integritat-mecanica)
                        (origen deliberacio)))
   (modify ?imp (resuelto TRUE) (estrategia-resolucion demanar-dades)))

;; constraint-failure, restriccio-prioritaria: prevalecen los reject. Reject a todo requerido
;; que mueva y require a la acción sin movimiento, con el criterio de mayor prioridad entre los
;; reject del sector (integritat-mecanica si no hay) (§5.7).
(defrule DELIBERACIO::constraint-restriccio-prioritaria
   (estado-soar (id S0) (fase deliberacio))
   (estado-soar (estado-padre S0) (impasse-asociado ?i))
   ?imp <- (impasse (id ?i) (sector ?s) (tipo-impasse constraint-failure) (resuelto FALSE))
   (operador-candidato (id ?q) (sector ?s) (accion ?aq&:(accion-sin-movimiento ?aq)))
   =>
   (bind ?criterio integritat-mecanica)
   (bind ?p-mejor 99)
   (do-for-all-facts ((?r preferencia)) (and (eq ?r:sector ?s) (eq ?r:tipo-preferencia reject))
      (if (< (prioridad-de ?r:criterio) ?p-mejor)
         then (bind ?criterio ?r:criterio) (bind ?p-mejor (prioridad-de ?r:criterio))))
   ;; primero se recogen los requeridos que mueven; después se asertan los reject
   (bind ?mueven (create$))
   (do-for-all-facts ((?r preferencia) (?c operador-candidato))
         (and (eq ?r:sector ?s) (eq ?r:tipo-preferencia require) (eq ?c:id ?r:operador-referencia)
              (candidato-mueve ?c:accion ?c:angulo-objetivo ?s))
      (bind ?mueven (create$ ?mueven ?c:id)))
   (foreach ?c ?mueven
      (assert (preferencia (en-estado S0) (sector ?s) (tipo-preferencia reject)
                           (operador-referencia ?c) (criterio ?criterio) (origen deliberacio))))
   (assert (preferencia (en-estado S0) (sector ?s) (tipo-preferencia require)
                        (operador-referencia ?q) (criterio ?criterio) (origen deliberacio)))
   (modify ?imp (resuelto TRUE) (estrategia-resolucion restriccio-prioritaria)))
