;;; 04_proposta.clp: PROPOSTA. Un candidato por acción aplicable y sector (<sector>-<acción>).
;;; Una acción que se mueve no se propone si su ángulo objetivo está a menos del límite baix del
;;; umbral moviment (5°) del ángulo actual: ya está ahí, y la acción sin movimiento hereda su
;;; beneficio (AVALUACIO). Así no hay vaivén entre posiciones.

(defmodule PROPOSTA (import MAIN ?ALL))

;; SOAR: propuesta de operador. Viento alt o critic, o sin un dato crítico: ir a defensa.
(defrule PROPOSTA::proponer-seguretat
   (estado-soar (id S0) (fase proposta))
   (sector (id ?s) (tiene-seguidor ?g))
   (exists (or (diagnostico (sector ?s) (tipo-diagnostico risc-mecanic))
               (diagnostico (sector ?s) (tipo-diagnostico incertesa-dades) (nivel critic))))
   (seguidor-solar (id ?g) (angulo-defensa-viento ?d))
   (umbral (variable moviment) (nivel baix) (limite-superior ?cerca))
   (not (observacion-panel (sector ?s) (angulo-actual ?x&:(< (abs (- ?d ?x)) ?cerca))))
   =>
   (assert (operador-candidato (id (sym-cat ?s -posicio-seguretat)) (sector ?s) (accion posicio-seguretat)
                               (angulo-objetivo ?d) (estado-candidato candidat))))

;; SOAR: propuesta de operador. Estrés térmico o hídrico: dar sombra al cultivo.
(defrule PROPOSTA::proponer-ombra
   (estado-soar (id S0) (fase proposta))
   (sector (id ?s) (tiene-seguidor ?g))
   (exists (diagnostico (sector ?s) (tipo-diagnostico estres-termic|estres-hidric)))
   (prediccion (sector ?s) (variable angle-ombra) (valor ?o))
   (seguidor-solar (id ?g) (angulo-minimo ?min) (angulo-maximo ?max))
   (umbral (variable moviment) (nivel baix) (limite-superior ?cerca))
   (not (observacion-panel (sector ?s) (angulo-actual ?x&:(< (abs (- (max ?min (min ?max ?o)) ?x)) ?cerca))))
   =>
   (assert (operador-candidato (id (sym-cat ?s -orientar-ombra)) (sector ?s) (accion orientar-ombra)
                               (angulo-objetivo (max ?min (min ?max ?o))) (estado-candidato candidat))))

;; SOAR: propuesta de operador. Oportunidad energética: orientar a máxima captación.
(defrule PROPOSTA::proponer-produccio
   (estado-soar (id S0) (fase proposta))
   (sector (id ?s) (tiene-seguidor ?g))
   (diagnostico (sector ?s) (tipo-diagnostico oportunitat-energetica))
   (prediccion (sector ?s) (variable angle-captacio) (valor ?c))
   (seguidor-solar (id ?g) (angulo-minimo ?min) (angulo-maximo ?max))
   (umbral (variable moviment) (nivel baix) (limite-superior ?cerca))
   (not (observacion-panel (sector ?s) (angulo-actual ?x&:(< (abs (- (max ?min (min ?max ?c)) ?x)) ?cerca))))
   =>
   (assert (operador-candidato (id (sym-cat ?s -orientar-produccio)) (sector ?s) (accion orientar-produccio)
                               (angulo-objetivo (max ?min (min ?max ?c))) (estado-candidato candidat))))

;; SOAR: propuesta de operador. Datos dudosos o fallo del actuador: no mover y pedir diagnóstico.
;; Ángulo: el actual, o nil sin panel.
(defrule PROPOSTA::proponer-diagnosticar
   (estado-soar (id S0) (fase proposta))
   (sector (id ?s))
   (exists (or (diagnostico (sector ?s) (tipo-diagnostico incertesa-dades) (nivel mitja|alt|critic))
               (diagnostico (sector ?s) (tipo-diagnostico fallada-actuador))))
   =>
   (bind ?x nil)
   (do-for-fact ((?p observacion-panel)) (eq ?p:sector ?s) (bind ?x ?p:angulo-actual))
   (assert (operador-candidato (id (sym-cat ?s -diagnosticar)) (sector ?s) (accion diagnosticar)
                               (angulo-objetivo ?x) (estado-candidato candidat))))

;; SOAR: propuesta de operador. Si no se propone diagnosticar: quedarse en el ángulo actual.
(defrule PROPOSTA::proponer-mantenir
   (estado-soar (id S0) (fase proposta))
   (observacion-panel (sector ?s) (angulo-actual ?x))
   (not (diagnostico (sector ?s) (tipo-diagnostico incertesa-dades) (nivel mitja|alt|critic)))
   (not (diagnostico (sector ?s) (tipo-diagnostico fallada-actuador)))
   =>
   (assert (operador-candidato (id (sym-cat ?s -mantenir-posicio)) (sector ?s) (accion mantenir-posicio)
                               (angulo-objetivo ?x) (estado-candidato candidat))))
