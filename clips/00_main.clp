;;; 00_main.clp: módulo MAIN con las plantillas, las deffunction y las reglas de control (roadmap §4.3, §8).
;;; I0: solo están las plantillas del conocimiento estático (§3.1) y la de estado-soar (S0);
;;; las demás se añaden en I1. Convenciones de §2.3.

(defmodule MAIN (export ?ALL))

;;; ---------------------------------------------------------------------------
;;; Conocimiento estático (§3.1). Los hechos los genera python/ontologia.py
;;; en config/base_coneixement.clp.
;;; ---------------------------------------------------------------------------

;; Sector de la instalación, con su cultivo y su seguidor (§3.1).
(deftemplate MAIN::sector
   (slot id (type SYMBOL))
   (slot tiene-cultivo (type SYMBOL))
   (slot tiene-seguidor (type SYMBOL)))

;; Parámetros agronómicos del cultivo de un sector (§3.1).
(deftemplate MAIN::cultivo
   (slot id (type SYMBOL))
   (slot nombre-cultivo (type SYMBOL))
   (slot fase-fenologica (type SYMBOL))
   (slot sensibilidad (type SYMBOL) (allowed-symbols baix mitja alt critic))
   (slot umbral-temp-estres (type NUMBER))
   (slot umbral-humedad-critica (type NUMBER)))

;; Límites mecánicos y de desgaste del seguidor de un sector (§3.1).
(deftemplate MAIN::seguidor-solar
   (slot id (type SYMBOL))
   (slot angulo-minimo (type NUMBER))
   (slot angulo-maximo (type NUMBER))
   (slot angulo-defensa-viento (type NUMBER))
   (slot umbral-viento-critico (type NUMBER))
   (slot max-movimientos-hora (type INTEGER))
   (slot tolerancia-angulo (type NUMBER)))

;; Objetivo de la política de prioridades: 1 es el más prioritario (§3.1).
(deftemplate MAIN::objetivo-activo
   (slot nombre-objetivo (type SYMBOL)
      (allowed-symbols seguretat-persones integritat-mecanica proteccio-cultiu
                       produccio-energia estabilitat))
   (slot prioridad (type INTEGER))
   (slot tipo-restriccion (type SYMBOL) (allowed-symbols dura tova)))

;; Variable que se debe observar y nivel de incertidumbre si falta (§3.1, §5.1).
(deftemplate MAIN::dato-requerido
   (slot variable (type SYMBOL)
      (allowed-symbols radiacio temp-cultiu temp-ambient humitat-sol vent vent-previst
                       pluja pluja-prevista preu-energia produccio moviment
                       angle-captacio angle-ombra))
   (slot nivel (type SYMBOL) (allowed-symbols baix mitja alt critic)))

;; Fila de la tabla de fases: módulo que la ejecuta y fase siguiente (§4.1).
(deftemplate MAIN::definicion-fase
   (slot fase (type SYMBOL)
      (allowed-symbols espera percepcio monitoratge elaboracio proposta avaluacio
                       seleccio deliberacio aplicacio explicacio aprenentatge neteja))
   (slot modulo (type SYMBOL)
      (allowed-symbols PERCEPCIO MONITORATGE ELABORACIO PROPOSTA AVALUACIO SELECCIO
                       DELIBERACIO APLICACIO EXPLICACIO APRENENTATGE NETEJA))
   (slot siguiente (type SYMBOL)
      (allowed-symbols espera percepcio monitoratge elaboracio proposta avaluacio
                       seleccio deliberacio aplicacio explicacio aprenentatge neteja)))

;; Intervalo [limite-inferior, limite-superior) que da un nivel a una variable;
;; un límite nil es infinito (§3.1, §5.3).
(deftemplate MAIN::umbral
   (slot variable (type SYMBOL)
      (allowed-symbols radiacio temp-cultiu temp-ambient humitat-sol vent vent-previst
                       pluja pluja-prevista preu-energia produccio moviment
                       angle-captacio angle-ombra))
   (slot nivel (type SYMBOL) (allowed-symbols baix mitja alt critic))
   (slot limite-inferior (type NUMBER SYMBOL) (allowed-symbols nil) (default nil))
   (slot limite-superior (type NUMBER SYMBOL) (allowed-symbols nil) (default nil))
   (slot referencia (type SYMBOL) (allowed-symbols absoluta cultiu seguidor)))

;; Parámetros de la memoria de chunks (§5.10, §6.2).
(deftemplate MAIN::parametros-aprendizaje
   (slot aprendizaje-activo (type SYMBOL) (allowed-symbols TRUE FALSE))
   (slot tasa-decaimiento (type NUMBER))
   (slot umbral-olvido (type NUMBER))
   (slot max-referencias (type INTEGER)))

;;; ---------------------------------------------------------------------------
;;; Familia 3: control (§3.2). S0 viene de la configuración generada.
;;; ---------------------------------------------------------------------------

;; Estado raíz S0 o subestado de deliberación (§3.2, §4.2, §5.7).
(deftemplate MAIN::estado-soar
   (slot id (type SYMBOL))
   (slot estado-padre (type SYMBOL) (default nil))
   (slot fase (type SYMBOL)
      (allowed-symbols espera percepcio monitoratge elaboracio proposta avaluacio
                       seleccio deliberacio aplicacio explicacio aprenentatge neteja))
   (slot subfase (type SYMBOL) (allowed-symbols pendent feta))
   (slot impasse-asociado (type SYMBOL) (default nil)))
