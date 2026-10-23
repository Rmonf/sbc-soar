# Pràctica de Sistemes Basats en Regles

**Arquitectura inspirada en SOAR implementada en CLIPS per a una instal·lació agrovoltaica**

Sistemes Basats en Coneixement · Departament de Ciències de la Computació · Grau en Intel·ligència Artificial – UPC

> Transcripció a markdown de `Enunciado.pdf`, sense canvis de contingut. Els números de capítol i secció són els de l'original; el roadmap hi fa referència com a "enunciat 3.x".

---

## 1. Organització, avaluació i lliurament

Aquest document conté els objectius d'aprenentatge, la descripció del problema, el guió de desenvolupament, una planificació orientativa i la rúbrica d'avaluació de la pràctica.

La pràctica s'ha de fer preferentment en grups de quatre. El nucli de decisió s'ha de desenvolupar en CLIPS, però la seva organització ha d'estar explícitament inspirada en SOAR. Això significa reconstruir amb els mecanismes de CLIPS un cicle deliberatiu basat en estat, elaboracions, operadors candidats, preferències, selecció i aplicació d'operadors, detecció d'impasses i deliberació addicional per resoldre'ls. No es demana programar en SOAR ni reproduir-ne internament tota l'arquitectura, sinó demostrar que els seus principis poden guiar el disseny d'un sistema de producció implementat en CLIPS.

Es permet emprar Python i clipspy per construir l'entorn simulat, calcular prediccions i connectar components, però la interpretació simbòlica, la generació d'alternatives, les preferències, la resolució dels conflictes i la decisió final han de quedar implementades mitjançant fets, regles, mòduls i agenda de CLIPS.

L'activitat està dimensionada per a set setmanes, amb 10 hores de laboratori i aproximadament 20,7 hores de treball personal per estudiant. En un grup de quatre, això correspon aproximadament a 92,8 hores de treball agregat.

> **Lliurament.** La data exacta, el mecanisme de lliurament electrònic i les franges de demostració presencial es publicaran al Racó. Cal lliurar l'informe en PDF, el codi font complet, instruccions reproduïbles d'execució i els fitxers dels casos de prova.

La qualificació valorarà especialment: l'anàlisi del domini; la qualitat dels `deftemplate`; la correspondència explícita entre SOAR i CLIPS; la generalitat i organització de les regles; el control del cicle deliberatiu; l'ús conscient de l'agenda; la resolució dels conflictes del domini; la traçabilitat de les decisions; i la qualitat dels experiments.

No es demana construir una instal·lació física ni entrenar models predictius sofisticats. Es demana **un prototip simulat, reproduïble i explicable** que integri informació ambiental i decideixi accions sobre els panells. Els models de predicció i optimització poden ser heurístics o proporcionats com a serveis; no poden substituir el raonament simbòlic que s'avalua.

---

## 2. Objectius d'aprenentatge

L'objectiu general és afrontar un problema dinàmic que requereix coneixement expert, objectius potencialment incompatibles i decisions justificables. En acabar la pràctica, l'estudiant hauria de ser capaç de:

- Analitzar un domini realista i identificar fonts de coneixement agronòmic, energètic, meteorològic i operatiu.
- Conceptualitzar l'estat d'una instal·lació agrovoltaica i representar-lo mitjançant objectes, atributs, relacions i valors simbòlics.
- Distingir coneixement declaratiu, procedural i de control.
- Comprendre els elements bàsics de l'arquitectura SOAR i traslladar-los de manera raonada a CLIPS.
- Representar l'estat corrent mitjançant fets estructurats, `deftemplate`, relacions i objectes quan sigui convenient.
- Implementar coneixement procedural mitjançant produccions i separar regles d'interpretació, proposta, avaluació, selecció, aplicació i explicació.
- Organitzar el raonament amb mòduls, focus i fets de control que representin les fases del cicle de decisió.
- Distingir la resolució de conflictes de l'agenda de CLIPS dels conflictes semàntics entre objectius del domini.
- Generar, comparar i seleccionar operadors candidats mitjançant restriccions dures, preferències i valoracions explícites.
- Detectar i tractar situacions sense solució immediata: empats, absència de candidats, dades insuficients o restriccions incompatibles.
- Representar els impasses com a fets explícits i activar una fase de deliberació anàloga al paper dels subestats en SOAR.
- Integrar el nucli CLIPS amb una simulació de sensors, actuadors i serveis externs, sense delegar-hi la decisió.
- Desenvolupar incrementalment prototips verificables i depurar-los amb `watch rules`, `watch facts`, l'agenda i les traces del sistema.
- Dissenyar casos de prova que mostrin comportament normal, conflictes, excepcions, dades incompletes i situacions de seguretat.
- Explicar una decisió a partir de l'estat percebut, les regles activades, els operadors candidats i les preferències aplicades.
- Treballar en equip i fer un ús crític, legal i ètic de les fonts d'informació i de les dades.

