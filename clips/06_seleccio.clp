;;; 06_seleccio.clp: módulo SELECCIO, procedimiento de decisión por sector (roadmap §5.6).
;;; I1: S3 (requerido) y S4 (único no dominado). Rechazado = tiene un reject; dominado = hay
;;; un better sobre él emitido por un candidato no rechazado. S1, S2, S6, S7 y B(s) llegan
;;; en I2; S5 (chunk), en I4.

(defmodule SELECCIO (import MAIN ?ALL))

;; S3: exactamente un candidato con require, y no rechazado, se selecciona (§5.6).
(defrule SELECCIO::s3-seleccionar-requerido
   (estado-soar (id S0) (fase seleccio))
   (preferencia (sector ?s) (tipo-preferencia require) (operador-referencia ?c))
   ?f <- (operador-candidato (id ?c) (estado-candidato candidat))
   (not (preferencia (tipo-preferencia reject) (operador-referencia ?c)))
   (not (preferencia (sector ?s) (tipo-preferencia require) (operador-referencia ~?c)))
   (not (operador-candidato (sector ?s) (estado-candidato seleccionat)))
   =>
   (modify ?f (estado-candidato seleccionat)))

;; S4: sin requeridos no rechazados, el único candidato no dominado se selecciona (§5.6).
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
