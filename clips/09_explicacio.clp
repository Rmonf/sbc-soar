;;; 09_explicacio.clp: módulo EXPLICACIO, episodio y traza de la decisión (roadmap §5.9).
;;; El episodio se crea en una regla y se completa con reglas acumulativas protegidas con
;;; (not (member$ ...)). La traza la escribe una sola regla, imprimir-traza, que solo se activa
;;; cuando no queda nada por anotar: su LHS niega la condición de cada regla acumulativa.
;;; Así la traza sale completa y una sola vez, sea cual sea la estrategia de agenda.
;;; El episodio y la traza no necesitan observacion-panel ni valoracion: sin panel (R5), el
;;; ángulo previo es nil, los beneficios baix y la traza dice panell=desconegut.
;;; Pendiente: chunks (I4).

(defmodule EXPLICACIO (import MAIN ?ALL))

;; Orden alfabético para imprimir los multislots como conjuntos (§2.3.11).
(deffunction EXPLICACIO::despues-de (?a ?b)
   (> (str-compare ?a ?b) 0))

;; Beneficio de un candidato en un slot de su valoración, o baix si no tiene: sin panel no
;; hay Δ ni valoración (§5.5b).
(deffunction EXPLICACIO::beneficio-de (?candidato ?slot)
   (bind ?v (find-fact ((?f valoracion)) (eq ?f:evalua-operador ?candidato)))
   (if (= (length$ ?v) 0) then baix else (fact-slot-value (nth$ 1 ?v) ?slot)))

;; Panel observado del sector para la traza, o desconegut sin observacion-panel (§3.2).
(deffunction EXPLICACIO::descripcion-panel (?sector)
   (bind ?p (find-fact ((?o observacion-panel)) (eq ?o:sector ?sector)))
   (if (= (length$ ?p) 0) then (return "desconegut"))
   (bind ?o (nth$ 1 ?p))
   (str-cat (fact-slot-value ?o angulo-actual) " (" (fact-slot-value ?o estado-mecanico) ", "
            (fact-slot-value ?o ocupacion) ")"))

;; Evidencias de los diagnósticos del sector, tipo=ev1 ev2, para la traza (§5.9, anexo B:
;; qué hechos sustentan la inferencia).
(deffunction EXPLICACIO::evidencias-de (?sector)
   (bind ?r (create$))
   (do-for-all-facts ((?d diagnostico)) (eq ?d:sector ?sector)
      (bind ?r (create$ ?r (str-cat ?d:tipo-diagnostico "=" (implode$ (sort despues-de ?d:evidencias))))))
   ?r)

;; Impasse del sector para la traza: tipo (estrategia), o "-" si no hubo (§5.9).
(deffunction EXPLICACIO::descripcion-impasse (?sector)
   (bind ?i (find-fact ((?f impasse)) (eq ?f:sector ?sector)))
   (if (= (length$ ?i) 0) then (return "-"))
   (str-cat (fact-slot-value (nth$ 1 ?i) tipo-impasse) " ("
            (fact-slot-value (nth$ 1 ?i) estrategia-resolucion) ")"))

;; Multislot ordenado y separado por comas, o "-" si está vacío.
(deffunction EXPLICACIO::lista (?valores)
   (if (= (length$ ?valores) 0) then (return "-"))
   (bind ?texto "")
   (foreach ?v (sort despues-de ?valores)
      (bind ?texto (if (= ?v-index 1) then (str-cat ?v) else (str-cat ?texto ", " ?v))))
   ?texto)

