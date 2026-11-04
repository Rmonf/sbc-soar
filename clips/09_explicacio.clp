;;; 09_explicacio.clp: EXPLICACIO. Una regla guarda el episodio (memoria episódica) y escribe la
;;; traza al estilo del anexo B del enunciado. Las funciones solo leen hechos que ya no cambian.

(defmodule EXPLICACIO (import MAIN ?ALL))

(deffunction EXPLICACIO::antes (?a ?b) (> (str-compare ?a ?b) 0))

;; Valores sin repetir y ordenados, o "-".
(deffunction EXPLICACIO::lista (?valores)
   (bind ?unicos (create$))
   (foreach ?v ?valores (if (not (member$ ?v ?unicos)) then (bind ?unicos (create$ ?unicos ?v))))
   (if (= (length$ ?unicos) 0) then "-" else (implode$ (sort antes ?unicos))))

(deffunction EXPLICACIO::situacion (?s)
   (bind ?r (create$))
   (do-for-all-facts ((?d diagnostico)) (eq ?d:sector ?s)
      (bind ?r (create$ ?r (sym-cat ?d:tipo-diagnostico : ?d:nivel))))
   ?r)

(deffunction EXPLICACIO::alternativas (?s)
   (bind ?r (create$))
   (do-for-all-facts ((?c operador-candidato)) (eq ?c:sector ?s) (bind ?r (create$ ?r ?c:accion)))
   ?r)

(deffunction EXPLICACIO::rechazado (?o)
   (any-factp ((?p preferencia)) (and (eq ?p:tipo-preferencia reject) (eq ?p:operador-referencia ?o))))

;; Criterio de los better de ?slot = ?o (operador-referencia u operador-comparado) emitidos por
;; candidatos no rechazados: primero uno de deliberación o de chunk; si no, el del objetivo más
;; prioritario. nil si no hay ninguno.
(deffunction EXPLICACIO::criterio-better (?slot ?o)
   (bind ?mejor nil) (bind ?clave 99)
   (do-for-all-facts ((?p preferencia) (?g objetivo-activo))
         (and (eq ?p:tipo-preferencia better) (eq (fact-slot-value ?p ?slot) ?o)
              (not (rechazado ?p:operador-referencia)) (eq ?g:nombre-objetivo ?p:criterio))
      (bind ?k (+ ?g:prioridad (if (eq ?p:origen regla) then 10 else 0)))
      (if (< ?k ?clave) then (bind ?clave ?k) (bind ?mejor ?p:criterio)))
   ?mejor)

;; accion:criterio de cada descartado: el de sus reject o, si no tiene, el del better en contra.
(deffunction EXPLICACIO::descartes (?s)
   (bind ?r (create$))
   (do-for-all-facts ((?c operador-candidato)) (and (eq ?c:sector ?s) (eq ?c:estado-candidato descartat))
      (if (rechazado ?c:id)
         then (do-for-all-facts ((?p preferencia))
                    (and (eq ?p:tipo-preferencia reject) (eq ?p:operador-referencia ?c:id))
                 (bind ?r (create$ ?r (sym-cat ?c:accion : ?p:criterio))))
         else (bind ?r (create$ ?r (sym-cat ?c:accion : (criterio-better operador-comparado ?c:id))))))
   ?r)

(deffunction EXPLICACIO::restricciones (?s)
   (bind ?r (create$))
   (do-for-all-facts ((?p preferencia)) (and (eq ?p:sector ?s) (neq ?p:restriccion nil))
      (if (not (member$ ?p:restriccion ?r)) then (bind ?r (create$ ?r ?p:restriccion))))
   ?r)

(deffunction EXPLICACIO::slot-impasse (?s ?slot)
   (bind ?i (find-fact ((?i impasse)) (eq ?i:sector ?s)))
   (if (= (length$ ?i) 0) then nil else (fact-slot-value (nth$ 1 ?i) ?slot)))

(deffunction EXPLICACIO::chunk-de (?c)
   (bind ?p (find-fact ((?p preferencia)) (and (eq ?p:origen chunk) (eq ?p:operador-referencia ?c))))
   (if (= (length$ ?p) 0) then nil else (fact-slot-value (nth$ 1 ?p) chunk-aplicado)))

