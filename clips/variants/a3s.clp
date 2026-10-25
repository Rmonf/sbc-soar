;;; a3s.clp: variante A3s del experimento de agenda (roadmap §11.3). NO es código de producción.
;;; Se carga después de los módulos (pont_clips.VARIANTES) y redefine, con el mismo nombre y
;;; módulo, los refinamientos que son reglas propias (salience -10) y las restricciones R1–R5
;;; (salience -20). Cada regla es una copia textual de la de producción con una línea declare
;;; añadida (tests/test_variantes.py lo comprueba). Con salience negativa disparan las últimas de
;;; su fase, al revés de lo que suele hacer depth (con valores positivos, la secuencia solo cambiaba
;;; en 3 de los 115 ciclos de la batería). La hipótesis es que la salience cambia el orden de
;;; disparo, pero no las órdenes, los episodios ni la traza.

;;; --- Copias de 03_elaboracio.clp con salience -10 ---

;; Copia de ELABORACIO::reforzar-risc-mecanic (03_elaboracio.clp) con salience -10 (§11.3, A3s).
(defrule ELABORACIO::reforzar-risc-mecanic
   (declare (salience -10))
   (estado-soar (id S0) (fase elaboracio))
   (abstraccion (sector ?s) (variable ?v&vent|vent-previst)
                (nivel ?n&:(>= (nivel-num ?n) (nivel-num alt))))
   ?d <- (diagnostico (sector ?s) (tipo-diagnostico risc-mecanic) (nivel ?actual)
                      (evidencias $?ev&:(not (member$ (sym-cat ?v ":" ?n) ?ev))))
   =>
   (modify ?d (nivel (nivel-max ?actual ?n)) (evidencias ?ev (sym-cat ?v ":" ?n))))

;; Copia de ELABORACIO::refinar-oportunitat-preu (03_elaboracio.clp) con salience -10 (§11.3, A3s).
(defrule ELABORACIO::refinar-oportunitat-preu
   (declare (salience -10))
   (estado-soar (id S0) (fase elaboracio))
   (abstraccion (sector ?s) (variable preu-energia) (nivel ?p&:(>= (nivel-num ?p) (nivel-num alt))))
   ?d <- (diagnostico (sector ?s) (tipo-diagnostico oportunitat-energetica) (nivel ?n)
                      (evidencias $?ev&:(not (member$ (sym-cat preu-energia ":" ?p) ?ev))))
   =>
   (modify ?d (nivel (nivel-desplazado ?n 1)) (evidencias ?ev (sym-cat preu-energia ":" ?p))))

;; Copia de ELABORACIO::anotar-estado-mecanico (03_elaboracio.clp) con salience -10 (§11.3, A3s).
(defrule ELABORACIO::anotar-estado-mecanico
   (declare (salience -10))
   (estado-soar (id S0) (fase elaboracio))
   (ciclo-temporal (instante ?t))
   (observacion-panel (sector ?s) (estado-mecanico ?e&~operatiu) (instante ?t))
   ?d <- (diagnostico (sector ?s) (tipo-diagnostico fallada-actuador)
                      (evidencias $?ev&:(not (member$ (sym-cat estat-mecanic ":" ?e) ?ev))))
   =>
   (modify ?d (evidencias ?ev (sym-cat estat-mecanic ":" ?e))))

;;; --- Copias de 05_avaluacio.clp con salience -20 ---

;; Copia de AVALUACIO::r1-rechazar-con-personas (05_avaluacio.clp) con salience -20 (§11.3, A3s).
(defrule AVALUACIO::r1-rechazar-con-personas
   (declare (salience -20))
   (estado-soar (id S0) (fase avaluacio))
   (diagnostico (sector ?s) (tipo-diagnostico risc-persones))
   (operador-candidato (id ?c) (sector ?s) (accion ?a) (angulo-objetivo ?o))
   (test (candidato-mueve ?a ?o ?s))
   =>
   (assert (preferencia (en-estado S0) (sector ?s) (tipo-preferencia reject)
                        (operador-referencia ?c) (criterio seguretat-persones)
                        (origen regla) (restriccion R1))))

