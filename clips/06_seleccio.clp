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