---

## 3. El problema

### 3.1 Context

Una explotació agrovoltaica combina cultius i producció d'energia solar sobre una mateixa superfície. Els panells poden canviar d'orientació i, segons la geometria de la instal·lació, modificar tant la captació solar com l'ombra, la temperatura i l'estrès hídric del cultiu. Una decisió beneficiosa per a la producció energètica pot perjudicar el cultiu, i una acció protectora pot reduir els ingressos elèctrics.

El sistema ha de percebre l'estat de la instal·lació, anticipar-ne l'evolució a curt termini i recomanar o executar una acció segura. Les decisions s'han de poder entendre des de dos punts de vista: l'enginyer energètic i l'agrònom.

### 3.2 Objectiu funcional

Cal construir un sistema basat en regles en CLIPS que, a cada interval de decisió, seleccioni una acció per a cada sector de la plantació o per al conjunt de la instal·lació. Com a mínim, ha de considerar els objectius següents:

- protegir el cultiu davant calor, radiació excessiva, dèficit hídric o episodis meteorològics adversos;
- mantenir una producció energètica raonable quan no hi hagi restriccions prioritàries;
- respectar límits mecànics, costos de moviment, manteniment i seguretat;
- evitar oscil·lacions innecessàries entre posicions consecutives;
- oferir una justificació simbòlica de l'acció escollida.

### 3.3 Escenari mínim

La instal·lació s'ha de dividir, com a mínim, en **tres sectors**. Cada sector conté un tipus de cultiu, un conjunt de panells orientables i sensors. El simulador proporcionarà lectures temporals o dades sintètiques amb, almenys:

- radiació solar, temperatura ambiental i temperatura del cultiu;
- humitat del sòl o un indicador d'estrès hídric;
- vent, pluja i previsió meteorològica a curt termini;
- angle actual, estat mecànic i disponibilitat dels panells;
- producció instantània o estimada i demanda/preu energètic opcional;
- fase fenològica o nivell de sensibilitat del cultiu.

Els valors numèrics es poden discretitzar en categories justificades (per exemple, `baix`, `mitja`, `alt`, `critic`). Cal documentar els llindars, la font o el criteri que els sustenta i les conseqüències de simplificar-los.

### 3.4 Accions i restriccions

El repertori mínim d'operadors ha d'incloure:

- `orientar-produccio`: aproximar el panell a l'angle de màxima captació;
- `orientar-ombra`: augmentar la protecció del cultiu;
- `posicio-seguretat`: reduir el risc mecànic davant vent o incidències;
- `mantenir-posicio`: evitar moviments de benefici marginal;
- `sollicitar-dades` o `diagnosticar`: reaccionar davant dades insuficients o incoherents.

Les restriccions de seguretat són dures: cap objectiu productiu pot prevaldre sobre un límit mecànic o una alarma crítica. La resta són preferències graduades que poden entrar en conflicte. El grup ha de definir i justificar una política de prioritats.

### 3.5 Arquitectura de referència

```text
  Simulador d'entorn          Predicció a curt termini
          │  fets d'entrada            │  fets derivats
          ▼                            ▼
   ┌──────────────────────────────────────────────┐
   │         Nucli CLIPS inspirat en SOAR         │
   │ estat + operadors + preferències + impasses  │
   └──────────────────────────────────────────────┘
          │  ordres                    │
          ▼                            ▼
  Controlador de panells        Traça i explicació
          ┊
          └┄┄┄┄ (efecte de l'ordre, de tornada al simulador)
```

