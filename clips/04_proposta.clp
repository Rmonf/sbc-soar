;;; 04_proposta.clp: módulo PROPOSTA, creación de operadores candidatos (roadmap §5.4).
;;; La condición "se propone si" de la tabla de §5.4 está en una sola función, motiva: la usan
;;; la regla que crea cada candidato (uno por acción y sector, con id derivado de ambos) y la
;;; que acumula sus motivos (tipo:nivel de cada diagnóstico que lo justifica).
;;; I2 P1: posicio-seguretat (riesgo mecánico), diagnosticar y mantenir-posicio; orientar-* y
;;; posicio-seguretat por incertidumbre llegan en P2 y P3.

(defmodule PROPOSTA (import MAIN ?ALL))

;; ¿Justifica un diagnóstico tipo/nivel proponer la acción? Columna "se propone si" de §5.4.
(deffunction PROPOSTA::motiva (?accion ?tipo ?nivel)
   (switch ?accion
      (case posicio-seguretat then
         (and (eq ?tipo risc-mecanic) (>= (nivel-num ?nivel) (nivel-num alt))))
      (case diagnosticar then
         (or (and (eq ?tipo incertesa-dades) (>= (nivel-num ?nivel) (nivel-num mitja)))
             (eq ?tipo fallada-actuador)))
      (default FALSE)))

;; Riesgo mecánico ≥ alt: se propone ir al ángulo de defensa del seguidor (§5.4).
(defrule PROPOSTA::proponer-posicio-seguretat
   (estado-soar (id S0) (fase proposta))
   (sector (id ?s) (tiene-seguidor ?sg))
   (exists (diagnostico (sector ?s) (tipo-diagnostico ?d)
                        (nivel ?n&:(motiva posicio-seguretat ?d ?n))))
   (seguidor-solar (id ?sg) (angulo-defensa-viento ?a))
   =>
   (assert (operador-candidato (id (sym-cat ?s "-posicio-seguretat")) (en-estado S0) (sector ?s)
                               (accion posicio-seguretat) (angulo-objetivo ?a)
                               (estado-candidato candidat))))

;; Incertidumbre ≥ mitja o fallada del actuador: se propone inspeccionar sin mover, en el
;; ángulo actual o nil si no se observa el panel (§5.4).
(defrule PROPOSTA::proponer-diagnosticar
   (estado-soar (id S0) (fase proposta))
   (sector (id ?s))
   (exists (diagnostico (sector ?s) (tipo-diagnostico ?d)
                        (nivel ?n&:(motiva diagnosticar ?d ?n))))
   =>
   (assert (operador-candidato (id (sym-cat ?s "-diagnosticar")) (en-estado S0) (sector ?s)
                               (accion diagnosticar) (angulo-objetivo (angulo-observado ?s))
                               (estado-candidato candidat))))

;; Sin incertidumbre ≥ mitja ni fallada del actuador: se propone mantener el ángulo actual (§5.4).
(defrule PROPOSTA::proponer-mantenir-posicio
   (estado-soar (id S0) (fase proposta))
   (observacion-panel (sector ?s) (angulo-actual ?a))
   (not (diagnostico (sector ?s) (tipo-diagnostico incertesa-dades)
                     (nivel ?n&:(>= (nivel-num ?n) (nivel-num mitja)))))
   (not (diagnostico (sector ?s) (tipo-diagnostico fallada-actuador)))
   =>
   (assert (operador-candidato (id (sym-cat ?s "-mantenir-posicio")) (en-estado S0) (sector ?s)
                               (accion mantenir-posicio) (angulo-objetivo ?a)
                               (estado-candidato candidat))))

;; Añade a los motivos de un candidato cada diagnóstico que lo justifica, como tipo:nivel (§5.4).
(defrule PROPOSTA::anotar-motivo
   (estado-soar (id S0) (fase proposta))
   ?c <- (operador-candidato (sector ?s) (accion ?a) (motivos $?m))
   (diagnostico (sector ?s) (tipo-diagnostico ?d) (nivel ?n&:(motiva ?a ?d ?n)))
   (test (not (member$ (sym-cat ?d ":" ?n) ?m)))
   =>
   (modify ?c (motivos ?m (sym-cat ?d ":" ?n))))
