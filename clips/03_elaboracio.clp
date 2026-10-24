;;; 03_elaboracio.clp: módulo ELABORACIO, abstracción → diagnóstico → refinamiento (roadmap §5.3).
;;; Abstracción: tres reglas para observaciones, una por referencia, que ignoran las lecturas
;;; fallada o antiguas (son datos desconocidos), y tres para predicciones (por sector con
;;; referencia absoluta o seguidor, y global, que se abstrae para cada sector). Diagnósticos:
;;; uno por sector y tipo (§2.3.10). Los refinamientos que solo suben de nivel se aplican al
;;; crear o con evidencia + máximo; la rebaja por lluvia de estres-hidric espera a que todas las
;;; lluvias del sector estén abstraídas, para no depender del orden de disparo.

(defmodule ELABORACIO (import MAIN ?ALL))

;;; --- Abstracción de observaciones (§5.3) ----------------------------------

;; Referencia absoluta: el nivel del valor observado (§5.3).
(defrule ELABORACIO::abstraer-ref-absoluta
   (estado-soar (id S0) (fase elaboracio))
   (ciclo-temporal (instante ?t))
   (observacion-sensor (sector ?s) (variable ?v) (valor ?x) (calidad ~fallada) (instante ?t))
   (umbral (variable ?v) (referencia absoluta) (nivel ?n) (limite-inferior ?inf) (limite-superior ?sup))
   (test (dins-interval ?x ?inf ?sup))
   =>
   (assert (abstraccion (sector ?s) (variable ?v) (nivel ?n))))

;; Referencia cultiu: delta = valor − umbral del cultivo (temperatura de estrés o humedad
;; crítica) (§5.3).
(defrule ELABORACIO::abstraer-ref-cultiu
   (estado-soar (id S0) (fase elaboracio))
   (ciclo-temporal (instante ?t))
   (observacion-sensor (sector ?s) (variable ?v) (valor ?x) (calidad ~fallada) (instante ?t))
   (sector (id ?s) (tiene-cultivo ?cu))
   (cultivo (id ?cu) (umbral-temp-estres ?ute) (umbral-humedad-critica ?uhc))
   (umbral (variable ?v) (referencia cultiu) (nivel ?n) (limite-inferior ?inf) (limite-superior ?sup))
   (test (dins-interval (- ?x (if (eq ?v temp-cultiu) then ?ute else ?uhc)) ?inf ?sup))
   =>
   (assert (abstraccion (sector ?s) (variable ?v) (nivel ?n))))

;; Referencia seguidor: delta = valor − umbral-viento-critico (§5.3).
(defrule ELABORACIO::abstraer-ref-seguidor
   (estado-soar (id S0) (fase elaboracio))
   (ciclo-temporal (instante ?t))
   (observacion-sensor (sector ?s) (variable ?v) (valor ?x) (calidad ~fallada) (instante ?t))
   (sector (id ?s) (tiene-seguidor ?sg))
   (seguidor-solar (id ?sg) (umbral-viento-critico ?u))
   (umbral (variable ?v) (referencia seguidor) (nivel ?n) (limite-inferior ?inf) (limite-superior ?sup))
   (test (dins-interval (- ?x ?u) ?inf ?sup))
   =>
   (assert (abstraccion (sector ?s) (variable ?v) (nivel ?n))))

;;; --- Abstracción de predicciones (§5.3) -----------------------------------

;; Predicción de un sector con referencia absoluta (pluja-prevista) (§5.3).
(defrule ELABORACIO::abstraer-prediccion-absoluta
   (estado-soar (id S0) (fase elaboracio))
   (prediccion (sector ?s&~nil) (variable ?v) (valor ?x))
   (umbral (variable ?v) (referencia absoluta) (nivel ?n) (limite-inferior ?inf) (limite-superior ?sup))
   (test (dins-interval ?x ?inf ?sup))
   =>
   (assert (abstraccion (sector ?s) (variable ?v) (nivel ?n))))

;; Predicción de un sector con referencia al seguidor (vent-previst) (§5.3).
(defrule ELABORACIO::abstraer-prediccion-seguidor
   (estado-soar (id S0) (fase elaboracio))
   (prediccion (sector ?s&~nil) (variable ?v) (valor ?x))
   (sector (id ?s) (tiene-seguidor ?sg))
   (seguidor-solar (id ?sg) (umbral-viento-critico ?u))
   (umbral (variable ?v) (referencia seguidor) (nivel ?n) (limite-inferior ?inf) (limite-superior ?sup))
   (test (dins-interval (- ?x ?u) ?inf ?sup))
   =>
   (assert (abstraccion (sector ?s) (variable ?v) (nivel ?n))))

