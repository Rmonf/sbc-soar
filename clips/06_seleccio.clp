;;; 06_seleccio.clp: SELECCIO. Procedimiento de decisión: elige, aplica un chunk o declara un
;;; impasse. "No dominado" = ni rechazado ni con un better en contra de un candidato no rechazado.
;;; Las condiciones son patrones para que las reglas reaccionen a las preferencias nuevas
;;; (las del chunk y las de la deliberación).

(defmodule SELECCIO (import MAIN ?ALL))

;; SOAR: procedimiento de decisión. Un único candidato no dominado, con datos suficientes o con el
;; impasse del sector ya resuelto: se elige.
(defrule SELECCIO::s4-elegir
   (estado-soar (id S0) (fase seleccio))
   ?c <- (operador-candidato (id ?o) (sector ?s) (estado-candidato candidat))
   (not (preferencia (tipo-preferencia reject) (operador-referencia ?o)))
   (not (and (preferencia (tipo-preferencia better) (operador-comparado ?o) (operador-referencia ?d))
             (not (preferencia (tipo-preferencia reject) (operador-referencia ?d)))))
   (not (and (operador-candidato (id ?o2&~?o) (sector ?s) (estado-candidato candidat))
             (not (preferencia (tipo-preferencia reject) (operador-referencia ?o2)))
             (not (and (preferencia (tipo-preferencia better) (operador-comparado ?o2) (operador-referencia ?d2))
                       (not (preferencia (tipo-preferencia reject) (operador-referencia ?d2)))))))
   (not (and (diagnostico (sector ?s) (tipo-diagnostico incertesa-dades) (nivel critic))
             (not (impasse (sector ?s) (resuelto TRUE)))))
   =>
   (modify ?c (estado-candidato seleccionat)))

;; SOAR: procedimiento de decisión. Elegido uno, los demás candidatos del sector se descartan.
(defrule SELECCIO::descartar-resto
   (estado-soar (id S0) (fase seleccio))
   (operador-candidato (sector ?s) (estado-candidato seleccionat))
   ?c <- (operador-candidato (sector ?s) (estado-candidato candidat))
   =>
   (modify ?c (estado-candidato descartat)))

;; SOAR: impasse por falta de datos. Falta un dato crítico (o el panel): no se puede elegir.
(defrule SELECCIO::s1-dades-insuficients
   (estado-soar (id S0) (fase seleccio))
   (ciclo-temporal (instante ?t))
   (sector (id ?s))
   (exists (diagnostico (sector ?s) (tipo-diagnostico incertesa-dades) (nivel critic)))
   (not (impasse (sector ?s)))
   =>
   (assert (impasse (id (sym-cat impasse- ?s - ?t)) (en-estado S0) (sector ?s)
                    (tipo-impasse dades-insuficients) (operadores-en-conflicto (no-dominados ?s))
                    (resuelto FALSE))))

;; SOAR: chunk aplicado. Exactamente dos candidatos no dominados y un chunk aprendido para la pareja:
;; better con origen chunk, sin impasse. Después decide s4-elegir.
(defrule SELECCIO::s5-aplicar-chunk
   (estado-soar (id S0) (fase seleccio))
   (operador-candidato (id ?a) (sector ?s) (estado-candidato candidat))
   (not (preferencia (tipo-preferencia reject) (operador-referencia ?a)))
   (not (and (preferencia (tipo-preferencia better) (operador-comparado ?a) (operador-referencia ?d))
             (not (preferencia (tipo-preferencia reject) (operador-referencia ?d)))))
   (operador-candidato (id ?b&~?a) (sector ?s) (estado-candidato candidat))
   (not (preferencia (tipo-preferencia reject) (operador-referencia ?b)))
   (not (and (preferencia (tipo-preferencia better) (operador-comparado ?b) (operador-referencia ?e))
             (not (preferencia (tipo-preferencia reject) (operador-referencia ?e)))))
   (not (and (operador-candidato (id ?o&~?a&~?b) (sector ?s) (estado-candidato candidat))
             (not (preferencia (tipo-preferencia reject) (operador-referencia ?o)))
             (not (and (preferencia (tipo-preferencia better) (operador-comparado ?o) (operador-referencia ?f))
                       (not (preferencia (tipo-preferencia reject) (operador-referencia ?f)))))))
   (not (diagnostico (sector ?s) (tipo-diagnostico incertesa-dades) (nivel critic)))
   (not (impasse (sector ?s)))
   (test (chunk-aplicable ?a ?b))
   =>
   (bind ?k (chunk-aplicable ?a ?b))
   (assert (preferencia (sector ?s) (tipo-preferencia better) (operador-referencia ?a) (operador-comparado ?b)
                        (criterio (fact-slot-value ?k criterio)) (origen chunk)
                        (chunk-aplicado (fact-slot-value ?k id)))))

;; SOAR: impasse tie. Dos o más candidatos no dominados (zona gris) y ningún chunk para la pareja.
(defrule SELECCIO::s6-tie
   (estado-soar (id S0) (fase seleccio))
   (ciclo-temporal (instante ?t))
   (operador-candidato (id ?a) (sector ?s) (estado-candidato candidat))
   (not (preferencia (tipo-preferencia reject) (operador-referencia ?a)))
   (not (and (preferencia (tipo-preferencia better) (operador-comparado ?a) (operador-referencia ?d))
             (not (preferencia (tipo-preferencia reject) (operador-referencia ?d)))))
   (operador-candidato (id ?b&~?a) (sector ?s) (estado-candidato candidat))
   (not (preferencia (tipo-preferencia reject) (operador-referencia ?b)))
   (not (and (preferencia (tipo-preferencia better) (operador-comparado ?b) (operador-referencia ?e))
             (not (preferencia (tipo-preferencia reject) (operador-referencia ?e)))))
   (not (diagnostico (sector ?s) (tipo-diagnostico incertesa-dades) (nivel critic)))
   (not (impasse (sector ?s)))
   (test (not (chunk-aplicable ?a ?b)))
   (test (not (chunk-aplicable ?b ?a)))
   =>
   (assert (impasse (id (sym-cat impasse- ?s - ?t)) (en-estado S0) (sector ?s) (tipo-impasse tie)
                    (operadores-en-conflicto (no-dominados ?s)) (resuelto FALSE))))
