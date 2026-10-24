;;; 06_seleccio.clp: módulo SELECCIO, procedimiento de decisión por sector (roadmap §5.6).
;;; Rechazado = tiene un reject; dominado = hay un better sobre él emitido por un candidato no
;;; rechazado; no dominado = ni una cosa ni otra. B(s) = incertesa-dades critic, o un candidato
;;; con require y reject, o dos candidatos con require. Todas las reglas exigen que no haya un
;;; seleccionado en el sector (una selección por ciclo). S5 (chunk) llega en I4.

(defmodule SELECCIO (import MAIN ?ALL))

;; Candidatos del sector que no están rechazados ni dominados (§5.6). Las preferencias no
;; cambian durante SELECCIO.
(deffunction SELECCIO::no-dominados (?sector)
   (bind ?r (create$))
   (do-for-all-facts ((?c operador-candidato)) (eq ?c:sector ?sector)
      (bind ?rechazado (> (length$ (find-fact ((?p preferencia))
                                      (and (eq ?p:tipo-preferencia reject)
                                           (eq ?p:operador-referencia ?c:id)))) 0))
      (bind ?dominado FALSE)
      (do-for-all-facts ((?b preferencia))
            (and (eq ?b:tipo-preferencia better) (eq ?b:operador-comparado ?c:id))
         (if (= (length$ (find-fact ((?p preferencia))
                            (and (eq ?p:tipo-preferencia reject)
                                 (eq ?p:operador-referencia ?b:operador-referencia)))) 0)
            then (bind ?dominado TRUE)))
      (if (and (not ?rechazado) (not ?dominado)) then (bind ?r (create$ ?r ?c:id))))
   ?r)

;; S1: incertesa-dades critic en el sector y sin impasse: impasse dades-insuficients (§5.6).
(defrule SELECCIO::s1-dades-insuficients
   (estado-soar (id S0) (fase seleccio))
   (diagnostico (sector ?s) (tipo-diagnostico incertesa-dades) (nivel critic))
   (not (impasse (sector ?s)))
   (not (operador-candidato (sector ?s) (estado-candidato seleccionat)))
   =>
   (assert (impasse (id (sym-cat ?s "-impasse")) (en-estado S0) (sector ?s)
                    (tipo-impasse dades-insuficients) (resuelto FALSE))))

;; S2: B(s) por un candidato con require y reject o por dos require, sin incertesa critic ni
;; impasse: impasse constraint-failure con los requeridos en conflicto (§5.6).
(defrule SELECCIO::s2-constraint-failure
   (estado-soar (id S0) (fase seleccio))
   (sector (id ?s))
   (or (and (preferencia (sector ?s) (tipo-preferencia require) (operador-referencia ?x))
            (preferencia (tipo-preferencia reject) (operador-referencia ?x)))
       (and (preferencia (sector ?s) (tipo-preferencia require) (operador-referencia ?x))
            (preferencia (sector ?s) (tipo-preferencia require) (operador-referencia ~?x))))
   (not (diagnostico (sector ?s) (tipo-diagnostico incertesa-dades) (nivel critic)))
   (not (impasse (sector ?s)))
   (not (operador-candidato (sector ?s) (estado-candidato seleccionat)))
   =>
   (bind ?requeridos (create$))
   (do-for-all-facts ((?p preferencia)) (and (eq ?p:sector ?s) (eq ?p:tipo-preferencia require))
      (if (not (member$ ?p:operador-referencia ?requeridos))
         then (bind ?requeridos (create$ ?requeridos ?p:operador-referencia))))
   (assert (impasse (id (sym-cat ?s "-impasse")) (en-estado S0) (sector ?s)
                    (tipo-impasse constraint-failure) (resuelto FALSE)
                    (operadores-en-conflicto ?requeridos))))

;; S3: exactamente un candidato con require no rechazado, sin B(s) o con un impasse del sector
;; resuelto y no escalat: se selecciona (§5.6).
(defrule SELECCIO::s3-seleccionar-requerido
   (estado-soar (id S0) (fase seleccio))
   (preferencia (sector ?s) (tipo-preferencia require) (operador-referencia ?c))
   ?f <- (operador-candidato (id ?c) (estado-candidato candidat))
   (not (preferencia (tipo-preferencia reject) (operador-referencia ?c)))
   (not (and (preferencia (sector ?s) (tipo-preferencia require) (operador-referencia ?o&~?c))
             (not (preferencia (tipo-preferencia reject) (operador-referencia ?o)))))
   (or (and (not (diagnostico (sector ?s) (tipo-diagnostico incertesa-dades) (nivel critic)))
            (not (and (preferencia (sector ?s) (tipo-preferencia require) (operador-referencia ?x))
                      (preferencia (tipo-preferencia reject) (operador-referencia ?x))))
            (not (and (preferencia (sector ?s) (tipo-preferencia require) (operador-referencia ?y))
                      (preferencia (sector ?s) (tipo-preferencia require) (operador-referencia ~?y)))))
       (impasse (sector ?s) (resuelto TRUE) (estrategia-resolucion ~escalat)))
   (not (operador-candidato (sector ?s) (estado-candidato seleccionat)))
   =>
   (modify ?f (estado-candidato seleccionat)))

