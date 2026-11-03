"""Entorno simulado (datos sintéticos): sol, meteorología (con lluvia y previsión de viento),
cultivo, paneles, producción y fallos. Calcula las observaciones de cada ciclo y aplica las órdenes
de CLIPS. No decide nada."""

import json
import math
import random
from pathlib import Path

import ontologia

CONFIG = Path(__file__).resolve().parent.parent / "config" / "simulacio.json"
SECTORES = ("s1", "s2", "s3")


class Simulador:
    def __init__(self, semilla: int, dias: int = 1):
        self.c = json.loads(CONFIG.read_text(encoding="utf-8"))
        # Generadores separados: las decisiones no cambian ni el tiempo ni el ruido de los sensores.
        self.rng, self.rng_sensor, self.rng_actuador = (random.Random(f"{semilla}-{x}") for x in "msa")
        self.dt, self.t, self.dias = self.c["dt-min"], 0, dias
        estatico = {str(s["id"]): s for _, s in ontologia.individuos()}
        self.cultivo = {s: estatico[str(estatico[s]["tiene-cultivo"])] for s in SECTORES}
        self.seguidor = {s: estatico[str(estatico[s]["tiene-seguidor"])] for s in SECTORES}
        tipos = self.c["tipus-dia"]
        self.tipo_dia = self.rng.choices(list(tipos), [x["prob"] for x in tipos.values()], k=dias)
        self.nubes = tipos[self.tipo_dia[0]]["nuvolositat"]
        self.viento_ruido = 0.0
        self.angulo = {s: 0.0 for s in SECTORES}
        self.humedad = {s: self.cultivo[s]["umbral-humedad-critica"] + self.c["cultiu"]["reg-sobre-umbral"]
                        for s in SECTORES}
        self.eventos = self._eventos()

    def _eventos(self) -> list:
        """(tipo, sector, inicio, fin) de los fallos y de la ocupación de cada día; y tormentas y
        lluvias, con su intensidad en lugar del sector."""
        f, ev = self.c["fallos"], []
        for d in range(self.dias):
            for tipo, p in f["prob-dia"].items():
                for s in SECTORES:
                    if self.rng.random() < p:
                        h0, h1 = f["hores-treball"] if tipo == "persones" else (0, 24)
                        inicio = d * 1440 + int(self.rng.uniform(h0, h1) * 60)
                        ev.append((tipo, s, inicio, inicio + self.rng.randint(*f["durada-min"])))
            v = self.c["vent"]
            if self.rng.random() < v["prob-tempesta-dia"]:
                inicio = d * 1440 + self.rng.randint(0, 1439)
                fin = inicio + int(self.rng.uniform(*v["durada-tempesta-h"]) * 60)
                ev.append(("tempesta", self.rng.uniform(*v["pic-tempesta"]), inicio, fin))
            p = self.c["pluja"]
            if self.rng.random() < p["prob-dia"]:
                inicio = d * 1440 + self.rng.randint(0, 1439)
                fin = inicio + int(self.rng.uniform(*p["durada-h"]) * 60)
                ev.append(("pluja", self.rng.uniform(*p["intensitat-mm-h"]), inicio, fin))
        return ev

    def _activo(self, tipo, s=None, t=None):
        t = self.t if t is None else t
        return next((e for e in self.eventos if e[0] == tipo and (s is None or e[1] == s)
                     and e[2] <= t < e[3]), None)

    def _sol(self, t=None):
        """Elevación relativa (0 de noche) y ángulos de captación y de sombra."""
        sol, hora = self.c["sol"], (self.t if t is None else t) % 1440 / 60
        x = (hora - sol["hora-sortida"]) / (sol["hora-posta"] - sol["hora-sortida"])
        if not 0 < x < 1:
            return 0.0, 0.0, 0.0
        captacion = -60 + 120 * x
        return math.sin(math.pi * x), captacion, max(-60.0, captacion - sol["desfase-ombra"])

    def _sombra(self, s, elevacion, ombra):
        if elevacion == 0:
            return 0.0
        return self.c["panell"]["ombra-maxima"] * math.cos(math.radians(self.angulo[s] - ombra)) ** 2

    def _meteo(self):
        tipo = self.c["tipus-dia"][self.tipo_dia[self.t // 1440]]
        elevacion, captacion, ombra = self._sol()
        radiacion = self.c["sol"]["radiacio-max"] * elevacion * (1 - 0.75 * self.nubes)
        hora = self.t % 1440 / 60
        temp = tipo["temp-mitjana"] + tipo["temp-amplitud"] * math.sin(math.pi * (hora - 9) / 12)
        lluvia = self._activo("pluja")
        return elevacion, captacion, ombra, radiacion, temp, self._viento(self.t), lluvia[1] if lluvia else 0.0

    def _viento(self, t):
        """Viento en t: media diurna con el ruido actual y, si hay tormenta, su perfil."""
        viento = max(0.0, self.c["vent"]["mitja"] + 6 * self._sol(t)[0] + self.viento_ruido)
        tormenta = self._activo("tempesta", t=t)
        if tormenta:
            fase = (t - tormenta[2]) / (tormenta[3] - tormenta[2])
            viento = max(viento, tormenta[1] * math.sin(math.pi * fase))
        return viento

    def _produccion(self, s, radiacion, captacion):
        """Potencia del sector en kW, proporcional a cos(ángulo − ángulo de captación)."""
        p = self.c["panell"]
        factor = max(0.0, math.cos(math.radians(self.angulo[s] - captacion)))
        return radiacion * p["superficie-m2"] * p["rendiment"] * factor / 1000

    def observaciones(self) -> dict:
        elevacion, captacion, ombra, radiacion, temp, viento, lluvia = self._meteo()
        obs, ruido = {}, self.c["soroll"]
        previsto = self._viento(self.t + self.c["vent"]["horitzo-prediccio-min"])
        for s in SECTORES:
            reales = {"vent": viento, "radiacio": radiacion, "humitat-sol": self.humedad[s],
                      "temp-ambient": temp, "pluja": lluvia, "produccio": self._produccion(s, radiacion, captacion),
                      "temp-cultiu": temp + self.c["cultiu"]["efecte-radiacio-temp"] * radiacion / 1000
                                     * (1 - self._sombra(s, elevacion, ombra))}
            o = {v: ("fallada" if self.rng_sensor.random() < self.c["fallos"]["prob-sensor-fallat"]
                     else round(max(0.0, x + self.rng_sensor.gauss(0, ruido[v])), 2)) for v, x in reales.items()}
            o["angle-captacio"], o["angle-ombra"] = round(captacion, 2), round(ombra, 2)
            o["vent-previst"] = round(max(0.0, previsto + self.rng_sensor.gauss(0, ruido["vent-previst"])), 2)
            if not self._activo("panell-sense-comunicacio", s):
                o["panel"] = {"angulo-actual": round(self.angulo[s] + self.rng_sensor.gauss(0, ruido["angulo"]), 2),
                              "ocupacion": "persones" if self._activo("persones", s) else "lliure",
                              "estado-mecanico": "alarma" if self._activo("actuador-alarma", s) else "operatiu"}
            obs[s] = o
        return obs

    def aplicar(self, ordenes: dict):
        """Mueve los paneles según las órdenes (con un error pequeño), integra la humedad y avanza
        un ciclo. Una orden a menos de la tolerancia del ángulo real no mueve el panel."""
        elevacion, _, ombra, radiacion, _, _, lluvia = self._meteo()
        for s, o in sorted(ordenes.items()):
            a, seg = o["angulo-ordenado"], self.seguidor[s]
            if a == "nil" or abs(a - self.angulo[s]) <= seg["tolerancia-angulo"] or self._activo("actuador-encallat", s) \
                    or self._activo("actuador-alarma", s):
                continue
            error = max(-1.0, min(1.0, self.rng_actuador.gauss(0, self.c["panell"]["error-posicio"])))
            self.angulo[s] = max(seg["angulo-minimo"], min(seg["angulo-maximo"], a + error))
        c = self.c["cultiu"]
        for s in SECTORES:
            et = c["et-per-hora"] * radiacion / 1000 * (1 - self._sombra(s, elevacion, ombra)) * self.dt / 60
            self.humedad[s] = min(100.0, max(0.0, self.humedad[s] - et + c["pluja-a-humitat"] * lluvia * self.dt / 60))
            if self.t % 1440 == c["hora-reg"] * 60:
                self.humedad[s] = max(self.humedad[s], self.cultivo[s]["umbral-humedad-critica"] + c["reg-sobre-umbral"])
        tipo = self.c["tipus-dia"][self.tipo_dia[min(self.t // 1440, self.dias - 1)]]
        self.nubes = min(1.0, max(0.0, self.nubes + 0.05 * (tipo["nuvolositat"] - self.nubes) + self.rng.gauss(0, 0.05)))
        self.viento_ruido = 0.9 * self.viento_ruido + self.rng.gauss(0, self.c["vent"]["desviacio"])
        self.t += self.dt


def simular(sistema, semilla: int, dias: int = 1):
    """Ejecuta el bucle cerrado simulador–CLIPS y devuelve el resultado de cada ciclo."""
    sim, pasos = Simulador(semilla, dias), []
    for _ in range(dias * 1440 // sim.dt):
        r = sistema.paso(sim.t, sim.observaciones())
        sim.aplicar(r["ordenes"])
        pasos.append(r)
    return pasos