;; Predicción global (sin sector, p. ej. preu-energia): se abstrae para cada sector (§5.3).
(defrule ELABORACIO::abstraer-prediccion-global
   (estado-soar (id S0) (fase elaboracio))
   (prediccion (sector nil) (variable ?v) (valor ?x))
   (sector (id ?s))
   (umbral (variable ?v) (referencia absoluta) (nivel ?n) (limite-inferior ?inf) (limite-superior ?sup))
   (test (dins-interval ?x ?inf ?sup))
   =>
   (assert (abstraccion (sector ?s) (variable ?v) (nivel ?n))))

;;; --- Diagnósticos (§5.3) ---------------------------------------------------

;; Viento observado o previsto ≥ alt: risc-mecanic con su nivel (§5.3).
(defrule ELABORACIO::diagnosticar-risc-mecanic
   (estado-soar (id S0) (fase elaboracio))
   (abstraccion (sector ?s) (variable ?v&vent|vent-previst)
                (nivel ?n&:(>= (nivel-num ?n) (nivel-num alt))))
   (not (diagnostico (sector ?s) (tipo-diagnostico risc-mecanic)))
   =>
   (assert (diagnostico (id (sym-cat ?s "-risc-mecanic")) (sector ?s)
                        (tipo-diagnostico risc-mecanic) (nivel ?n)
                        (evidencias (sym-cat ?v ":" ?n)))))

;; Otra fuente de viento ≥ alt: añade evidencia y eleva al máximo de vent y vent-previst (§5.3, §2.3.10).
(defrule ELABORACIO::reforzar-risc-mecanic
   (estado-soar (id S0) (fase elaboracio))
   (abstraccion (sector ?s) (variable ?v&vent|vent-previst)
                (nivel ?n&:(>= (nivel-num ?n) (nivel-num alt))))
   ?d <- (diagnostico (sector ?s) (tipo-diagnostico risc-mecanic) (nivel ?actual)
                      (evidencias $?ev&:(not (member$ (sym-cat ?v ":" ?n) ?ev))))
   =>
   (modify ?d (nivel (nivel-max ?actual ?n)) (evidencias ?ev (sym-cat ?v ":" ?n))))

;; Temperatura del cultivo ≥ mitja: estres-termic, +1 nivel si la sensibilidad es ≥ alt (§5.3).
(defrule ELABORACIO::diagnosticar-estres-termic
   (estado-soar (id S0) (fase elaboracio))
   (abstraccion (sector ?s) (variable temp-cultiu) (nivel ?n&:(>= (nivel-num ?n) (nivel-num mitja))))
   (sector (id ?s) (tiene-cultivo ?cu))
   (cultivo (id ?cu) (sensibilidad ?sens))
   (not (diagnostico (sector ?s) (tipo-diagnostico estres-termic)))
   =>
   (bind ?sube (>= (nivel-num ?sens) (nivel-num alt)))
   (assert (diagnostico (id (sym-cat ?s "-estres-termic")) (sector ?s)
                        (tipo-diagnostico estres-termic)
                        (nivel (nivel-desplazado ?n (if ?sube then 1 else 0)))
                        (evidencias (sym-cat temp-cultiu ":" ?n)
                                    (if ?sube then (sym-cat sensibilitat ":" ?sens) else (create$))))))

;; Humedad del suelo ≥ mitja: estres-hidric, +1 nivel con sensibilidad ≥ alt y −1 con pluja o
;; pluja-prevista ≥ alt; solo si el nivel final sigue ≥ mitja (§5.3). Espera a que toda lluvia
;; vigente del sector esté abstraída: la rebaja depende de que no haya lluvia ≥ alt.
(defrule ELABORACIO::diagnosticar-estres-hidric
   (estado-soar (id S0) (fase elaboracio))
   (ciclo-temporal (instante ?t))
   (abstraccion (sector ?s) (variable humitat-sol) (nivel ?n&:(>= (nivel-num ?n) (nivel-num mitja))))
   (sector (id ?s) (tiene-cultivo ?cu))
   (cultivo (id ?cu) (sensibilidad ?sens))
   (not (diagnostico (sector ?s) (tipo-diagnostico estres-hidric)))
   ;; guarda: toda lluvia observada o prevista (del sector o global) ya está abstraída
   (not (and (observacion-sensor (sector ?s) (variable pluja) (calidad ~fallada) (instante ?t))
             (not (abstraccion (sector ?s) (variable pluja)))))
   (not (and (prediccion (sector ?s|nil) (variable pluja-prevista))
             (not (abstraccion (sector ?s) (variable pluja-prevista)))))
   =>
   (bind ?lluvias (create$))
   (do-for-all-facts ((?a abstraccion))
         (and (eq ?a:sector ?s) (member$ ?a:variable (create$ pluja pluja-prevista))
              (>= (nivel-num ?a:nivel) (nivel-num alt)))
      (bind ?lluvias (create$ ?lluvias (sym-cat ?a:variable ":" ?a:nivel))))
   (bind ?sube (>= (nivel-num ?sens) (nivel-num alt)))
   (bind ?final (nivel-desplazado ?n (- (if ?sube then 1 else 0)
                                        (if (> (length$ ?lluvias) 0) then 1 else 0))))
   (if (>= (nivel-num ?final) (nivel-num mitja)) then
      (assert (diagnostico (id (sym-cat ?s "-estres-hidric")) (sector ?s)
                           (tipo-diagnostico estres-hidric) (nivel ?final)
                           (evidencias (sym-cat humitat-sol ":" ?n)
                                       (if ?sube then (sym-cat sensibilitat ":" ?sens) else (create$))
                                       ?lluvias)))))

