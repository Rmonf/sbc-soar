;;; 10_aprenentatge.clp: APRENENTATGE. Chunking con refuerzo y olvido (activación base de Soar).
;;; Solo actúa con (parametros-aprendizaje (aprendizaje-activo TRUE)).

(defmodule APRENENTATGE (import MAIN ?ALL))

;; SOAR: chunking. Un tie de dos candidatos resuelto en el subestado se compila en un chunk:
;; "con esta pareja de acciones y estos beneficios, prefiere esta".
;; Corrección: la deliberación elige por el objetivo más prioritario al que sirve cada candidato.
;; Una acción que se mueve sirve siempre al objetivo de su criterio, y en un tie la acción sin
;; movimiento solo puede heredar el criterio de la otra acción que se mueve que no está en la pareja,
;; o ninguno (si heredara el mecánico, su better resolvería sin tie). Así, las dos acciones y sus
;; beneficios máximos fijan el resultado de la deliberación, y aplicar el chunk decide lo mismo.
(defrule APRENENTATGE::compilar
   (estado-soar (id S0) (fase aprenentatge))
   (parametros-aprendizaje (aprendizaje-activo TRUE))
   (ciclo-temporal (instante ?t))
   (impasse (tipo-impasse tie) (resuelto TRUE) (estrategia-resolucion ?e) (operadores-en-conflicto ?x ?y))
   (preferencia (tipo-preferencia better) (origen deliberacio) (operador-referencia ?p&?x|?y)
                (operador-comparado ?d&?x|?y) (criterio ?k))
   (operador-candidato (id ?p) (accion ?ap))
   (operador-candidato (id ?d) (accion ?ad))
   (not (chunk (accion-preferida ?ap) (beneficio-preferida =(beneficio-maximo ?p))
               (accion-descartada ?ad) (beneficio-descartada =(beneficio-maximo ?d))))
   =>
   (bind ?bp (beneficio-maximo ?p))
   (bind ?bd (beneficio-maximo ?d))
   (bind ?id (sym-cat chunk- ?ap - ?bp - ?ad - ?bd))
   (assert (chunk (id ?id) (accion-preferida ?ap) (beneficio-preferida ?bp) (accion-descartada ?ad)
                  (beneficio-descartada ?bd) (criterio ?k) (estrategia-resolucion ?e) (instante ?t)
                  (referencias ?t)))
   (printout traza "Aprenentatge (t=" ?t "): compilat " ?id ": " ?ap " (" ?bp ") sobre " ?ad
                   " (" ?bd "), criteri " ?k crlf))

;; SOAR: refuerzo (activación base). Un uso del chunk confirmado en el ciclo siguiente (episodio ok)
;; y posterior a su última referencia se añade; se guardan las max-referencias más recientes.
(defrule APRENENTATGE::reforzar
   (estado-soar (id S0) (fase aprenentatge))
   (parametros-aprendizaje (aprendizaje-activo TRUE) (max-referencias ?max))
   (ciclo-temporal (instante ?t))
   ?k <- (chunk (id ?c) (referencias $?refs))
   (episodio (chunk-aplicado ?c) (resultado ok) (instante ?i&:(> ?i (nth$ (length$ ?refs) ?refs))))
   =>
   (bind ?n (create$ ?refs ?i))
   (bind ?n (subseq$ ?n (max 1 (- (length$ ?n) (- ?max 1))) (length$ ?n)))
   (modify ?k (referencias ?n))
   (printout traza "Aprenentatge (t=" ?t "): reforcat " ?c " per l'us de t=" ?i crlf))

;; SOAR: olvido (activación base). Un chunk con activación bajo umbral-olvido y sin refuerzo
;; pendiente se borra.
(defrule APRENENTATGE::olvidar
   (estado-soar (id S0) (fase aprenentatge))
   (parametros-aprendizaje (aprendizaje-activo TRUE) (tasa-decaimiento ?d) (umbral-olvido ?u))
   (ciclo-temporal (instante ?t))
   ?k <- (chunk (id ?c) (referencias $?refs))
   (test (< (activacio ?refs ?t ?d) ?u))
   (not (episodio (chunk-aplicado ?c) (resultado ok) (instante ?i&:(> ?i (nth$ (length$ ?refs) ?refs)))))
   =>
   (printout traza "Aprenentatge (t=" ?t "): oblidat " ?c ", activacio="
                   (format nil "%.3f" (activacio ?refs ?t ?d)) " < " ?u crlf)
   (retract ?k))