*Figura 3.1: Arquitectura mínima recomanada. Els components externs simulen, calculen o executen; CLIPS interpreta, decideix i justifica.*

No es requereix un sistema multiagent distribuït. Si el grup decideix implementar diversos motors o agents (per exemple, un per sector i un coordinador), haurà de justificar què s'obté amb aquesta complexitat i comparar-la amb l'alternativa d'un únic entorn CLIPS modular. L'extensió multiagent no compensa mancances en els requisits nuclears.

### 3.6 Inspiració obligatòria en SOAR

SOAR s'utilitzarà com a **model conceptual de l'arquitectura de decisió**; CLIPS serà el **llenguatge i motor d'execució**. No és suficient construir una base de regles convencional que produeixi directament una acció. El sistema ha de fer visible el procés deliberatiu inspirat en SOAR i implementar la correspondència següent:

| Concepte de SOAR | Implementació en CLIPS | Evidència exigida |
|---|---|---|
| Estat i memòria de treball | Fets estructurats amb `deftemplate` | Esquema de fets observats, derivats, de control, candidats i resultats. |
| Elaboracions | Regles que deriven atributs simbòlics sense decidir encara l'acció | Traça que mostri com les lectures es converteixen en riscos, necessitats i oportunitats. |
| Operador | Fet `operador-candidat` creat per regles de proposta | En cada decisió no trivial s'han de considerar explícitament diverses alternatives aplicables. |
| Preferències | Fets de valoració, prioritat o dominància entre candidats | Justificació de restriccions dures, objectius tous i criteris de comparació. |
| Selecció d'operador | Regles del mòdul de resolució | Identificació de candidats descartats, criteri determinant i operador seleccionat. |
| Aplicació d'operador | Regles que creen una ordre d'actuació i actualitzen l'estat | Separació estricta entre proposar, seleccionar i aplicar. |
| Impasse | Fet explícit `conflicte` o `impasse` | Detecció reproduïble d'almenys dos tipus: empat, falta de candidat, dades insuficients, contradicció o restriccions incompatibles. |
| Subestat o deliberació | Mòdul o fase específica activada per l'impasse | Regles addicionals que consulten historial, demanen dades o apliquen un criteri secundari i retornen un resultat al cicle principal. |
| Entrada i sortida | Inserció de fets i generació de fets `ordre-actuador` | Contracte explícit entre simulador i CLIPS; els components externs no poden decidir. |
| Memòria episòdica | Historial de situacions, decisions i resultats | Ús de l'historial en almenys una decisió o impasse. |

La inspiració en SOAR comporta quatre principis obligatoris:

1. **separació entre elaboració i decisió**: les regles primer interpreten l'estat i després proposen operadors;
2. **decisió mediada per operadors**: una acció no pot executar-se si abans no ha estat proposada i seleccionada;
3. **preferències explícites**: els conflictes entre objectius s'han de representar i raonar, no ocultar en l'ordre de les regles;
4. **deliberació davant impasses**: quan el coneixement immediat no permet decidir, el sistema activa un procés addicional i retorna el resultat al nivell principal.

El grup haurà d'incloure en l'informe una taula de correspondència SOAR–CLIPS adaptada a la seva implementació i explicar quines propietats de SOAR s'han preservat, quines s'han aproximat i quines han quedat fora de l'abast.

### 3.7 Representació del coneixement en CLIPS

La memòria de treball ha de tenir una estructura coherent i documentada mitjançant `deftemplate`. Com a mínim, ha d'incloure el cicle temporal, els sectors, el cultiu, l'estat dels panells, les observacions, les prediccions, els riscos, els objectius actius, els operadors candidats, les valoracions i l'historial recent necessari per evitar oscil·lacions.

Cal distingir explícitament cinc famílies de fets: **observats, derivats, de control, candidats d'acció i resultats**. Cada plantilla ha d'indicar el significat dels slots, el domini de valors, l'origen de la informació, la persistència i qui la pot modificar.

El coneixement s'ha de separar funcionalment en produccions de:

1. **elaboració**: deriven símbols d'alt nivell a partir de lectures i prediccions;
2. **proposta**: generen operadors aplicables;
3. **avaluació**: creen valoracions o preferències explícites entre candidats;
4. **aplicació**: materialitzen l'operador seleccionat i generen una ordre;
5. **monitoratge**: detecten efectes, errors, canvis inesperats o dades insuficients;
6. **explicació**: registren evidències i motius de la decisió.

#### 3.7.1 Cicle de control i mòduls

CLIPS no imposa el cicle de decisió de SOAR. El grup l'ha de reconstruir mitjançant un fet com `(control (fase percepcio))` i una seqüència justificada de fases: `percepcio`, `elaboracio`, `proposta`, `avaluacio`, `seleccio`, `aplicacio`, `explicacio` i `monitoratge`. Davant un impasse, el flux ha de passar temporalment a `deliberacio` i retornar després un resultat a la fase de selecció. Es recomana distribuir les fases en mòduls CLIPS i governar-ne l'execució amb `focus` o amb regles de transició.

#### 3.7.2 Dos nivells de resolució de conflictes

La pràctica ha de diferenciar:

- **conflicte de l'agenda**: diverses activacions poden disparar. Cal experimentar amb salience, especificitat i almenys dues estratègies de l'agenda (per exemple, depth, breadth, LEX o MEA);
- **conflicte del domini**: diverses accions aplicables afavoreixen objectius incompatibles. Aquest conflicte s'ha de representar amb fets i resoldre mitjançant restriccions, prioritats o puntuacions, no com un efecte accidental de la salience.

La solució recomanada és híbrida: primer s'eliminen els operadors que violen restriccions dures; després es comparen els candidats restants segons protecció del cultiu, energia, estabilitat i cost de moviment.

#### 3.7.3 Impasses explícits

CLIPS no genera subestats automàticament. El sistema ha de detectar almenys dos tipus de situació sense decisió immediata: empat entre candidats, absència d'operadors, dades insuficients, informació contradictòria o restriccions incompatibles. La detecció ha de crear un fet conflicte i activar una fase de deliberació que consulti l'historial, demani dades, apliqui un criteri secundari, triï l'acció més reversible o derivi el cas a una persona.

### 3.8 Cicle de funcionament

Per cada pas simulat, el sistema ha de:

1. rebre i validar observacions;
2. construir o actualitzar la representació simbòlica;
3. derivar riscos, necessitats i oportunitats;
4. proposar tots els operadors aplicables com a fets, sense seleccionar-los prematurament;
5. avaluar-los segons seguretat, protecció del cultiu, energia i cost de moviment;
6. resoldre els conflictes del domini i seleccionar una acció;
7. enviar l'ordre al simulador i registrar-ne la justificació;
8. observar el resultat al pas següent i, si escau, revisar la decisió.

### 3.9 Abast i extensions

Són obligatoris: taula de correspondència SOAR–CLIPS; `deftemplate`; regles d'elaboració; mòduls o fases explícites; proposta, selecció i aplicació separades; generació de múltiples operadors; preferències o valoracions; ús justificat de l'agenda; detecció i deliberació sobre dos tipus d'impasse; explicació; historial; i integració simulada. **No és acceptable que Python prengui la decisió final ni usar salience com a única política de raonament.**

Són extensions opcionals: ontologia inicial en Protégé; COOL i objectes; dades meteorològiques reals; aprenentatge de pesos; planificació multipas; visualització avançada; robot mòbil d'inspecció o coordinació multiagent. Qualsevol extensió s'ha d'avaluar amb una hipòtesi concreta i una línia base.

### 3.10 Lliurables

La tramesa ha d'incloure:

- informe que segueixi identificació, conceptualització, formalització, implementació i prova;
- diagrama de l'arquitectura i esquema complet de la memòria de treball;
- taula de correspondència entre els conceptes de SOAR i la implementació concreta en CLIPS;
- catàleg d'operadors, regles de proposta, aplicació i preferència;
- codi CLIPS comentat i codi del simulador/integració;
- esquema dels mòduls, fases i transicions de control;
- experiment documentat sobre les estratègies de resolució de conflictes de l'agenda;
- fitxer de configuració o dades per reproduir els experiments;
- un mínim de vuit casos de prova, amb entrades, traça rellevant, sortida i explicació;
- instruccions d'instal·lació i execució des d'un entorn net;
- breu registre de contribucions i decisions del grup.