;; Crea el episodio del sector con la acción aplicada, el ángulo previo (nil sin panel) y los
;; beneficios de la acción elegida (baix sin valoración); las pérdidas parten de baix, el
;; máximo de un conjunto vacío (§5.9).
(defrule EXPLICACIO::crear-episodio
   (estado-soar (id S0) (fase explicacio))
   (ciclo-temporal (instante ?t))
   (operador-candidato (id ?c) (sector ?s) (accion ?a) (estado-candidato aplicat))
   (orden-actuador (sector ?s) (instante ?t) (angulo-ordenado ?ang) (escalado-humano ?esc))
   =>
   (assert (episodio (id (sym-cat episodio- ?s "-" ?t)) (sector ?s) (instante ?t) (accion ?a)
                     (angulo-previo (angulo-observado ?s)) (angulo-ordenado ?ang)
                     (beneficio-cultivo (beneficio-de ?c beneficio-cultivo))
                     (beneficio-energia (beneficio-de ?c beneficio-energia))
                     (perdida-cultivo baix) (perdida-energia baix)
                     (escalado-humano ?esc) (resultado pendent))))

;; Añade cada diagnóstico del sector a la situación, como tipo:nivel (§5.9).
(defrule EXPLICACIO::anotar-situacion
   (estado-soar (id S0) (fase explicacio))
   ?e <- (episodio (sector ?s) (instante ?t) (situacion $?sit))
   (ciclo-temporal (instante ?t))
   (diagnostico (sector ?s) (tipo-diagnostico ?d) (nivel ?n))
   (test (not (member$ (sym-cat ?d ":" ?n) ?sit)))
   =>
   (modify ?e (situacion ?sit (sym-cat ?d ":" ?n))))

;; Añade cada candidato del sector a las alternativas (§5.9).
(defrule EXPLICACIO::anotar-alternativa
   (estado-soar (id S0) (fase explicacio))
   ?e <- (episodio (sector ?s) (instante ?t) (alternativas $?alt))
   (ciclo-temporal (instante ?t))
   (operador-candidato (sector ?s) (accion ?a&:(not (member$ ?a ?alt))))
   =>
   (modify ?e (alternativas ?alt ?a)))

;; Descartado por un reject: accion:criterio de cada reject (§5.9).
(defrule EXPLICACIO::anotar-descarte-reject
   (estado-soar (id S0) (fase explicacio))
   ?e <- (episodio (sector ?s) (instante ?t) (descartes $?des))
   (ciclo-temporal (instante ?t))
   (operador-candidato (id ?o) (sector ?s) (accion ?a) (estado-candidato descartat))
   (preferencia (tipo-preferencia reject) (operador-referencia ?o) (criterio ?k))
   (test (not (member$ (sym-cat ?a ":" ?k) ?des)))
   =>
   (modify ?e (descartes ?des (sym-cat ?a ":" ?k))))

;; Descartado no rechazado pero dominado: accion:criterio de cada better efectivo (§5.9).
(defrule EXPLICACIO::anotar-descarte-better
   (estado-soar (id S0) (fase explicacio))
   ?e <- (episodio (sector ?s) (instante ?t) (descartes $?des))
   (ciclo-temporal (instante ?t))
   (operador-candidato (id ?o) (sector ?s) (accion ?a) (estado-candidato descartat))
   (not (preferencia (tipo-preferencia reject) (operador-referencia ?o)))
   (preferencia (tipo-preferencia better) (operador-comparado ?o) (operador-referencia ?d)
                (criterio ?k))
   (not (preferencia (tipo-preferencia reject) (operador-referencia ?d)))
   (test (not (member$ (sym-cat ?a ":" ?k) ?des)))
   =>
   (modify ?e (descartes ?des (sym-cat ?a ":" ?k))))

;; Descartado ni rechazado ni dominado: lo desplaza el require del sector (§5.9).
(defrule EXPLICACIO::anotar-descarte-require
   (estado-soar (id S0) (fase explicacio))
   ?e <- (episodio (sector ?s) (instante ?t) (descartes $?des))
   (ciclo-temporal (instante ?t))
   (operador-candidato (id ?o) (sector ?s) (accion ?a) (estado-candidato descartat))
   (not (preferencia (tipo-preferencia reject) (operador-referencia ?o)))
   (not (and (preferencia (tipo-preferencia better) (operador-comparado ?o) (operador-referencia ?d))
             (not (preferencia (tipo-preferencia reject) (operador-referencia ?d)))))
   (preferencia (sector ?s) (tipo-preferencia require) (criterio ?k))
   (test (not (member$ (sym-cat ?a ":" ?k) ?des)))
   =>
   (modify ?e (descartes ?des (sym-cat ?a ":" ?k))))