;; S4: sin requeridos no rechazados, el único candidato no dominado, sin B(s) o con un impasse
;; del sector resuelto y no escalat: se selecciona (§5.6).
(defrule SELECCIO::s4-seleccionar-no-dominado
   (estado-soar (id S0) (fase seleccio))
   ?f <- (operador-candidato (id ?c) (sector ?s) (estado-candidato candidat))
   ;; ningún candidato no rechazado del sector tiene require
   (not (and (preferencia (sector ?s) (tipo-preferencia require) (operador-referencia ?r))
             (not (preferencia (tipo-preferencia reject) (operador-referencia ?r)))))
   ;; ?c no está rechazado ni dominado
   (not (preferencia (tipo-preferencia reject) (operador-referencia ?c)))
   (not (and (preferencia (tipo-preferencia better) (operador-comparado ?c) (operador-referencia ?d))
             (not (preferencia (tipo-preferencia reject) (operador-referencia ?d)))))
   ;; ningún otro candidato del sector es no dominado
   (not (and (operador-candidato (id ?o&~?c) (sector ?s))
             (not (preferencia (tipo-preferencia reject) (operador-referencia ?o)))
             (not (and (preferencia (tipo-preferencia better) (operador-comparado ?o)
                                    (operador-referencia ?d2))
                       (not (preferencia (tipo-preferencia reject) (operador-referencia ?d2)))))))
   (or (and (not (diagnostico (sector ?s) (tipo-diagnostico incertesa-dades) (nivel critic)))
            (not (and (preferencia (sector ?s) (tipo-preferencia require) (operador-referencia ?x))
                      (preferencia (tipo-preferencia reject) (operador-referencia ?x))))
            (not (and (preferencia (sector ?s) (tipo-preferencia require) (operador-referencia ?y))
                      (preferencia (sector ?s) (tipo-preferencia require) (operador-referencia ~?y)))))
       (impasse (sector ?s) (resuelto TRUE) (estrategia-resolucion ~escalat)))
   (not (operador-candidato (sector ?s) (estado-candidato seleccionat)))
   =>
   (modify ?f (estado-candidato seleccionat)))

;; S6: dos o más no dominados, ningún requerido no rechazado, sin B(s) ni impasse: impasse
;; tie con los no dominados en conflicto (§5.6).
(defrule SELECCIO::s6-tie
   (estado-soar (id S0) (fase seleccio))
   (operador-candidato (id ?a) (sector ?s))
   (operador-candidato (id ?b&~?a) (sector ?s))
   (not (preferencia (tipo-preferencia reject) (operador-referencia ?a)))
   (not (preferencia (tipo-preferencia reject) (operador-referencia ?b)))
   (not (and (preferencia (tipo-preferencia better) (operador-comparado ?a) (operador-referencia ?da))
             (not (preferencia (tipo-preferencia reject) (operador-referencia ?da)))))
   (not (and (preferencia (tipo-preferencia better) (operador-comparado ?b) (operador-referencia ?db))
             (not (preferencia (tipo-preferencia reject) (operador-referencia ?db)))))
   (not (and (preferencia (sector ?s) (tipo-preferencia require) (operador-referencia ?r))
             (not (preferencia (tipo-preferencia reject) (operador-referencia ?r)))))
   (not (diagnostico (sector ?s) (tipo-diagnostico incertesa-dades) (nivel critic)))
   (not (and (preferencia (sector ?s) (tipo-preferencia require) (operador-referencia ?x))
             (preferencia (tipo-preferencia reject) (operador-referencia ?x))))
   (not (and (preferencia (sector ?s) (tipo-preferencia require) (operador-referencia ?y))
             (preferencia (sector ?s) (tipo-preferencia require) (operador-referencia ~?y))))
   (not (impasse (sector ?s)))
   (not (operador-candidato (sector ?s) (estado-candidato seleccionat)))
   =>
   (assert (impasse (id (sym-cat ?s "-impasse")) (en-estado S0) (sector ?s)
                    (tipo-impasse tie) (resuelto FALSE)
                    (operadores-en-conflicto (no-dominados ?s)))))

;; S7: impasse del sector cerrado como escalat: se selecciona la acción sin movimiento (§5.6).
(defrule SELECCIO::s7-escalado
   (estado-soar (id S0) (fase seleccio))
   (impasse (sector ?s) (estrategia-resolucion escalat))
   ?f <- (operador-candidato (sector ?s) (accion ?a&:(accion-sin-movimiento ?a))
                             (estado-candidato candidat))
   (not (operador-candidato (sector ?s) (estado-candidato seleccionat)))
   =>
   (modify ?f (estado-candidato seleccionat)))

;; Con un seleccionado en el sector, los demás candidatos pasan a descartat (§5.6).
(defrule SELECCIO::descartar-resto
   (estado-soar (id S0) (fase seleccio))
   (operador-candidato (sector ?s) (estado-candidato seleccionat))
   ?f <- (operador-candidato (sector ?s) (estado-candidato candidat))
   =>
   (modify ?f (estado-candidato descartat)))