---

## 4. Guió de la pràctica

**Primera setmana: enunciat, domini i fonts.** Llegiu l'enunciat, delimiteu l'escenari i identifiqueu el coneixement necessari. Estudieu la descripció bàsica de l'arquitectura SOAR i identifiqueu estat, elaboracions, operadors, preferències, cicle de decisió, impasses i subestats. Cerqueu també fonts autoritzades sobre agrivoltaica, cultius i CLIPS. Definiu tres casos narratius: operació normal, protecció del cultiu i emergència.

**Segona setmana: CLIPS i especificació inicial.** Instal·leu CLIPS a partir dels recursos oficials i executeu exemples bàsics. Practiqueu `deftemplate`, fets, regles, agenda i traces. Elaboreu una primera taula SOAR–CLIPS i implementeu un cicle mínim amb elaboració, proposta, selecció i aplicació separades. El sistema ha de rebre un únic sector i seleccionar entre mantenir posició i posició de seguretat.

**Tercera setmana: conceptualització i memòria de treball.** Descriviu conceptes, atributs i relacions. Dissenyeu els `deftemplate` i una taula que indiqui origen, domini i persistència de cada slot. Definiu la discretització de les variables i separeu observacions, inferències, control, candidats i resultats. Implementeu elaboracions simbòliques i verifiqueu-les amb traces.

**Quarta setmana: descomposició i prototip vertical.** Descomponeu el cicle en percepció, interpretació, proposta, avaluació, selecció, aplicació i explicació. Definiu mòduls, fases, transicions i operadors. Completeu un prototip vertical que produeixi una ordre i una explicació. Compareu dues estratègies de l'agenda sobre un mateix conjunt d'activacions.

**Cinquena setmana: valoracions, conflictes i integració.** Implementeu restriccions i valoracions de seguretat, cultiu, energia i estabilitat. Provoqueu conflictes del domini i distingiu-los dels de l'agenda. Detecteu almenys dos impasses explícits i documenteu-ne les regles de deliberació. Connecteu CLIPS al simulador, preferentment mitjançant clipspy, i amplieu el sistema a tres sectors.

**Sisena setmana: prototip definitiu.** Completeu la cobertura de casos, tracteu dades absents i fallades d'actuació, i estabilitzeu les regles. Afegiu la traça d'explicació. Si implementeu una extensió, compareu-la amb una línia base. Congelareu una versió candidata i començareu a recopilar resultats reproduïbles.

**Setena setmana: proves, informe i demostració.** Executeu els vuit casos mínims, incloent casos no utilitzats durant el desenvolupament. Analitzeu decisions correctes i errors. Prepareu una demostració breu en què es pugui canviar una observació i seguir la cadena fet–activació–elaboració–candidats–valoració–decisió–acció. Completeu l'informe i verifiqueu la instal·lació des d'un entorn net.

---

## 5. Planificació de tasques

La planificació següent és orientativa. Les hores són l'esforç agregat del grup.

| Període | Dedicació | Resultats esperats |
|---|---|---|
| Setmana 1 | 0 h lab + 9,5 h externes | Lectura; conceptes bàsics de SOAR; delimitació; mapa de coneixement; fonts; tres escenaris inicials; repartiment de rols. |
| Setmana 2 | 2 h lab + 13 h externes | Entorn CLIPS operatiu; primera taula SOAR–CLIPS; contracte d'entrades/sortides; cicle deliberatiu mínim; repositori. |
| Setmana 3 | 2 h lab + 13 h externes | Model conceptual; `deftemplate`; discretització justificada; regles d'elaboració; proves de la interpretació simbòlica. |
| Setmana 4 | 2 h lab + 13 h externes | Mòduls i fases; catàleg d'operadors; prototip vertical; experiment amb l'agenda; primera traça explicada. |
| Setmana 5 | 2 h lab + 13 h externes | Restriccions i valoracions; conflictes del domini; impasses explícits; integració amb el simulador; tres sectors. |
| Setmana 6 | 2 h lab + 13 h externes | Prototip complet; excepcions i fallades; vuit casos definits; resultats preliminars; extensió opcional avaluada. |
| Setmana 7 | 0 h lab + 8,3 h externes | Experiments finals; informe; guia de reproducció; revisió creuada; paquet de lliurament i demostració. |

