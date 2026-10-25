;;; 10_aprenentatge.clp: módulo APRENENTATGE, chunking con refuerzo y olvido (roadmap §5.10, §6).
;;; Solo actúa con (parametros-aprendizaje (aprendizaje-activo TRUE)); con FALSE es la línea base
;;; C0 (§6.2). Tres grupos de reglas que no dependen del orden de disparo: compilar, reforzar y
;;; olvidar. El id del chunk se deriva de sus cinco condiciones y la traza no nombra el sector:
;;; si dos sectores empatan igual en el mismo ciclo, el chunk no depende de cuál compila (§5.10).

(defmodule APRENENTATGE (import MAIN ?ALL))

;; Compilar: un tie de dos candidatos resuelto por minima-intervencio o prioritat-objectius da un
;; chunk con el par, el beneficio máximo de cada uno y la relación de Δ, salvo que ya exista uno
;; con las mismas cinco condiciones (§5.10.1, §6.2).
(defrule APRENENTATGE::compilar-chunk
   (estado-soar (id S0) (fase aprenentatge))
   (parametros-aprendizaje (aprendizaje-activo TRUE))
   (ciclo-temporal (instante ?t))
   (impasse (sector ?s) (tipo-impasse tie) (resuelto TRUE)
            (estrategia-resolucion ?e&minima-intervencio|prioritat-objectius)
            (operadores-en-conflicto ?x ?y))
   (preferencia (sector ?s) (tipo-preferencia better) (origen deliberacio)
                (operador-referencia ?p&?x|?y) (operador-comparado ?d&?x|?y) (criterio ?k))
   (operador-candidato (id ?p) (accion ?ap))
   (operador-candidato (id ?d) (accion ?ad))
   (valoracion (evalua-operador ?p) (beneficio-mecanico ?pm) (beneficio-cultivo ?pc)
               (beneficio-energia ?pe) (desplazamiento ?dp))
   (valoracion (evalua-operador ?d) (beneficio-mecanico ?dm) (beneficio-cultivo ?dc)
               (beneficio-energia ?de) (desplazamiento ?dd))
   (not (chunk (accion-preferida ?ap) (beneficio-preferida =(nivel-max ?pm (nivel-max ?pc ?pe)))
               (accion-descartada ?ad) (beneficio-descartada =(nivel-max ?dm (nivel-max ?dc ?de)))
               (relacion-delta =(relacio-delta ?dp ?dd (tolerancia-sector ?s)))))
   =>
   (bind ?bp (nivel-max ?pm (nivel-max ?pc ?pe)))
   (bind ?bd (nivel-max ?dm (nivel-max ?dc ?de)))
   (bind ?rel (relacio-delta ?dp ?dd (tolerancia-sector ?s)))
   (bind ?id (sym-cat chunk- ?ap - ?bp - ?ad - ?bd - ?rel))
   (assert (chunk (id ?id) (accion-preferida ?ap) (beneficio-preferida ?bp)
                  (accion-descartada ?ad) (beneficio-descartada ?bd) (relacion-delta ?rel)
                  (criterio ?k) (estrategia-resolucion ?e) (instante ?t) (referencias ?t)))
   (printout traza "Aprenentatge (t=" ?t "): compilat " ?id ": " ?ap " (benefici " ?bp ") sobre "
                   ?ad " (benefici " ?bd "), delta " ?rel ", criteri " ?k ", apres de " ?e crlf))