;; Ocupación observada distinta de lliure en el panel vigente: risc-persones critic (§5.3). Una
;; ocupación antigua es desconocida.
(defrule ELABORACIO::diagnosticar-risc-persones
   (estado-soar (id S0) (fase elaboracio))
   (ciclo-temporal (instante ?t))
   (observacion-panel (sector ?s) (ocupacion ?o&~lliure) (instante ?t))
   =>
   (assert (diagnostico (id (sym-cat ?s "-risc-persones")) (sector ?s)
                        (tipo-diagnostico risc-persones) (nivel critic)
                        (evidencias (sym-cat ocupacio ":" ?o)))))

;; Radiación ≥ mitja: oportunitat-energetica con su nivel (§5.3).
(defrule ELABORACIO::diagnosticar-oportunitat-energetica
   (estado-soar (id S0) (fase elaboracio))
   (abstraccion (sector ?s) (variable radiacio) (nivel ?n&:(>= (nivel-num ?n) (nivel-num mitja))))
   (not (diagnostico (sector ?s) (tipo-diagnostico oportunitat-energetica)))
   =>
   (assert (diagnostico (id (sym-cat ?s "-oportunitat-energetica")) (sector ?s)
                        (tipo-diagnostico oportunitat-energetica) (nivel ?n)
                        (evidencias (sym-cat radiacio ":" ?n)))))

;; Precio de la energía ≥ alt: la oportunidad sube un nivel, una sola vez (evidencia) (§5.3).
(defrule ELABORACIO::refinar-oportunitat-preu
   (estado-soar (id S0) (fase elaboracio))
   (abstraccion (sector ?s) (variable preu-energia) (nivel ?p&:(>= (nivel-num ?p) (nivel-num alt))))
   ?d <- (diagnostico (sector ?s) (tipo-diagnostico oportunitat-energetica) (nivel ?n)
                      (evidencias $?ev&:(not (member$ (sym-cat preu-energia ":" ?p) ?ev))))
   =>
   (modify ?d (nivel (nivel-desplazado ?n 1)) (evidencias ?ev (sym-cat preu-energia ":" ?p))))

;; Estado mecánico distinto de operatiu: fallada-actuador alt (§5.3).
(defrule ELABORACIO::diagnosticar-fallada-actuador
   (estado-soar (id S0) (fase elaboracio))
   (ciclo-temporal (instante ?t))
   (observacion-panel (sector ?s) (estado-mecanico ?e&~operatiu) (instante ?t))
   (not (diagnostico (sector ?s) (tipo-diagnostico fallada-actuador)))
   =>
   (assert (diagnostico (id (sym-cat ?s "-fallada-actuador")) (sector ?s)
                        (tipo-diagnostico fallada-actuador) (nivel alt)
                        (evidencias (sym-cat estat-mecanic ":" ?e)))))

;; Si MONITORATGE ya creó fallada-actuador, el estado mecánico solo añade evidencia (§5.3).
(defrule ELABORACIO::anotar-estado-mecanico
   (estado-soar (id S0) (fase elaboracio))
   (ciclo-temporal (instante ?t))
   (observacion-panel (sector ?s) (estado-mecanico ?e&~operatiu) (instante ?t))
   ?d <- (diagnostico (sector ?s) (tipo-diagnostico fallada-actuador)
                      (evidencias $?ev&:(not (member$ (sym-cat estat-mecanic ":" ?e) ?ev))))
   =>
   (modify ?d (evidencias ?ev (sym-cat estat-mecanic ":" ?e))))
