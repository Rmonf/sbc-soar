;;; 07_deliberacio.clp: módulo DELIBERACIO, resolución de impasses en subestados (roadmap §5.7).
;;; Por cada impasse abierto se crea un subestado (id derivado del impasse). Las estrategias de
;;; cada tipo están en orden y son mutuamente excluyentes: una se aplica solo si da un resultado
;;; único, y la siguiente solo si la anterior no se aplica. El resultado vuelve al estado padre
;;; S0 como preferencia (origen deliberacio); no se crean candidatos. Si ninguna se aplica, MAIN
;;; cierra el impasse como escalat (§4.2). Las funciones leen valoraciones, preferencias y
;;; episodios, que no cambian durante la deliberación de un sector. La estrategia que se aplica
;;; escribe en la traza una línea Deliberacio con lo que comparó (§5.9), con los elementos
;;; ordenados para que no dependa del orden de disparo.

(defmodule DELIBERACIO (import MAIN ?ALL))

;; Orden alfabético y unión con comas, para la traza (§2.3.11).
(deffunction DELIBERACIO::despues-de (?a ?b)
   (> (str-compare ?a ?b) 0))

(deffunction DELIBERACIO::juntar (?textos)
   (bind ?r "")
   (foreach ?x (sort despues-de ?textos)
      (bind ?r (if (= ?x-index 1) then ?x else (str-cat ?r ", " ?x))))
   ?r)

;; Acción de un candidato.
(deffunction DELIBERACIO::accion-de (?candidato)
   (fact-slot-value (nth$ 1 (find-fact ((?c operador-candidato)) (eq ?c:id ?candidato))) accion))

;; Línea de la deliberación en la traza (§5.9).
(deffunction DELIBERACIO::traza-deliberacion (?sector ?tipo ?estrategia ?comparado ?resultado)
   (printout traza "Deliberacio (t=" (instante-actual) "): sector=" ?sector ", " ?tipo ", "
                   ?estrategia ": " ?comparado " -> " ?resultado crlf))

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

;; Qué miró posicio-preventiva en el sector: si posicio-seguretat existe y no está rechazada,
;; el require de R2 y los episodios de la última hora con riesgo mecánico ≥ alt (§5.7).
(deffunction DELIBERACIO::motivo-preventiva (?sector ?t)
   (bind ?p (find-fact ((?c operador-candidato))
               (and (eq ?c:sector ?sector) (eq ?c:accion posicio-seguretat))))
   (if (= (length$ ?p) 0) then (return "sense candidat posicio-seguretat"))
   (bind ?id (fact-slot-value (nth$ 1 ?p) id))
   (if (rechazado ?id) then
      (bind ?rs (create$))
      (do-for-all-facts ((?r preferencia))
            (and (eq ?r:tipo-preferencia reject) (eq ?r:operador-referencia ?id))
         (bind ?rs (create$ ?rs (str-cat ?r:restriccion))))
      (return (str-cat "posicio-seguretat rebutjada (" (juntar ?rs) ")")))
   (if (> (length$ (find-fact ((?r preferencia))
                      (and (eq ?r:tipo-preferencia require) (eq ?r:operador-referencia ?id)
                           (eq ?r:restriccion R2))))
          0)
      then (return "posicio-seguretat no rebutjada; R2 la requereix"))
   (bind ?es (create$))
   (do-for-all-facts ((?e episodio))
         (and (eq ?e:sector ?sector) (>= ?e:instante (- ?t ?*ventana-episodica*)) (< ?e:instante ?t)
              (or (member$ risc-mecanic:alt ?e:situacion) (member$ risc-mecanic:critic ?e:situacion)))
      (bind ?es (create$ ?es (str-cat "t=" ?e:instante))))
   (if (> (length$ ?es) 0)
      then (str-cat "posicio-seguretat no rebutjada; risc mecanic recent (episodis " (juntar ?es) ")")
      else "posicio-seguretat no rebutjada; sense R2 ni risc mecanic recent"))

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
   (bind ?deltas (create$))
   (foreach ?o ?ops
      (bind ?deltas (create$ ?deltas (str-cat "Δ " (accion-de ?o) "="
                                               (fact-slot-value (valoracion-de ?o) desplazamiento)))))
   (traza-deliberacion ?s tie minima-intervencio
                       (str-cat (juntar ?deltas) " (tolerancia " (tolerancia-sector ?s) ")")
                       (accion-de ?g))
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
   (bind ?objetivos (create$))
   (foreach ?o ?ops
      (bind ?obj (objetivo-de ?o))
      (bind ?objetivos (create$ ?objetivos
                                (if (eq ?obj nil) then (str-cat (accion-de ?o) ": cap objectiu")
                                 else (str-cat (accion-de ?o) ": " ?obj " (prioritat "
                                               (prioridad-de ?obj) ")")))))
   (traza-deliberacion ?s tie prioritat-objectius (juntar ?objetivos) (accion-de ?g))
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
   (traza-deliberacion ?s dades-insuficients posicio-preventiva (motivo-preventiva ?s ?t)
                       "require posicio-seguretat")
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
   (traza-deliberacion ?s dades-insuficients demanar-dades
                       (str-cat "posicio-preventiva no aplicable: " (motivo-preventiva ?s ?t))
                       "require diagnosticar")
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
   (bind ?rechazos (create$))
   (do-for-all-facts ((?r preferencia)) (and (eq ?r:sector ?s) (eq ?r:tipo-preferencia reject))
      (bind ?texto (str-cat ?r:restriccion " " ?r:criterio " (prioritat " (prioridad-de ?r:criterio) ")"))
      (if (not (member$ ?texto ?rechazos)) then (bind ?rechazos (create$ ?rechazos ?texto)))
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
   (traza-deliberacion ?s constraint-failure restriccio-prioritaria
                       (str-cat "rebutjos " (if (= (length$ ?rechazos) 0) then "-" else (juntar ?rechazos))
                                "; criteri " ?criterio)
                       (str-cat "require " ?aq))
   (modify ?imp (resuelto TRUE) (estrategia-resolucion restriccio-prioritaria)))
