;;; 01_percepcio.clp: PERCEPCIO. Marca los datos que faltan o están fallados.

(defmodule PERCEPCIO (import MAIN ?ALL))

;; SOAR: elaboración de la entrada. Dato requerido ausente o fallado: incertidumbre de su nivel.
(defrule PERCEPCIO::dato-ausente
   (estado-soar (id S0) (fase percepcio))
   (sector (id ?s))
   (dato-requerido (variable ?v) (nivel ?n))
   (not (observacion-sensor (sector ?s) (variable ?v) (calidad ok)))
   =>
   (assert (diagnostico (sector ?s) (tipo-diagnostico incertesa-dades) (nivel ?n)
                        (evidencias (sym-cat ?v :absent)))))

;; SOAR: elaboración de la entrada. Sin observación del panel no se sabe dónde está: critic.
(defrule PERCEPCIO::panel-ausente
   (estado-soar (id S0) (fase percepcio))
   (sector (id ?s))
   (not (observacion-panel (sector ?s)))
   =>
   (assert (diagnostico (sector ?s) (tipo-diagnostico incertesa-dades) (nivel critic)
                        (evidencias observacio-panel:absent))))
