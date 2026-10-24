;;; 01_percepcio.clp: módulo PERCEPCIO, validación de los datos observados (roadmap §5.1).
;;; Por sector y dato-requerido: un dato que falta, con calidad fallada o con instante anterior
;;; al ciclo da incertesa-dades con el nivel del dato; una lectura degradat, incertesa baix;
;;; sin observacion-panel vigente (ausente, o con instante anterior al ciclo), incertesa critic. Un solo diagnóstico por sector (§2.3.10): una regla
;;; lo crea en baix, el máximo de un conjunto vacío, y cada causa añade su evidencia y eleva el
;;; nivel al máximo. El resultado no depende del orden de disparo.

(defmodule PERCEPCIO (import MAIN ?ALL))

;; Algún dato del sector falta, está fallado, es antiguo o degradado, o falta el panel:
;; se crea la incertesa-dades del sector (§5.1, §2.3.10).
(defrule PERCEPCIO::crear-incertesa
   (estado-soar (id S0) (fase percepcio))
   (ciclo-temporal (instante ?t))
   (sector (id ?s))
   (or (and (dato-requerido (variable ?v))
            (not (observacion-sensor (sector ?s) (variable ?v))))
       (and (dato-requerido (variable ?v))
            (observacion-sensor (sector ?s) (variable ?v) (calidad fallada)))
       (and (dato-requerido (variable ?v))
            (observacion-sensor (sector ?s) (variable ?v) (instante ?i&:(< ?i ?t))))
       (observacion-sensor (sector ?s) (calidad degradat))
       (not (observacion-panel (sector ?s) (instante ?t))))
   (not (diagnostico (sector ?s) (tipo-diagnostico incertesa-dades)))
   =>
   (assert (diagnostico (id (sym-cat ?s "-incertesa-dades")) (sector ?s)
                        (tipo-diagnostico incertesa-dades) (nivel baix))))

;; Dato requerido sin observación: evidencia variable:absent y nivel del dato (§5.1).
(defrule PERCEPCIO::anotar-dato-absent
   (estado-soar (id S0) (fase percepcio))
   (dato-requerido (variable ?v) (nivel ?n))
   (sector (id ?s))
   (not (observacion-sensor (sector ?s) (variable ?v)))
   ?d <- (diagnostico (sector ?s) (tipo-diagnostico incertesa-dades) (nivel ?actual)
                      (evidencias $?ev&:(not (member$ (sym-cat ?v ":absent") ?ev))))
   =>
   (modify ?d (nivel (nivel-max ?actual ?n)) (evidencias ?ev (sym-cat ?v ":absent"))))

;; Dato requerido con calidad fallada: evidencia variable:fallada y nivel del dato (§5.1).
(defrule PERCEPCIO::anotar-dato-fallada
   (estado-soar (id S0) (fase percepcio))
   (dato-requerido (variable ?v) (nivel ?n))
   (observacion-sensor (sector ?s) (variable ?v) (calidad fallada))
   ?d <- (diagnostico (sector ?s) (tipo-diagnostico incertesa-dades) (nivel ?actual)
                      (evidencias $?ev&:(not (member$ (sym-cat ?v ":fallada") ?ev))))
   =>
   (modify ?d (nivel (nivel-max ?actual ?n)) (evidencias ?ev (sym-cat ?v ":fallada"))))

;; Dato requerido con instante anterior al ciclo: evidencia variable:antiga y nivel del dato (§5.1).
(defrule PERCEPCIO::anotar-dato-antiga
   (estado-soar (id S0) (fase percepcio))
   (ciclo-temporal (instante ?t))
   (dato-requerido (variable ?v) (nivel ?n))
   (observacion-sensor (sector ?s) (variable ?v) (instante ?i&:(< ?i ?t)))
   ?d <- (diagnostico (sector ?s) (tipo-diagnostico incertesa-dades) (nivel ?actual)
                      (evidencias $?ev&:(not (member$ (sym-cat ?v ":antiga") ?ev))))
   =>
   (modify ?d (nivel (nivel-max ?actual ?n)) (evidencias ?ev (sym-cat ?v ":antiga"))))

;; Lectura degradada: evidencia variable:degradat, solo informativa (nivel baix, §5.1).
(defrule PERCEPCIO::anotar-dato-degradat
   (estado-soar (id S0) (fase percepcio))
   (observacion-sensor (sector ?s) (variable ?v) (calidad degradat))
   ?d <- (diagnostico (sector ?s) (tipo-diagnostico incertesa-dades)
                      (evidencias $?ev&:(not (member$ (sym-cat ?v ":degradat") ?ev))))
   =>
   (modify ?d (evidencias ?ev (sym-cat ?v ":degradat"))))

;; Sin ninguna observacion-panel, el ángulo y la ocupación son desconocidos: incertesa critic (§5.1).
(defrule PERCEPCIO::anotar-panel-absent
   (estado-soar (id S0) (fase percepcio))
   (sector (id ?s))
   (not (observacion-panel (sector ?s)))
   ?d <- (diagnostico (sector ?s) (tipo-diagnostico incertesa-dades)
                      (evidencias $?ev&:(not (member$ observacio-panel:absent ?ev))))
   =>
   (modify ?d (nivel critic) (evidencias ?ev observacio-panel:absent)))

;; observacion-panel antigua (instante anterior al ciclo) y ninguna vigente: el ángulo y la
;; ocupación son desconocidos, como si faltara: incertesa critic (§5.1).
(defrule PERCEPCIO::anotar-panel-antiga
   (estado-soar (id S0) (fase percepcio))
   (ciclo-temporal (instante ?t))
   (observacion-panel (sector ?s) (instante ?i&:(< ?i ?t)))
   (not (observacion-panel (sector ?s) (instante ?t)))
   ?d <- (diagnostico (sector ?s) (tipo-diagnostico incertesa-dades)
                      (evidencias $?ev&:(not (member$ observacio-panel:antiga ?ev))))
   =>
   (modify ?d (nivel critic) (evidencias ?ev observacio-panel:antiga)))