(deffunction EXPLICACIO::beneficio-de (?c ?slot)
   (bind ?v (find-fact ((?v valoracion)) (eq ?v:evalua-operador ?c)))
   (if (= (length$ ?v) 0) then baix else (fact-slot-value (nth$ 1 ?v) ?slot)))

(deffunction EXPLICACIO::entradas (?s)
   (bind ?r (create$))
   (do-for-all-facts ((?o observacion-sensor)) (eq ?o:sector ?s)
      (bind ?r (create$ ?r (sym-cat ?o:variable = (if (eq ?o:calidad fallada) then fallada else ?o:valor)))))
   (do-for-all-facts ((?o prediccion)) (eq ?o:sector ?s) (bind ?r (create$ ?r (sym-cat ?o:variable = ?o:valor))))
   (bind ?p "desconegut")
   (do-for-fact ((?o observacion-panel)) (eq ?o:sector ?s)
      (bind ?p (str-cat ?o:angulo-actual " (" ?o:estado-mecanico ", " ?o:ocupacion ")")))
   (str-cat (lista ?r) " panell=" ?p))

;; SOAR: memoria episódica y explicación. Guarda el episodio del sector y escribe su traza.
(defrule EXPLICACIO::explicar
   (estado-soar (id S0) (fase explicacio))
   (ciclo-temporal (instante ?t))
   (operador-candidato (id ?c) (sector ?s) (accion ?a) (estado-candidato aplicat))
   (orden-actuador (sector ?s) (instante ?t) (angulo-ordenado ?ang) (escalado-humano ?esc))
   =>
   (bind ?previo nil)
   (do-for-fact ((?o observacion-panel)) (eq ?o:sector ?s) (bind ?previo ?o:angulo-actual))
   (bind ?sit (situacion ?s))
   (bind ?criterio (criterio-better operador-referencia ?c))
   (if (and (eq ?criterio nil) (= 1 (length$ (find-all-facts ((?k operador-candidato)) (and (eq ?k:sector ?s) (not (rechazado ?k:id)))))))
    then (do-for-fact ((?p preferencia)) (and (eq ?p:sector ?s) (eq ?p:tipo-preferencia reject))
            (bind ?criterio ?p:criterio)))
   (bind ?chunk (chunk-de ?c))
   (bind ?ti (slot-impasse ?s tipo-impasse))
   (bind ?bc (beneficio-de ?c beneficio-cultivo))
   (bind ?be (beneficio-de ?c beneficio-energia))
   (bind ?sens nil)
   (do-for-fact ((?x sector) (?k cultivo)) (and (eq ?x:id ?s) (eq ?k:id ?x:tiene-cultivo)) (bind ?sens ?k:sensibilidad))
   (assert (episodio (sector ?s) (instante ?t) (situacion ?sit) (alternativas (alternativas ?s))
                     (descartes (descartes ?s)) (restricciones-activas (restricciones ?s))
                     (criterio-determinante ?criterio) (accion ?a) (angulo-previo ?previo)
                     (angulo-ordenado ?ang) (beneficio-cultivo ?bc) (beneficio-energia ?be)
                     (tipo-impasse ?ti) (chunk-aplicado ?chunk) (resultado pendent)))
   (printout traza "Fets d'entrada: t=" ?t ", sector=" ?s ", " (entradas ?s) crlf
                   "Diagnosi: " (lista ?sit) crlf
                   "Candidats: " (lista (alternativas ?s)) crlf
                   "Descartats: " (lista (descartes ?s)) "   Restriccions: " (lista (restricciones ?s)) crlf
                   "Impasse: " (if (eq ?ti nil) then "-" else (str-cat ?ti " (" (slot-impasse ?s estrategia-resolucion) ")")) crlf
                   "Decisio: " ?a (if (eq ?chunk nil) then "" else (str-cat " (" ?chunk ", apres de "
                        (fact-slot-value (nth$ 1 (find-fact ((?k chunk)) (eq ?k:id ?chunk))) estrategia-resolucion) ")"))
                   "   Criteri: " (if (eq ?criterio nil) then "-" else ?criterio) crlf
                   "Ordre: sector=" ?s ", angle=" ?ang ", escalat a persona: " (if ?esc then "si" else "no") crlf
                   "Vista agronomica: benefici cultiu=" ?bc ", sensibilitat del cultiu=" ?sens "   Vista energetica: benefici energia=" ?be crlf crlf))
