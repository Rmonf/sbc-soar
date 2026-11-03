;;; 07_deliberacio.clp: DELIBERACIO. Resuelve cada impasse en un subestado y devuelve a S0 una
;;; preferencia better del ganador sobre los demás candidatos del sector. Toda deliberación
;;; termina con un ganador único.

(defmodule DELIBERACIO (import MAIN ?ALL))

;; Resultado del subestado: ?w es better que los demás candidatos del sector y el impasse se cierra.
(deffunction DELIBERACIO::resolver (?impasse ?w ?criterio ?estrategia)
   (bind ?s (fact-slot-value ?impasse sector))
   (do-for-all-facts ((?c operador-candidato)) (and (eq ?c:sector ?s) (neq ?c:id ?w))
      (assert (preferencia (sector ?s) (tipo-preferencia better) (operador-referencia ?w)
                           (operador-comparado ?c:id) (criterio ?criterio) (origen deliberacio))))
   (modify ?impasse (resuelto TRUE) (estrategia-resolucion ?estrategia)))

;; SOAR: subestado. Cada impasse abierto crea un estado hijo de S0 en el que se delibera.
(defrule DELIBERACIO::crear-subestado
   (estado-soar (id S0) (fase deliberacio))
   (impasse (id ?i) (en-estado ?padre) (resuelto FALSE))
   (not (estado-soar (impasse-asociado ?i)))
   =>
   (assert (estado-soar (id (sym-cat S- ?i)) (estado-padre ?padre) (fase deliberacio)
                        (subfase pendent) (impasse-asociado ?i))))

;; SOAR: resolución de un tie en el subestado. Gana el candidato que sirve al objetivo más
;; prioritario (objetivo-activo). Es único: cada objetivo lo sirve una sola acción, porque la
;; acción sin movimiento solo hereda objetivos de acciones que no se propusieron.
(defrule DELIBERACIO::tie-prioridad
   (estado-soar (id S0) (fase deliberacio))
   (estado-soar (impasse-asociado ?i))
   ?imp <- (impasse (id ?i) (tipo-impasse tie) (resuelto FALSE) (operadores-en-conflicto $? ?w $?))
   (objetivo-activo (nombre-objetivo ?k&:(eq ?k (objetivo-servido ?w))) (prioridad ?p))
   (not (and (impasse (id ?i) (operadores-en-conflicto $? ?o&~?w $?))
             (objetivo-activo (nombre-objetivo ?k2&:(eq ?k2 (objetivo-servido ?o))) (prioridad ?q&:(< ?q ?p)))))
   =>
   (resolver ?imp ?w ?k prioritat-objectius))

;; SOAR: resolución de dades-insuficients con la memoria episódica. Hubo riesgo mecánico en la
;; última hora: ir a defensa por prevención.
(defrule DELIBERACIO::datos-preventiva
   (estado-soar (id S0) (fase deliberacio))
   (ciclo-temporal (instante ?t))
   (estado-soar (impasse-asociado ?i))
   ?imp <- (impasse (id ?i) (sector ?s) (tipo-impasse dades-insuficients) (resuelto FALSE))
   (operador-candidato (id ?w) (sector ?s) (accion posicio-seguretat))
   (not (preferencia (tipo-preferencia reject) (operador-referencia ?w)))
   (test (riesgo-reciente ?s ?t))
   =>
   (resolver ?imp ?w integritat-mecanica posicio-preventiva))

;; SOAR: resolución de dades-insuficients. Si no hay motivo para ir a defensa: no mover y pedir datos.
(defrule DELIBERACIO::datos-pedir
   (estado-soar (id S0) (fase deliberacio))
   (ciclo-temporal (instante ?t))
   (estado-soar (impasse-asociado ?i))
   ?imp <- (impasse (id ?i) (sector ?s) (tipo-impasse dades-insuficients) (resuelto FALSE))
   (operador-candidato (id ?w) (sector ?s) (accion diagnosticar))
   (not (and (operador-candidato (id ?x) (sector ?s) (accion posicio-seguretat))
             (not (preferencia (tipo-preferencia reject) (operador-referencia ?x)))
             (test (riesgo-reciente ?s ?t))))
   =>
   (resolver ?imp ?w estabilitat demanar-dades))