Es recomana rotar la revisió: ningú no hauria de ser l'única persona que entén els `deftemplate`, l'agenda, les valoracions o la integració. Quatre persones davant d'un únic ordinador durant una hora compten com una hora de treball agregat, no quatre.

---

## 6. Rúbrica d'avaluació

La nota es calcularà sobre 100 punts. Per a nivells intermedis es pot assignar una puntuació proporcional entre les descripcions. Un sistema que no s'executi o que delegui la decisió principal a Python o a un altre component extern no pot assolir els nivells alts dels criteris de CLIPS.

### A. Enginyeria del coneixement (20 punts)

| Criteri | Insuficient | Acceptable | Excel·lent |
|---|---|---|---|
| Identificació i fonts (6) | Reprodueix l'enunciat; fonts escasses o no avaluades. | Objectius i fonts pertinents, amb viabilitat i limitacions bàsiques. | Anàlisi pròpia i precisa; fonts diverses i autoritzades; qualitat, biaixos, llicències i ús justificats. |
| Conceptualització (7) | Conceptes inconnexos i sense procés de resolució. | Conceptes, relacions i subproblemes principals descrits. | Model complet i coherent; exemples de coneixement expert; dependències i procés de resolució clarament justificats. |
| Formalització (7) | No hi ha correspondència clara entre domini i símbols. | La major part del domini té representació i llindars raonables. | Vocabulari formal complet; restriccions, incertesa/discretització i decisions de modelatge argumentades i traçables. |

### B. Model CLIPS i estratègia de raonament (30 punts)

| Criteri | Insuficient | Acceptable | Excel·lent |
|---|---|---|---|
| Correspondència SOAR–CLIPS (4) | SOAR només es menciona o s'usa com a etiqueta. | Es relacionen els conceptes principals amb components de CLIPS. | Correspondència completa i crítica; es demostra a les traces què s'ha preservat, aproximat o exclòs. |
| Fets i `deftemplate` (5) | Fets plans, redundants o inconsistents; observacions i inferències es confonen. | Plantilles funcionals amb la majoria d'elements necessaris. | Plantilles clares i documentades; tipus de fet, domini, origen, persistència i actualització coherents. |
| Produccions (5) | Regles monolítiques, específiques per cas o que deleguen la decisió. | Separació bàsica entre elaboració, proposta i aplicació. | Regles petites i generals; elaboració, proposta, avaluació i aplicació separades i documentades. |
| Mòduls i fases (4) | No hi ha control explícit o depèn de la casualitat de l'agenda. | Cicle funcional i separació parcial de responsabilitats. | Mòduls, focus i transicions reprodueixen el cicle deliberatiu i el retorn des de deliberació. |
| Operadors i conflictes del domini (4) | Acció directa sense candidats ni comparació. | Candidats i preferències explícites per als casos comuns. | Restriccions dures, objectius tous i valoracions justificades; alternatives i empats totalment traçables. |
| Agenda de CLIPS (4) | Salience arbitrària o desconeixement de les activacions. | Ús bàsic i justificat de prioritats i estratègia. | Experiment comparatiu; efectes de salience, especificitat i estratègies analitzats sense confondre'ls amb el domini. |
| Impasses explícits (4) | No es detecten o el sistema es bloqueja. | Es detecten i resolen dos tipus d'impasse. | Deliberació explícita, justificable i reutilitzable; dades, historial, reversibilitat o intervenció humana emprats coherentment. |

### C. Implementació i integració (20 punts)

