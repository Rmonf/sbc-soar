;;; 09_explicacio.clp: módulo EXPLICACIO, episodio y traza de la decisión (roadmap §5.9).
;;; El episodio se crea en una regla y se completa con reglas acumulativas protegidas con
;;; (not (member$ ...)). La traza la escribe una sola regla, imprimir-traza, que solo se activa
;;; cuando no queda nada por anotar: su LHS niega la condición de cada regla acumulativa.
;;; Así la traza sale completa y una sola vez, sea cual sea la estrategia de agenda.
;;; I1: sin impasses, chunks ni resultado observado (t+1), que llegan en I2–I4. Tampoco
;;; están el descarte por reject ni el cálculo de las pérdidas (mayor beneficio de cultivo y de
;;; energía entre los descartados): en I1 no hay reject ni beneficios de cultivo o energía,
;;; así que serían reglas muertas (§10.1). Llegan en I2 con R1, R3, R5 y orientar-*.

(defmodule EXPLICACIO (import MAIN ?ALL))

;; Orden alfabético para imprimir los multislots como conjuntos (§2.3.11).
(deffunction EXPLICACIO::despues-de (?a ?b)
   (> (str-compare ?a ?b) 0))

;; Multislot ordenado y separado por comas, o "-" si está vacío.
(deffunction EXPLICACIO::lista (?valores)
   (if (= (length$ ?valores) 0) then (return "-"))
   (bind ?texto "")
   (foreach ?v (sort despues-de ?valores)
      (bind ?texto (if (= ?v-index 1) then (str-cat ?v) else (str-cat ?texto ", " ?v))))
   ?texto)

;; Crea el episodio del sector con la acción aplicada, el ángulo previo y los beneficios
;; de la acción elegida; las pérdidas parten de baix, el máximo de un conjunto vacío, y en I1
;; se quedan así porque ningún candidato tiene beneficio de cultivo ni de energía (§5.9).
(defrule EXPLICACIO::crear-episodio
   (estado-soar (id S0) (fase explicacio))
   (ciclo-temporal (instante ?t))
   (operador-candidato (id ?c) (sector ?s) (accion ?a) (estado-candidato aplicat))
   (orden-actuador (sector ?s) (instante ?t) (angulo-ordenado ?ang) (escalado-humano ?esc))
   (observacion-panel (sector ?s) (angulo-actual ?previo))
   (valoracion (evalua-operador ?c) (beneficio-cultivo ?bc) (beneficio-energia ?be))
   =>
   (assert (episodio (id (sym-cat episodio- ?s "-" ?t)) (sector ?s) (instante ?t) (accion ?a)
                     (angulo-previo ?previo) (angulo-ordenado ?ang)
                     (beneficio-cultivo ?bc) (beneficio-energia ?be)
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

;; Criterio determinante: el del require de la acción aplicada (§5.9).
(defrule EXPLICACIO::anotar-criterio-require
   (estado-soar (id S0) (fase explicacio))
   ?e <- (episodio (sector ?s) (instante ?t) (criterio-determinante nil))
   (ciclo-temporal (instante ?t))
   (operador-candidato (id ?c) (sector ?s) (estado-candidato aplicat))
   (preferencia (tipo-preferencia require) (operador-referencia ?c) (criterio ?k))
   =>
   (modify ?e (criterio-determinante ?k)))

;; Sin require: el criterio del better de la acción aplicada con el objetivo más prioritario (§5.9).
(defrule EXPLICACIO::anotar-criterio-better
   (estado-soar (id S0) (fase explicacio))
   ?e <- (episodio (sector ?s) (instante ?t) (criterio-determinante nil))
   (ciclo-temporal (instante ?t))
   (operador-candidato (id ?c) (sector ?s) (estado-candidato aplicat))
   (not (preferencia (tipo-preferencia require) (operador-referencia ?c)))
   (preferencia (tipo-preferencia better) (operador-referencia ?c) (criterio ?k))
   (objetivo-activo (nombre-objetivo ?k) (prioridad ?p))
   (not (and (preferencia (tipo-preferencia better) (operador-referencia ?c) (criterio ?k2))
             (objetivo-activo (nombre-objetivo ?k2) (prioridad ?p2&:(< ?p2 ?p)))))
   =>
   (modify ?e (criterio-determinante ?k)))

;; Con el episodio completo (ninguna regla anotar-* aplicable), escribe la traza en el
;; router traza: formato del anexo B y §5.9, con las dos vistas del enunciado 3.1.
(defrule EXPLICACIO::imprimir-traza
   (estado-soar (id S0) (fase explicacio))
   (ciclo-temporal (instante ?t))
   (episodio (sector ?s) (instante ?t) (situacion $?sit) (alternativas $?alt) (descartes $?des)
             (restricciones-activas $?ra) (criterio-determinante ?cd) (accion ?a)
             (angulo-previo ?previo) (angulo-ordenado ?ang)
             (beneficio-cultivo ?bc) (beneficio-energia ?be)
             (perdida-cultivo ?pc) (perdida-energia ?pe))
   (observacion-panel (sector ?s) (estado-mecanico ?em) (ocupacion ?oc))
   ;; anotar-situacion
   (not (and (diagnostico (sector ?s) (tipo-diagnostico ?d) (nivel ?n))
             (test (not (member$ (sym-cat ?d ":" ?n) ?sit)))))
   ;; anotar-alternativa
   (not (operador-candidato (sector ?s) (accion ?x&:(not (member$ ?x ?alt)))))
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
   ;; anotar-criterio-require y anotar-criterio-better
   (not (and (test (eq ?cd nil))
             (operador-candidato (id ?c) (sector ?s) (estado-candidato aplicat))
             (preferencia (tipo-preferencia require|better) (operador-referencia ?c))))
   =>
   (bind ?entradas (create$))
   (do-for-all-facts ((?h observacion-sensor)) (eq ?h:sector ?s)
      (bind ?entradas (create$ ?entradas (str-cat ?h:variable "=" ?h:valor))))
   (printout traza "Fets d'entrada: t=" ?t ", sector=" ?s ", " (lista ?entradas)
                   ", panell=" ?previo " (" ?em ", " ?oc ")" crlf)
   (printout traza "Diagnosi: " (lista ?sit) crlf)
   (printout traza "Candidats: " (lista ?alt) crlf)
   (printout traza "Descartats: " (lista ?des) crlf)
   (printout traza "Decisio: " ?a "   Criteri: " (if (eq ?cd nil) then "-" else ?cd) crlf)
   (printout traza "Ordre: sector=" ?s ", angle=" ?ang crlf)
   (printout traza "Vista agronomica: benefici cultiu=" ?bc "; renuncia cultiu=" ?pc crlf)
   (printout traza "Vista energetica: benefici energia=" ?be "; renuncia energia=" ?pe
                   "; restriccions actives: " (lista ?ra) crlf))