;; Añade cada restricción dura activa en el sector (§5.9).
(defrule EXPLICACIO::anotar-restriccion
   (estado-soar (id S0) (fase explicacio))
   ?e <- (episodio (sector ?s) (instante ?t) (restricciones-activas $?ra))
   (ciclo-temporal (instante ?t))
   (preferencia (sector ?s) (restriccion ?r&~nil&:(not (member$ ?r ?ra))))
   =>
   (modify ?e (restricciones-activas ?ra ?r)))

;; Tipo del impasse que tuvo el sector en este ciclo (§5.9).
(defrule EXPLICACIO::anotar-impasse
   (estado-soar (id S0) (fase explicacio))
   ?e <- (episodio (sector ?s) (instante ?t) (tipo-impasse nil))
   (ciclo-temporal (instante ?t))
   (impasse (sector ?s) (tipo-impasse ?ti))
   =>
   (modify ?e (tipo-impasse ?ti)))

;; Criterio determinante (§5.9), en este orden: escalat si el impasse del sector se cerró así;
;; si no, el require de la acción aplicada; si no, su better de deliberación (o chunk); si no,
;; su better de regla; con varios, el del objetivo más prioritario. Sin nada de eso, nil.

;; Impasse del sector cerrado como escalat: la decisión es la derivación a una persona.
(defrule EXPLICACIO::anotar-criterio-escalat
   (estado-soar (id S0) (fase explicacio))
   ?e <- (episodio (sector ?s) (instante ?t) (criterio-determinante nil))
   (ciclo-temporal (instante ?t))
   (impasse (sector ?s) (estrategia-resolucion escalat))
   =>
   (modify ?e (criterio-determinante escalat)))

;; El require de la acción aplicada con el objetivo más prioritario.
(defrule EXPLICACIO::anotar-criterio-require
   (estado-soar (id S0) (fase explicacio))
   ?e <- (episodio (sector ?s) (instante ?t) (criterio-determinante nil))
   (ciclo-temporal (instante ?t))
   (not (impasse (sector ?s) (estrategia-resolucion escalat)))
   (operador-candidato (id ?c) (sector ?s) (estado-candidato aplicat))
   (preferencia (tipo-preferencia require) (operador-referencia ?c) (criterio ?k))
   (objetivo-activo (nombre-objetivo ?k) (prioridad ?p))
   (not (and (preferencia (tipo-preferencia require) (operador-referencia ?c) (criterio ?k2))
             (objetivo-activo (nombre-objetivo ?k2) (prioridad ?p2&:(< ?p2 ?p)))))
   =>
   (modify ?e (criterio-determinante ?k)))

;; Sin require: el better de deliberación o de chunk de la acción aplicada.
(defrule EXPLICACIO::anotar-criterio-deliberacion
   (estado-soar (id S0) (fase explicacio))
   ?e <- (episodio (sector ?s) (instante ?t) (criterio-determinante nil))
   (ciclo-temporal (instante ?t))
   (not (impasse (sector ?s) (estrategia-resolucion escalat)))
   (operador-candidato (id ?c) (sector ?s) (estado-candidato aplicat))
   (not (preferencia (tipo-preferencia require) (operador-referencia ?c)))
   (preferencia (tipo-preferencia better) (operador-referencia ?c) (origen deliberacio|chunk)
                (criterio ?k))
   (objetivo-activo (nombre-objetivo ?k) (prioridad ?p))
   (not (and (preferencia (tipo-preferencia better) (operador-referencia ?c)
                          (origen deliberacio|chunk) (criterio ?k2))
             (objetivo-activo (nombre-objetivo ?k2) (prioridad ?p2&:(< ?p2 ?p)))))
   =>
   (modify ?e (criterio-determinante ?k)))

