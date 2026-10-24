;;; 03_elaboracio.clp: módulo ELABORACIO, abstracción → diagnóstico (roadmap §5.3).
;;; I1: solo la referencia seguidor (vent) y el diagnóstico risc-mecanic; las referencias
;;; absoluta y cultiu y el resto de diagnósticos llegan en I2.

(defmodule ELABORACIO (import MAIN ?ALL))

;; Nivel de una variable con referencia al seguidor: delta = valor − umbral-viento-critico.
;; Las lecturas con calidad fallada no se abstraen: son datos desconocidos (§5.3).
(defrule ELABORACIO::abstraer-ref-seguidor
   (estado-soar (id S0) (fase elaboracio))
   (observacion-sensor (sector ?s) (variable ?v) (valor ?x) (calidad ~fallada))
   (sector (id ?s) (tiene-seguidor ?sg))
   (seguidor-solar (id ?sg) (umbral-viento-critico ?u))
   (umbral (variable ?v) (referencia seguidor) (nivel ?n)
           (limite-inferior ?inf) (limite-superior ?sup))
   (test (dins-interval (- ?x ?u) ?inf ?sup))
   =>
   (assert (abstraccion (sector ?s) (variable ?v) (nivel ?n))))

;; Viento ≥ alt: diagnóstico risc-mecanic con el nivel del viento, uno por sector (§5.3, §2.3.10).
(defrule ELABORACIO::diagnosticar-risc-mecanic
   (estado-soar (id S0) (fase elaboracio))
   (abstraccion (sector ?s) (variable vent) (nivel ?n&:(>= (nivel-num ?n) (nivel-num alt))))
   (not (diagnostico (sector ?s) (tipo-diagnostico risc-mecanic)))
   =>
   (assert (diagnostico (id (sym-cat ?s "-risc-mecanic")) (sector ?s)
                        (tipo-diagnostico risc-mecanic) (nivel ?n)
                        (evidencias (sym-cat vent ":" ?n)))))