;; Copia de AVALUACIO::r2-rechazar-orientar (05_avaluacio.clp) con salience -20 (§11.3, A3s).
(defrule AVALUACIO::r2-rechazar-orientar
   (declare (salience -20))
   (estado-soar (id S0) (fase avaluacio))
   (diagnostico (sector ?s) (tipo-diagnostico risc-mecanic) (nivel critic))
   (operador-candidato (id ?c) (sector ?s) (accion orientar-produccio|orientar-ombra))
   =>
   (assert (preferencia (en-estado S0) (sector ?s) (tipo-preferencia reject)
                        (operador-referencia ?c) (criterio integritat-mecanica)
                        (origen regla) (restriccion R2))))

;; Copia de AVALUACIO::r3-rechazar-con-fallada (05_avaluacio.clp) con salience -20 (§11.3, A3s).
(defrule AVALUACIO::r3-rechazar-con-fallada
   (declare (salience -20))
   (estado-soar (id S0) (fase avaluacio))
   (ciclo-temporal (instante ?t))
   (operador-candidato (id ?c) (sector ?s) (accion ?a) (angulo-objetivo ?o))
   (test (fallada-actuador-reciente ?s ?t))
   (test (candidato-mueve ?a ?o ?s))
   =>
   (assert (preferencia (en-estado S0) (sector ?s) (tipo-preferencia reject)
                        (operador-referencia ?c) (criterio integritat-mecanica)
                        (origen regla) (restriccion R3))))

;; Copia de AVALUACIO::r4-rechazar-por-desgaste (05_avaluacio.clp) con salience -20 (§11.3, A3s).
(defrule AVALUACIO::r4-rechazar-por-desgaste
   (declare (salience -20))
   (estado-soar (id S0) (fase avaluacio))
   (ciclo-temporal (instante ?t))
   (sector (id ?s) (tiene-seguidor ?sg))
   (seguidor-solar (id ?sg) (max-movimientos-hora ?max))
   (test (>= (movimientos-recientes ?s ?t) ?max))
   (operador-candidato (id ?c) (sector ?s) (accion ?a&~posicio-seguretat) (angulo-objetivo ?o))
   (test (candidato-mueve ?a ?o ?s))
   =>
   (assert (preferencia (en-estado S0) (sector ?s) (tipo-preferencia reject)
                        (operador-referencia ?c) (criterio integritat-mecanica)
                        (origen regla) (restriccion R4))))

;; Copia de AVALUACIO::r5-rechazar-sin-panel (05_avaluacio.clp) con salience -20 (§11.3, A3s).
(defrule AVALUACIO::r5-rechazar-sin-panel
   (declare (salience -20))
   (estado-soar (id S0) (fase avaluacio))
   (ciclo-temporal (instante ?t))
   (sector (id ?s))
   (not (observacion-panel (sector ?s) (instante ?t)))
   (operador-candidato (id ?c) (sector ?s) (accion ?a) (angulo-objetivo ?o))
   (test (candidato-mueve ?a ?o ?s))
   =>
   (assert (preferencia (en-estado S0) (sector ?s) (tipo-preferencia reject)
                        (operador-referencia ?c) (criterio seguretat-persones)
                        (origen regla) (restriccion R5))))

;; Copia de AVALUACIO::r2-requerir-seguretat (05_avaluacio.clp) con salience -20 (§11.3, A3s).
(defrule AVALUACIO::r2-requerir-seguretat
   (declare (salience -20))
   (estado-soar (id S0) (fase avaluacio))
   (diagnostico (sector ?s) (tipo-diagnostico risc-mecanic) (nivel critic))
   (operador-candidato (id ?c) (sector ?s) (accion posicio-seguretat))
   =>
   (assert (preferencia (en-estado S0) (sector ?s) (tipo-preferencia require)
                        (operador-referencia ?c) (criterio integritat-mecanica)
                        (origen regla) (restriccion R2))))