;; Sin require ni better de deliberación: el better de regla con el objetivo más prioritario.
(defrule EXPLICACIO::anotar-criterio-better
   (estado-soar (id S0) (fase explicacio))
   ?e <- (episodio (sector ?s) (instante ?t) (criterio-determinante nil))
   (ciclo-temporal (instante ?t))
   (not (impasse (sector ?s) (estrategia-resolucion escalat)))
   (operador-candidato (id ?c) (sector ?s) (estado-candidato aplicat))
   (not (preferencia (tipo-preferencia require) (operador-referencia ?c)))
   (not (preferencia (tipo-preferencia better) (operador-referencia ?c) (origen deliberacio|chunk)))
   (preferencia (tipo-preferencia better) (operador-referencia ?c) (origen regla) (criterio ?k))
   (objetivo-activo (nombre-objetivo ?k) (prioridad ?p))
   (not (and (preferencia (tipo-preferencia better) (operador-referencia ?c) (origen regla)
                          (criterio ?k2))
             (objetivo-activo (nombre-objetivo ?k2) (prioridad ?p2&:(< ?p2 ?p)))))
   =>
   (modify ?e (criterio-determinante ?k)))

;; Pérdida de cultivo: el mayor beneficio de cultivo entre los descartados (§5.9).
(defrule EXPLICACIO::anotar-perdida-cultivo
   (estado-soar (id S0) (fase explicacio))
   ?e <- (episodio (sector ?s) (instante ?t) (perdida-cultivo ?pc))
   (ciclo-temporal (instante ?t))
   (operador-candidato (id ?o) (sector ?s) (estado-candidato descartat))
   (valoracion (evalua-operador ?o) (beneficio-cultivo ?b&:(> (nivel-num ?b) (nivel-num ?pc))))
   =>
   (modify ?e (perdida-cultivo ?b)))

;; Pérdida de energía: el mayor beneficio de energía entre los descartados (§5.9).
(defrule EXPLICACIO::anotar-perdida-energia
   (estado-soar (id S0) (fase explicacio))
   ?e <- (episodio (sector ?s) (instante ?t) (perdida-energia ?pe))
   (ciclo-temporal (instante ?t))
   (operador-candidato (id ?o) (sector ?s) (estado-candidato descartat))
   (valoracion (evalua-operador ?o) (beneficio-energia ?b&:(> (nivel-num ?b) (nivel-num ?pe))))
   =>
   (modify ?e (perdida-energia ?b)))

