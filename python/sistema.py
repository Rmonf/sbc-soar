"""Puente con CLIPS: carga el sistema, aserta las observaciones de cada ciclo y lee los resultados.
Python no decide: nunca modifica ni retracta hechos."""

import re
from pathlib import Path

import clips

import ontologia

CLIPS = Path(__file__).resolve().parent.parent / "clips"
SENSORES = ("vent", "radiacio", "temp-cultiu", "humitat-sol")
PREDICCIONES = ("angle-captacio", "angle-ombra")
# B0 sustituye a la evaluación, la selección, la deliberación y el aprendizaje.
SUSTITUIDOS_POR_B0 = {"05_avaluacio.clp", "06_seleccio.clp", "07_deliberacio.clp", "10_aprenentatge.clp"}


class Captura(clips.Router):
    """Guarda la traza (router traza), las reglas disparadas (watch rules) y los errores."""

    def __init__(self):
        super().__init__("captura", 30)
        self.texto = {"traza": [], "stdout": [], "stderr": [], "stdwrn": []}

    def query(self, nombre):
        return nombre in self.texto

    def write(self, nombre, mensaje):
        self.texto[nombre].append(mensaje)

    def vaciar(self, nombre):
        texto = "".join(self.texto[nombre])
        self.texto[nombre].clear()
        return texto


def _python(v):
    if isinstance(v, tuple):
        return [_python(x) for x in v]
    return str(v) if isinstance(v, clips.Symbol) else v


class Sistema:
    def __init__(self, estrategia="depth", aprendizaje=True, variante=None):
        self.env = clips.Environment()
        self.captura = Captura()
        self.env.add_router(self.captura)
        for f in sorted(CLIPS.glob("[01][0-9]_*.clp")):
            if not (variante == "b0" and f.name in SUSTITUIDOS_POR_B0):
                self.env.load(str(f))
        if variante == "b0":
            self.env.load(str(CLIPS / "b0.clp"))
        self.env.eval(f"(set-strategy {estrategia})")
        self.env.eval("(seed 42)")  # estrategia random reproducible
        self.env.eval("(watch rules)")
        self.env.reset()
        ontologia.cargar(self.env, aprendizaje)

    def _hechos(self, plantilla):
        return [{k: _python(v) for k, v in dict(f).items()}
                for f in self.env.facts() if f.template.name == plantilla]

    def paso(self, t: int, observaciones: dict) -> dict:
        """observaciones: {sector: {variable: valor | "fallada", ..., "panel": {...}}}. Una
        variable o un panel que falta (o es None) no se observa."""
        sensor = self.env.find_template("observacion-sensor")
        for s, obs in observaciones.items():
            for v in SENSORES:
                if obs.get(v) is not None:
                    fallada = obs[v] == "fallada"
                    sensor.assert_fact(sector=clips.Symbol(s), variable=clips.Symbol(v),
                                       valor=0.0 if fallada else float(obs[v]),
                                       calidad=clips.Symbol("fallada" if fallada else "ok"))
            for v in PREDICCIONES:
                self.env.find_template("prediccion").assert_fact(
                    sector=clips.Symbol(s), variable=clips.Symbol(v), valor=float(obs[v]))
            if obs.get("panel"):
                p = obs["panel"]
                self.env.find_template("observacion-panel").assert_fact(**{
                    "sector": clips.Symbol(s), "angulo-actual": float(p["angulo-actual"]),
                    "estado-mecanico": clips.Symbol(p.get("estado-mecanico", "operatiu")),
                    "ocupacion": clips.Symbol(p.get("ocupacion", "lliure"))})
        self.env.find_template("ciclo-temporal").assert_fact(instante=t)
        self.env.run()
        return {
            "ordenes": {o["sector"]: o for o in self._hechos("orden-actuador")},
            "episodios": {e["sector"]: e for e in self._hechos("episodio") if e["instante"] == t},
            "chunks": self._hechos("chunk"),
            "traza": self.captura.vaciar("traza"),
            "reglas": re.findall(r"FIRE\s+\d+\s+(\S+):", self.captura.vaciar("stdout")),
            "errores": self.captura.vaciar("stderr") + self.captura.vaciar("stdwrn"),
        }