| Criteri | Insuficient | Acceptable | Excel·lent |
|---|---|---|---|
| Simulador i integració (6) | Entrades fixes o ordres sense efecte verificable. | Simulador reproduïble i connexió amb CLIPS funcional. | Bucle tancat robust; diversos sectors, temps, errors i efectes modelats; Python calcula o simula però no decideix. |
| Qualitat del codi (5) | Codi desorganitzat, fràgil o sense instruccions. | Estructura raonable, comentaris i execució documentada. | Estructura modular, configuració separada, validacions, versions fixades i arrencada reproduïble. |
| Traçabilitat i explicació (5) | Només es mostra l'acció final. | Es registren regles, candidats i motiu principal. | Explicació llegible vinculada a evidències, elaboracions, preferències, operador i efecte observat. |
| Extensió avaluada (4) | Extensió decorativa o no funcional. | Extensió funcional amb exemple. | Hipòtesi, línia base, mètrica i anàlisi crítica; o, si no hi ha extensió, profunditat equivalent en robustesa. |

### D. Jocs de prova i anàlisi (15 punts)

| Criteri | Insuficient | Acceptable | Excel·lent |
|---|---|---|---|
| Cobertura (7) | Menys de 5 casos o variants trivials. | Almenys 8 casos diferents, incloent seguretat i conflicte. | Cobertura sistemàtica de normalitat, límits, dades absents, fallades, canvis temporals i casos no vistos. |
| Evidències i explicació (5) | Resultats manuals o sense entrades ni traces. | Entrades, sortides originals i explicació adequada. | Experiments reproduïbles; traces seleccionades; resultats esperats i observats; discrepàncies analitzades. |
| Avaluació (3) | Afirmacions sense criteris. | Mètriques simples de decisions i seguretat. | Mètriques pertinents (violacions, energia, estrès, moviments, cicles) i discussió dels compromisos. |

### E. Informe, equip i demostració (15 punts)

| Criteri | Insuficient | Acceptable | Excel·lent |
|---|---|---|---|
| Informe (6) | Desorganitzat, poc clar o incomplet. | Estructura correcta i explicacions comprensibles. | Relat concís i rigorós; figures útils; decisions justificades; conclusions i limitacions honestes. |
| Treball en equip (4) | Repartiment opac o integració tardana. | Planificació, responsabilitats i coordinació documentades. | Integració contínua, revisió creuada, gestió de conflictes i contribució equilibrada demostrables. |
| Demostració (5) | No funciona o no es pot explicar. | Executa casos preparats i respon preguntes bàsiques. | Modificació en directe d'un escenari; traça completa; tots els membres poden explicar arquitectura i decisions. |

### Condicions de suficiència

Per aprovar cal, a més de la nota global, que: (1) el sistema s'executi; (2) la decisió principal es faci en CLIPS; (3) la implementació mostri explícitament el cicle inspirat en SOAR; (4) es generin diversos operadors candidats i es resolgui almenys un conflicte del domini; (5) es documentin dos tipus d'impasse i la deliberació que els resol; (6) s'analitzi l'agenda; i (7) els lliurables permetin reproduir almenys un cas complet.

---

## 7. Competència "Treball en equip"

*Capítol omès en aquesta transcripció: l'equip el gestiona fora del repositori.*

---

## 8. Competència "Ús solvent dels recursos d'informació"

Cal identificar necessitats d'informació, cercar fonts adequades, seleccionar-les, sintetitzar-les i fer-ne un ús legal i ètic. Hi ha quatre famílies de fonts: arquitectura SOAR; documentació de CLIPS i de la integració; coneixement agronòmic i agrovoltaic; i dades meteorològiques, energètiques o de sensors.

Per cada font candidata i, especialment, per cada font finalment utilitzada, indiqueu:

- creador, responsabilitat editorial i tipus de contingut;
- coneixement o dades que aporta i decisions del sistema que en depenen;
- qualitat, actualitat, cobertura, incertesa i possibles biaixos;
- llicència, atribució, límits de reutilització i transformacions efectuades;
- riscos derivats d'aplicar una font genèrica a un cultiu o context local;
- mecanisme de versionament o data de consulta.

L'accés públic no implica permís de reutilització. Eviteu copiar conjunts de dades o documentació sense comprovar-ne la llicència. Si useu dades reals de finques, elimineu identificadors i informació comercial sensible. Les dades sintètiques s'han d'etiquetar com a tals i no s'han de presentar com a mesures agronòmiques validades.