;; Con el episodio completo (ninguna regla anotar-* aplicable), escribe la traza en el
;; router traza: formato del anexo B y §5.9, con las dos vistas del enunciado 3.1.
(defrule EXPLICACIO::imprimir-traza
   (estado-soar (id S0) (fase explicacio))
   (ciclo-temporal (instante ?t))
   (episodio (sector ?s) (instante ?t) (situacion $?sit) (alternativas $?alt) (descartes $?des)
             (restricciones-activas $?ra) (criterio-determinante ?cd) (accion ?a)
             (angulo-ordenado ?ang) (tipo-impasse ?ti) (escalado-humano ?esc)
             (beneficio-cultivo ?bc) (beneficio-energia ?be)
             (perdida-cultivo ?pc) (perdida-energia ?pe))
   ;; anotar-situacion
   (not (and (diagnostico (sector ?s) (tipo-diagnostico ?d) (nivel ?n))
             (test (not (member$ (sym-cat ?d ":" ?n) ?sit)))))
   ;; anotar-alternativa
   (not (operador-candidato (sector ?s) (accion ?x&:(not (member$ ?x ?alt)))))
   ;; anotar-descarte-reject
   (not (and (operador-candidato (id ?o1) (sector ?s) (accion ?a1) (estado-candidato descartat))
             (preferencia (tipo-preferencia reject) (operador-referencia ?o1) (criterio ?k1))
             (test (not (member$ (sym-cat ?a1 ":" ?k1) ?des)))))
   ;; anotar-descarte-better
   (not (and (operador-candidato (id ?o2) (sector ?s) (accion ?a2) (estado-candidato descartat))
             (not (preferencia (tipo-preferencia reject) (operador-referencia ?o2)))
             (preferencia (tipo-preferencia better) (operador-comparado ?o2)
                          (operador-referencia ?d2) (criterio ?k2))
             (not (preferencia (tipo-preferencia reject) (operador-referencia ?d2)))
             (test (not (member$ (sym-cat ?a2 ":" ?k2) ?des)))))
   ;; anotar-descarte-require
   (not (and (operador-candidato (id ?o3) (sector ?s) (accion ?a3) (estado-candidato descartat))
             (not (preferencia (tipo-preferencia reject) (operador-referencia ?o3)))
             (not (and (preferencia (tipo-preferencia better) (operador-comparado ?o3)
                                    (operador-referencia ?d3))
                       (not (preferencia (tipo-preferencia reject) (operador-referencia ?d3)))))
             (preferencia (sector ?s) (tipo-preferencia require) (criterio ?k3))
             (test (not (member$ (sym-cat ?a3 ":" ?k3) ?des)))))
   ;; anotar-restriccion
   (not (preferencia (sector ?s) (restriccion ?r&~nil&:(not (member$ ?r ?ra)))))
   ;; anotar-impasse
   (not (and (test (eq ?ti nil)) (impasse (sector ?s))))
   ;; anotar-criterio-escalat, -require, -deliberacion y -better
   (not (and (test (eq ?cd nil)) (impasse (sector ?s) (estrategia-resolucion escalat))))
   (not (and (test (eq ?cd nil))
             (operador-candidato (id ?c) (sector ?s) (estado-candidato aplicat))
             (preferencia (tipo-preferencia require|better) (operador-referencia ?c))))
   ;; anotar-perdida-cultivo y anotar-perdida-energia
   (not (and (operador-candidato (id ?o4) (sector ?s) (estado-candidato descartat))
             (valoracion (evalua-operador ?o4)
                         (beneficio-cultivo ?b4&:(> (nivel-num ?b4) (nivel-num ?pc))))))
   (not (and (operador-candidato (id ?o5) (sector ?s) (estado-candidato descartat))
             (valoracion (evalua-operador ?o5)
                         (beneficio-energia ?b5&:(> (nivel-num ?b5) (nivel-num ?pe))))))
   =>
   (bind ?entradas (create$))
   (do-for-all-facts ((?h observacion-sensor)) (eq ?h:sector ?s)
      (bind ?entradas (create$ ?entradas
                               (str-cat ?h:variable "=" ?h:valor
                                        (if (eq ?h:calidad ok) then "" else (str-cat " (" ?h:calidad ")"))))))
   (printout traza "Fets d'entrada: t=" ?t ", sector=" ?s ", " (lista ?entradas)
                   ", panell=" (descripcion-panel ?s) crlf)
   (printout traza "Diagnosi: " (lista ?sit) crlf)
   (printout traza "Evidencies: " (lista (evidencias-de ?s)) crlf)
   (printout traza "Candidats: " (lista ?alt) crlf)
   (printout traza "Descartats: " (lista ?des) crlf)
   (printout traza "Impasse: " (descripcion-impasse ?s) crlf)
   (printout traza "Decisio: " ?a "   Criteri: " (if (eq ?cd nil) then "-" else ?cd) crlf)
   (printout traza "Ordre: sector=" ?s ", angle=" ?ang
                   ", escalat a persona: " (if (eq ?esc TRUE) then "si" else "no") crlf)
   (bind ?estres (create$))
   (foreach ?x ?sit
      (if (eq (sub-string 1 6 ?x) "estres") then (bind ?estres (create$ ?estres ?x))))
   (printout traza "Vista agronomica: estres=" (lista ?estres) "; benefici cultiu=" ?bc
                   "; renuncia cultiu=" ?pc crlf)
   (printout traza "Vista energetica: benefici energia=" ?be "; renuncia energia=" ?pe
                   "; restriccions actives: " (lista ?ra) crlf))
