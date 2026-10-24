"""Simulador heurístico del entorno agrovoltaico (roadmap §9, enunciado 3.3 y 3.5).

Calcula, para tres sectores y con pasos de dt minutos, la meteorología, la geometría solar, el
estado del cultivo y de los paneles, y las observaciones y predicciones que Python aserta en
CLIPS. Aplica las órdenes que decide CLIPS: Python calcula o simula, pero no decide.

Todos los modelos son heurísticos y sus datos son sintéticos (informe, capítulo 8):
  - radiación: curva diurna (seno entre la salida y la puesta del sol) × (1 − 0,75·nubosidad),
    con la nubosidad como paseo aleatorio;
  - temperatura ambiente: curva diurna con máximo a las 15 h y desviación aleatoria por día;
  - viento: media diurna con ruido AR(1) y tormentas (probabilidad por día, duración e
    intensidad aleatorias);
  - lluvia: cadena de Markov (empieza y para con probabilidad fija por paso);
  - precio: curva diaria con picos de mañana y tarde;
  - predicciones: el valor real dentro de horitzo-prediccio-min más ruido.
Geometría (supuesto de §9, cultivo entre filas): angle-captacio sigue al sol de −60° (salida) a
60° (puesta) y vale 0 de noche; angle-ombra = max(−60, angle-captacio − 45) es el ángulo que
proyecta la sombra del panel sobre la fila (continuo, y distinto de angle-captacio salvo a la
salida del sol, sin radiación). La sombra sobre el cultivo es
ombra-maxima · cos²(ángulo − angle-ombra) y la producción es proporcional a
cos(ángulo − angle-captacio). El cultivo se calienta con la radiación no sombreada y pierde
humedad por evapotranspiración (Kc × radiación × (1 − sombra)); gana humedad con la lluvia y con
un riego diario fijo, que no decide el sistema.

Fallos inyectables (configuración "fallos"): por lectura, sensor fallada, degradat, antiguo o
ausente; por sector y día, episodios de comunicación del panel perdida (sin observación o con la
última lectura antigua), actuador encallado (no se mueve pero informa operatiu), actuador en
alarma, movimiento no ordenado y ocupación (personas en horario de trabajo, o maquinaria). El
"calendari" fuerza eventos en un instante fijo (también tormentas), para los tests.

La meteorología de toda la ejecución se genera al crear el simulador (las predicciones miran al
futuro). Cada proceso aleatorio tiene su propio generador (SeedSequence.spawn), de modo que
inyectar un fallo no cambia el tiempo meteorológico de la semilla.
"""

import json
import math

import numpy as np

import ontologia
from pont_clips import SIMULACIO

SECTORES = ("s1", "s2", "s3")


def cargar_config() -> dict:
    return json.loads(SIMULACIO.read_text(encoding="utf-8"))


def instalacion() -> dict:
    """Sector -> parámetros de su cultivo y su seguidor, leídos del TTL (§2.2: una sola fuente)."""
    onto = ontologia.leer_ontologia()
    def valores(nombre):
        return {k: (float(v[0][0]) if v[0][1] in ("decimal", "integer") else v[0][0])
                for k, v in onto.individuos[nombre].valores.items()}
    res = {}
    for s in SECTORES:
        sector = valores(s)
        res[s] = {"cultivo": sector["tiene-cultivo"], **valores(sector["tiene-cultivo"]),
                  **valores(sector["tiene-seguidor"])}
    return res