---

## 9. Recursos inicials

Els recursos següents són un punt de partida, no substitueixen la cerca crítica del grup:

- Arquitectura SOAR: <https://soar.eecs.umich.edu/soar_manual/02_TheSoarArchitecture/>
- Repositori oficial de SOAR: <https://github.com/SoarGroup/Soar>
- Web oficial de CLIPS: <https://www.clipsrules.net/>
- Documentació oficial, inclosos el User's Guide i el Basic Programming Guide: <https://www.clipsrules.net/Documentation.html>
- Descàrregues i distribucions de CLIPS: <https://sourceforge.net/projects/clipsrules/>
- Documentació de clipspy: <https://clipspy.readthedocs.io/en/stable/>
- Repositori de clipspy: <https://github.com/noxdafox/clipspy>

SOAR aporta el patró deliberatiu que cal adaptar: estat, elaboracions, proposta d'operadors, preferències, selecció, aplicació i impasses que obren deliberació addicional. CLIPS aporta el llenguatge de programació basat en regles amb encadenament cap endavant, fets, objectes, mòduls, agenda i estratègies de resolució de conflictes. clipspy ofereix una capa Python sobre les API natives de CLIPS; s'ha d'utilitzar com a mecanisme d'integració, no per substituir el raonament simbòlic.

---

## 10. Ús d'eines d'intel·ligència artificial

D'acord amb les recomanacions del Comitè d'Ètica de les Publicacions (COPE), adoptades per les principals editorials acadèmiques, i en coherència amb els valors que tot l'estudiantat de la UPC assumeix en signar el Compromís d'integritat acadèmica de la UPC, es recomana incloure una declaració explícita sobre l'ús d'eines d'intel·ligència artificial generativa que incorpori els elements següents:

- Eina o eines utilitzades, indicant-ne les versions del programari.
- Finalitat del seu ús.
- Parts o seccions específiques en què s'han utilitzat, si escau.
- Revisió i edició, per part dels autors, del resultat generat per l'eina, si escau.
- Declaració de responsabilitat dels autors sobre els continguts de l'obra.

En el cas de les eines d'intel·ligència artificial generativa que permetin crear un enllaç permanent (URL) al contingut generat o a la sessió de treball, també es recomana utilitzar una citació bibliogràfica.

Per a més informació, podeu consultar:

1. Biblioguia: com citar i elaborar bibliografies.
2. Com citar la IA en els treballs acadèmics.

---

## Annex A. Exemple mínim de representació i control

Aquest fragment és orientatiu i no prescriu els noms exactes ni els llindars:

```clips
(deftemplate control
   (slot instant)
   (slot fase))

(deftemplate observacio
   (slot sector)
   (slot temperatura)
   (slot radiacio)
   (slot humitat-sol)
   (slot vent))

(deftemplate operador-candidat
   (slot sector)
   (slot tipus)
   (slot puntuacio (default 0))
   (multislot motius))

(deftemplate risc
   (slot sector)
   (slot tipus)
   (slot nivell))

(defrule interpretar-vent-critic
   (control (fase interpretacio))
   (observacio (sector ?s) (vent ?v&:(> ?v 70)))
   =>
   (assert (risc (sector ?s)
                 (tipus mecanic)
                 (nivell critic))))
```

## Annex B. Exemple mínim de traça d'una decisió

```text
Fets d'entrada: sector=s2, vent=82, panell=operatiu
Regla activada: interpretar-vent-critic
Fet derivat: risc-mecanic=critic
Candidats: posicio-seguretat, mantenir-posicio
Eliminacio: mantenir-posicio viola restriccio-seguretat
Decisio: posicio-seguretat
Ordre: sector=s2, angle=0, motiu=vent-critic
Resultat observat: angle=0, alarma-mecanica=no
```

Una bona explicació no es limita a repetir la regla. Ha de mostrar quins fets sustenten la inferència, quines regles s'han activat, per què cada operador era aplicable, quines alternatives competien, quin criteri ha decidit i si l'efecte observat confirma l'acció.
