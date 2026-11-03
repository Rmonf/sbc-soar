;;; 03_elaboracio.clp: ELABORACIO. Lecturas → niveles (umbrales del TTL) → diagnósticos.

(defmodule ELABORACIO (import MAIN ?ALL))

;; SOAR: elaboración. Nivel de una lectura con umbral absoluto.
(defrule ELABORACIO::abstraer-absoluta
   (estado-soar (id S0) (fase elaboracio))
   (observacion-sensor (sector ?s) (variable ?v) (valor ?x) (calidad ~fallada))
   (umbral (variable ?v) (referencia absoluta) (nivel ?n) (limite-inferior ?li) (limite-superior ?ls))
   (test (dins-interval ?x ?li ?ls))
   =>
   (assert (abstraccion (sector ?s) (variable ?v) (nivel ?n))))

;; SOAR: elaboración. Nivel de la diferencia con el umbral del cultivo del sector
;; (temp-cultiu con umbral-temp-estres, humitat-sol con umbral-humedad-critica).
(defrule ELABORACIO::abstraer-cultiu
   (estado-soar (id S0) (fase elaboracio))
   (observacion-sensor (sector ?s) (variable ?v) (valor ?x) (calidad ~fallada))
   (umbral (variable ?v) (referencia cultiu) (nivel ?n) (limite-inferior ?li) (limite-superior ?ls))
   (sector (id ?s) (tiene-cultivo ?c))
   (cultivo (id ?c) (umbral-temp-estres ?ut) (umbral-humedad-critica ?uh))
   (test (dins-interval (- ?x (if (eq ?v temp-cultiu) then ?ut else ?uh)) ?li ?ls))
   =>
   (assert (abstraccion (sector ?s) (variable ?v) (nivel ?n))))

;; SOAR: elaboración. Nivel de la diferencia con el umbral de viento crítico del seguidor.
(defrule ELABORACIO::abstraer-seguidor
   (estado-soar (id S0) (fase elaboracio))
   (observacion-sensor (sector ?s) (variable ?v) (valor ?x) (calidad ~fallada))
   (umbral (variable ?v) (referencia seguidor) (nivel ?n) (limite-inferior ?li) (limite-superior ?ls))
   (sector (id ?s) (tiene-seguidor ?g))
   (seguidor-solar (id ?g) (umbral-viento-critico ?u))
   (test (dins-interval (- ?x ?u) ?li ?ls))
   =>
   (assert (abstraccion (sector ?s) (variable ?v) (nivel ?n))))

;; SOAR: elaboración. Viento alt o critic: riesgo mecánico.
(defrule ELABORACIO::risc-mecanic
   (estado-soar (id S0) (fase elaboracio))
   (abstraccion (sector ?s) (variable vent) (nivel ?n&alt|critic))
   =>
   (assert (diagnostico (sector ?s) (tipo-diagnostico risc-mecanic) (nivel ?n) (evidencias (sym-cat vent: ?n)))))

;; SOAR: elaboración con una predicción (anticipación). Viento previsto a 30 minutos alt o critic,
;; con los umbrales del viento: riesgo mecánico.
(defrule ELABORACIO::risc-mecanic-previst
   (estado-soar (id S0) (fase elaboracio))
   (prediccion (sector ?s) (variable vent-previst) (valor ?x))
   (sector (id ?s) (tiene-seguidor ?g))
   (seguidor-solar (id ?g) (umbral-viento-critico ?u))
   (umbral (variable vent) (referencia seguidor) (nivel ?n&alt|critic) (limite-inferior ?li) (limite-superior ?ls))
   (test (dins-interval (- ?x ?u) ?li ?ls))
   =>
   (assert (diagnostico (sector ?s) (tipo-diagnostico risc-mecanic) (nivel ?n) (evidencias (sym-cat vent-previst: ?n)))))

;; SOAR: elaboración. Temperatura del cultivo cerca o por encima de su umbral: estrés térmico.
(defrule ELABORACIO::estres-termic
   (estado-soar (id S0) (fase elaboracio))
   (abstraccion (sector ?s) (variable temp-cultiu) (nivel ?n&~baix))
   =>
   (assert (diagnostico (sector ?s) (tipo-diagnostico estres-termic) (nivel ?n) (evidencias (sym-cat temp-cultiu: ?n)))))

;; SOAR: elaboración. Humedad del suelo cerca o por debajo de su umbral: estrés hídrico.
(defrule ELABORACIO::estres-hidric
   (estado-soar (id S0) (fase elaboracio))
   (abstraccion (sector ?s) (variable humitat-sol) (nivel ?n&~baix))
   =>
   (assert (diagnostico (sector ?s) (tipo-diagnostico estres-hidric) (nivel ?n) (evidencias (sym-cat humitat-sol: ?n)))))

;; SOAR: elaboración. Radiación mitja o más: oportunidad de producir energía.
(defrule ELABORACIO::oportunitat-energetica
   (estado-soar (id S0) (fase elaboracio))
   (abstraccion (sector ?s) (variable radiacio) (nivel ?n&~baix))
   =>
   (assert (diagnostico (sector ?s) (tipo-diagnostico oportunitat-energetica) (nivel ?n) (evidencias (sym-cat radiacio: ?n)))))

;; SOAR: elaboración. Personas bajo los paneles.
(defrule ELABORACIO::risc-persones
   (estado-soar (id S0) (fase elaboracio))
   (observacion-panel (sector ?s) (ocupacion ?o&~lliure))
   =>
   (assert (diagnostico (sector ?s) (tipo-diagnostico risc-persones) (nivel critic) (evidencias (sym-cat ocupacio: ?o)))))

;; SOAR: elaboración. El seguidor informa de un estado mecánico anómalo.
(defrule ELABORACIO::fallada-actuador
   (estado-soar (id S0) (fase elaboracio))
   (observacion-panel (sector ?s) (estado-mecanico ?m&~operatiu))
   =>
   (assert (diagnostico (sector ?s) (tipo-diagnostico fallada-actuador) (nivel alt) (evidencias (sym-cat estat: ?m)))))