class Meteorologia:
    """Series meteorológicas de toda la ejecución, deterministas por semilla."""

    def __init__(self, config: dict, rng: np.random.Generator):
        m, dt = config["meteo"], config["dt-min"]
        self.dt = dt
        n = int(config["dias"] * 24 * 60 / dt) + int(m["horitzo-prediccio-min"] / dt) + 1
        horas = (np.arange(n) * dt / 60.0) % 24
        dias = (np.arange(n) * dt // (24 * 60)).astype(int)
        self.horas = horas
        # sol: elevación relativa entre la salida y la puesta
        salida, posta = m["hora-sortida"], m["hora-posta"]
        fraccion = np.clip((horas - salida) / (posta - salida), 0, 1)
        self.elevacion = np.where((horas > salida) & (horas < posta), np.sin(np.pi * fraccion), 0.0)
        self.angulo_captacion = np.where(self.elevacion > 0, -60 + 120 * fraccion, 0.0)
        # nubosidad (paseo aleatorio) y lluvia (cadena de Markov)
        nubes, lluvia = np.zeros(n), np.zeros(n)
        c, lloviendo = rng.uniform(0, 0.3), False
        for k in range(n):
            if not lloviendo and rng.random() < m["prob-inici-pluja"]:
                lloviendo, intensidad = True, rng.lognormal(math.log(m["pluja-mitjana"]), 0.6)
            elif lloviendo and rng.random() < m["prob-fi-pluja"]:
                lloviendo = False
            c = float(np.clip(c + rng.normal(0, 0.05), 0, 1))
            nubes[k] = max(c, 0.9) if lloviendo else c
            lluvia[k] = intensidad if lloviendo else 0.0
        self.lluvia = lluvia
        self.radiacion = m["radiacio-max"] * self.elevacion * (1 - 0.75 * nubes)
        # temperatura ambiente: curva diurna con desviación por día
        desviacion = rng.normal(0, m["temp-desviacio-dia"], dias.max() + 1)[dias]
        self.temp_ambiente = (m["temp-mitjana"] + desviacion
                              + m["temp-amplitud"] * np.sin(np.pi * (horas - 9) / 12))
        # viento: media diurna + AR(1) + tormentas
        viento, e = np.zeros(n), 0.0
        for k in range(n):
            e = 0.9 * e + rng.normal(0, m["vent-desviacio"])
            viento[k] = m["vent-mitja"] + 6 * self.elevacion[k] + e
        pasos_dia = int(24 * 60 / dt)
        for d in range(dias.max() + 1):
            if rng.random() < m["prob-tempesta-dia"]:
                inicio = d * pasos_dia + int(rng.integers(0, pasos_dia))
                duracion = int(rng.uniform(*m["durada-tempesta-h"]) * 60 / dt)
                pico = rng.uniform(*m["vent-tempesta"])
                for k in range(inicio, min(n, inicio + duracion)):
                    fase = (k - inicio) / max(1, duracion - 1)
                    viento[k] = max(viento[k], pico * math.sin(math.pi * fase) + rng.normal(0, 3))
        self.viento = np.clip(viento, 0, None)
        # precio: picos de mañana y tarde
        self.precio = np.clip(m["preu-base"] + 30 * np.exp(-((horas - 9) / 2) ** 2)
                              + 60 * np.exp(-((horas - 20) / 2) ** 2) + rng.normal(0, 10, n), 0, None)
        self.horizonte = int(m["horitzo-prediccio-min"] / dt)

    def angulo_sombra(self, k: int) -> float:
        return float(max(-60.0, self.angulo_captacion[k] - 45))


class Simulador:
    """Estado de los tres sectores; observaciones para CLIPS y aplicación de sus órdenes."""

    def __init__(self, semilla: int, config: dict | None = None):
        self.config = config or cargar_config()
        self.semilla = semilla
        self.dt = self.config["dt-min"]
        self.pasos = int(self.config["dias"] * 24 * 60 / self.dt)
        self.instal = instalacion()
        meteo_ss, sensores_ss, fallos_ss, ocupacion_ss = np.random.SeedSequence(semilla).spawn(4)
        self.meteo = Meteorologia(self.config, np.random.default_rng(meteo_ss))
        self.rng_sensores = np.random.default_rng(sensores_ss)
        self.rng_fallos = np.random.default_rng(fallos_ss)
        self.rng_ocupacion = np.random.default_rng(ocupacion_ss)
        c = self.config["cultiu"]
        self.eventos = self._generar_eventos()
        for ev in self.eventos:
            if ev["tipo"] == "tempesta":
                self._forzar_tormenta(ev)
        self.k = 0
        self.ultimo_panel = {}
        self.sectores = {s: {"angulo": 0.0, "estado-mecanico": "operatiu", "ocupacion": "lliure",
                             "humitat": p["umbral-humedad-critica"] + c["humitat-inicial"]}
                         for s, p in self.instal.items()}
        self._actualizar_eventos()

    # --- fallos y eventos -------------------------------------------------------

    def _generar_eventos(self) -> list[dict]:
        """Eventos por sector y día (probabilidad) más los del calendario fijo."""
        f = self.config["fallos"]
        eventos = [dict(ev) for ev in f["calendari"]]
        for d in range(math.ceil(self.config["dias"])):
            for tipo, prob in f["prob-dia"].items():
                rng = self.rng_ocupacion if tipo in ("persones", "maquinaria") else self.rng_fallos
                for s in SECTORES:
                    if rng.random() < prob:
                        if tipo in ("persones", "maquinaria"):
                            h0, h1 = f["hores-treball"]
                            inicio = d * 1440 + int(rng.uniform(h0, h1) * 60)
                        else:
                            inicio = d * 1440 + int(rng.uniform(0, 1440))
                        eventos.append({"tipo": tipo, "sector": s, "inicio-min": inicio,
                                        "durada-min": int(rng.uniform(*f["durada-min"]))})
        return eventos

    def _forzar_tormenta(self, ev: dict):
        m = self.meteo
        k0, n = int(ev["inicio-min"] / self.dt), int(ev["durada-min"] / self.dt)
        for k in range(k0, min(len(m.viento), k0 + n)):
            m.viento[k] = max(m.viento[k], ev["vent"])

    def activo(self, tipo: str, s: str) -> dict | None:
        t = self.instante()
        return next((ev for ev in self.eventos if ev["tipo"] == tipo and ev.get("sector") == s
                     and ev["inicio-min"] <= t < ev["inicio-min"] + ev["durada-min"]), None)

    def _actualizar_eventos(self):
        """Estado mecánico, ocupación y movimientos no ordenados del paso actual (se llama al
        empezar cada paso, antes de leer el estado real y las observaciones)."""
        t = self.instante()
        for s, e in self.sectores.items():
            e["estado-mecanico"] = "alarma" if self.activo("actuador-alarma", s) else "operatiu"
            e["ocupacion"] = ("persones" if self.activo("persones", s)
                              else "maquinaria" if self.activo("maquinaria", s) else "lliure")
            ev = self.activo("moviment-no-ordenat", s)
            if ev and ev["inicio-min"] == t - t % self.dt and not ev.get("hecho"):
                ev["hecho"] = True
                grados = self.rng_fallos.uniform(*self.config["fallos"]["moviment-no-ordenat-graus"])
                signo = 1 if e["angulo"] <= 0 else -1
                e["angulo"] = float(np.clip(e["angulo"] + signo * grados, self.instal[s]["angulo-minimo"],
                                            self.instal[s]["angulo-maximo"]))

    # --- estado real ---------------------------------------------------------

    def instante(self) -> int:
        return self.k * self.dt

    def sombra(self, s: str) -> float:
        m, k = self.meteo, self.k
        if m.elevacion[k] <= 0:
            return 0.0
        dif = math.radians(self.sectores[s]["angulo"] - m.angulo_sombra(k))
        return self.config["panell"]["ombra-maxima"] * math.cos(dif) ** 2

    def temp_cultivo(self, s: str) -> float:
        m, k = self.meteo, self.k
        return float(m.temp_ambiente[k] + self.config["cultiu"]["efecte-radiacio-temp"]
                     * m.radiacion[k] / 1000 * (1 - self.sombra(s)))

    def produccion(self, s: str) -> float:
        """Potencia del sector en kW."""
        m, k, p = self.meteo, self.k, self.config["panell"]
        factor = max(0.0, math.cos(math.radians(self.sectores[s]["angulo"] - m.angulo_captacion[k])))
        return float(m.radiacion[k] * p["superficie-m2"] * p["rendiment"] * factor / 1000)

    def estado_real(self) -> dict:
        m, k = self.meteo, self.k
        return {"instante": self.instante(), "viento": float(m.viento[k]), "lluvia": float(m.lluvia[k]),
                "eventos": sorted({f"{ev['tipo']}:{ev.get('sector', '-')}" for ev in self.eventos
                                   if ev["inicio-min"] <= self.instante() < ev["inicio-min"] + ev["durada-min"]}),
                "radiacion": float(m.radiacion[k]), "precio": float(m.precio[k]),
                "sectores": {s: {**{x: v for x, v in e.items()}, "temp-cultiu": self.temp_cultivo(s),
                                 "actuador-encallat": self.activo("actuador-encallat", s) is not None,
                                 "sombra": self.sombra(s), "produccion": self.produccion(s)}
                             for s, e in self.sectores.items()}}

    # --- observaciones (formato de Pont.paso) -----------------------------------

    def _ruido(self, valor: float, variable: str) -> float:
        return round(float(valor + self.rng_sensores.normal(0, self.config["soroll-sensors"][variable])), 2)

    def _lectura(self, s: str, variable: str, valor: float, t: int) -> dict | None:
        """Lectura de un sensor con los fallos por lectura: ausente (None), fallada, degradat
        o antigua (instante anterior)."""
        f, r = self.config["fallos"], self.rng_fallos.random()
        if self._forzado("sensor-absent", s, variable):
            return None
        lectura = {"sector": s, "variable": variable, "valor": valor, "calidad": "ok"}
        if self._forzado("sensor-fallada", s, variable) or r < f["prob-sensor-fallada"]:
            lectura["calidad"] = "fallada"
        elif r < f["prob-sensor-fallada"] + f["prob-sensor-degradat"]:
            lectura["calidad"] = "degradat"
        elif r < f["prob-sensor-fallada"] + f["prob-sensor-degradat"] + f["prob-sensor-antic"]:
            lectura["instante"] = t - self.dt
        elif r < (f["prob-sensor-fallada"] + f["prob-sensor-degradat"] + f["prob-sensor-antic"]
                  + f["prob-sensor-absent"]):
            return None
        return lectura

    def _forzado(self, tipo: str, s: str, variable: str) -> bool:
        ev = self.activo(tipo, s)
        return ev is not None and ev.get("variable") == variable

    def observaciones(self) -> dict:
        m, k, t = self.meteo, self.k, self.instante()
        sensores, paneles, predicciones = [], [], []
        futuro = min(k + m.horizonte, len(m.viento) - 1)
        for s, e in self.sectores.items():
            reales = {"vent": m.viento[k], "radiacio": m.radiacion[k], "temp-cultiu": self.temp_cultivo(s),
                      "temp-ambient": m.temp_ambiente[k], "humitat-sol": e["humitat"], "pluja": m.lluvia[k]}
            for variable, valor in reales.items():
                v = self._ruido(valor, variable)
                if variable in ("vent", "radiacio", "pluja", "humitat-sol"):
                    v = max(0.0, v)
                lectura = self._lectura(s, variable, v, t)
                if lectura:
                    sensores.append(lectura)
            sensores.append({"sector": s, "variable": "produccio", "valor": round(self.produccion(s), 2),
                             "calidad": "ok"})
            panel = {"sector": s, "angulo-actual": self._ruido(e["angulo"], "angulo"),
                     "estado-mecanico": e["estado-mecanico"], "ocupacion": e["ocupacion"], "instante": t}
            if self.activo("panell-sense-comunicacio", s):
                pass                                      # sin observación del panel
            elif self.activo("panell-lectura-antiga", s) and s in self.ultimo_panel:
                paneles.append(self.ultimo_panel[s])      # se repite la última lectura recibida
            else:
                paneles.append(panel)
                self.ultimo_panel[s] = panel
            predicciones += [
                {"sector": s, "variable": "angle-captacio", "valor": round(float(m.angulo_captacion[k]), 2)},
                {"sector": s, "variable": "angle-ombra", "valor": round(m.angulo_sombra(k), 2)},
                {"sector": s, "variable": "vent-previst",
                 "valor": max(0.0, self._ruido(m.viento[futuro], "prediccio-vent"))},
                {"sector": s, "variable": "pluja-prevista",
                 "valor": max(0.0, self._ruido(m.lluvia[futuro], "prediccio-pluja"))},
            ]
        predicciones.append({"variable": "preu-energia", "valor": round(float(m.precio[k]), 2)})
        return {"instante": t, "sensores": sensores, "paneles": paneles, "predicciones": predicciones}

    # --- efecto de las órdenes y avance ----------------------------------------

    def aplicar(self, ordenes: list[dict]):
        """Aplica las órdenes del instante actual (nil = no mover), integra el paso y avanza.
        Se aplican en orden de sector: el orden en que CLIPS las devuelve depende de la estrategia
        de agenda y no debe cambiar qué error aleatorio de posición recibe cada panel."""
        p = self.config["panell"]
        for o in sorted(ordenes, key=lambda o: o["sector"]):
            if o["instante"] != self.instante() or o["angulo-ordenado"] == "nil":
                continue
            e = self.sectores[o["sector"]]
            if e["estado-mecanico"] == "operatiu" and not self.activo("actuador-encallat", o["sector"]):
                error = float(np.clip(self.rng_fallos.normal(0, p["error-posicio"]), -1, 1))
                lim = self.instal[o["sector"]]
                e["angulo"] = float(np.clip(o["angulo-ordenado"] + error, lim["angulo-minimo"],
                                            lim["angulo-maximo"]))
        self._integrar_humedad()
        self.k += 1
        self._actualizar_eventos()

    def _integrar_humedad(self):
        c, m, k, horas = self.config["cultiu"], self.meteo, self.k, self.dt / 60
        riego = abs(m.horas[k] - c["reg-hora"]) < self.dt / 120
        for s, e in self.sectores.items():
            kc = c["kc"][self.instal[s]["cultivo"]]
            et = kc * c["et-maxima-per-hora"] * m.radiacion[k] / 1000 * (1 - self.sombra(s)) * horas
            e["humitat"] = float(np.clip(e["humitat"] - et + c["pluja-a-humitat"] * m.lluvia[k] * horas,
                                         0, 100))
            if riego:
                objetivo = self.instal[s]["umbral-humedad-critica"] + c["reg-objectiu"]
                e["humitat"] = max(e["humitat"], objetivo)
