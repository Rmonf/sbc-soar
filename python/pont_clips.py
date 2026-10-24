"""Puente entre Python y CLIPS (roadmap §9).

Carga el sistema en un Environment nuevo por ejecución, aserta los hechos observados
(familia 1), ejecuta el ciclo y lee orden-actuador y episodio, junto con la traza y la
secuencia de reglas disparadas. Python no decide: nunca modifica ni retracta hechos.
"""

import ctypes
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import clips

RAIZ = Path(__file__).resolve().parent.parent
CLIPS_DIR = RAIZ / "clips"
BASE = RAIZ / "config" / "base_coneixement.clp"
SIMULACIO = RAIZ / "config" / "simulacio.json"

FIRE = re.compile(r"FIRE\s+\d+\s+(\S+):")
# Aviso de CLIPS al destruir un Environment con memoria sin liberar (roadmap §13)
AVISO_FUGA = re.compile(r"\n?\[ENVRNMNT8\][^\n]*\n")
_LIBC = ctypes.CDLL(None)


def ficheros(base: Path = BASE) -> list[Path]:
    """Orden de carga de §8: 00_main → configuración generada → 01…11."""
    modulos = sorted(p for p in CLIPS_DIR.glob("[01][0-9]_*.clp") if p.name != "00_main.clp")
    return [CLIPS_DIR / "00_main.clp", base, *modulos]


def estrategia_por_defecto() -> str:
    return json.loads(SIMULACIO.read_text(encoding="utf-8"))["estrategia"]


class Captura(clips.Router):
    """Captura la salida de CLIPS por nombre lógico. No reclama otros nombres: el nombre
    'build' lo usa clipspy internamente y reclamarlo hace fallar build (§14)."""

    NOMBRES = ("stdout", "stderr", "stdwrn", "traza")

    def __init__(self):
        super().__init__("captura", 30)
        self.texto = {n: [] for n in self.NOMBRES}

    def query(self, nombre):
        return nombre in self.NOMBRES

    def write(self, nombre, mensaje):
        self.texto[nombre].append(mensaje)

    def vaciar(self, nombre: str) -> str:
        texto = "".join(self.texto[nombre])
        self.texto[nombre].clear()
        return texto


@dataclass
class Paso:
    """Lo que Python lee tras ejecutar un ciclo."""
    instante: int
    disparos: int                       # valor devuelto por run()
    reglas: list[str]                   # nombres de las reglas disparadas, en orden
    ordenes: list[dict]                 # orden-actuador presentes tras el ciclo
    episodios: list[dict]               # episodio presentes tras el ciclo
    traza: str                          # router traza
    errores: str = ""                   # stderr y stdwrn
    ventana_episodica: int = 60         # ?*ventana-episodica* (§2.3.8)
    modulo_de: dict[str, str] = field(default_factory=dict, repr=False)


def _python(valor):
    """Valor de CLIPS a Python: símbolos a str, multislots a lista."""
    if isinstance(valor, tuple):
        return [_python(v) for v in valor]
    if isinstance(valor, clips.Symbol):
        return str(valor)
    return valor


def _clips(valor):
    """Valor de Python a CLIPS: str a símbolo y reales como float (§9)."""
    if isinstance(valor, str):
        return clips.Symbol(valor)
    if isinstance(valor, bool):
        return clips.Symbol("TRUE" if valor else "FALSE")
    if isinstance(valor, int | float):
        return float(valor)
    return valor


class Pont:
    """Una ejecución: un Environment nuevo, un único reset (§9, §14). Se usa con `with`
    (o llamando a cerrar) para destruir el Environment al terminar."""

    def __init__(self, estrategia: str | None = None, base: Path = BASE):
        self.estrategia = estrategia or estrategia_por_defecto()
        self.env = clips.Environment()
        self.captura = Captura()
        self.env.add_router(self.captura)
        for ruta in ficheros(base):
            self.env.load(str(ruta))
        self.env.eval(f"(set-strategy {self.estrategia})")
        self.env.eval("(watch rules)")
        self.env.reset()
        # env.rules() solo da las del módulo actual; get-defrule-list * da las de todos,
        # con el nombre calificado (MODULO::regla), y watch rules escribe el nombre sin módulo
        self.modulo_de = {nombre: modulo for modulo, nombre in
                          (str(r).split("::") for r in self.env.eval("(get-defrule-list *)"))}

    def _asertar(self, plantilla: str, instante: int, slots: dict):
        """El instante es INTEGER; el resto de números son reales (§2.3.9)."""
        self.env.find_template(plantilla).assert_fact(
            instante=instante, **{k: _clips(v) for k, v in slots.items()})

    def _leer(self, plantilla: str) -> list[dict]:
        return [{k: _python(v) for k, v in dict(f).items()}
                for f in self.env.facts() if f.template.name == plantilla]

    def paso(self, instante: int, sensores: list[dict] = (), paneles: list[dict] = ()) -> Paso:
        """Aserta las observaciones y el ciclo-temporal del instante y ejecuta el ciclo."""
        for s in sensores:
            self._asertar("observacion-sensor", instante, {
                "id": f"{s['sector']}-{s['variable']}-{instante}", "calidad": "ok", **s})
        for p in paneles:
            self._asertar("observacion-panel", instante, p)
        self.env.find_template("ciclo-temporal").assert_fact(instante=instante)
        disparos = self.env.run()
        return Paso(
            instante=instante,
            disparos=disparos,
            reglas=FIRE.findall(self.captura.vaciar("stdout")),
            ordenes=self._leer("orden-actuador"),
            episodios=self._leer("episodio"),
            traza=self.captura.vaciar("traza"),
            errores=self.captura.vaciar("stderr") + self.captura.vaciar("stdwrn"),
            modulo_de=self.modulo_de,
            ventana_episodica=self.env.eval("?*ventana-episodica*"),
        )

    def reglas(self) -> list[str]:
        return list(self.modulo_de)

    def cerrar(self):
        """Destruye el Environment y filtra solo el aviso ENVRNMNT8 de la fuga conocida de
        CLIPS (roadmap §13). CLIPS lo escribe con stdio de C en el fd 1 al destruirse, fuera
        de los routers, así que se captura el fd 1 durante la destrucción y se reescribe
        todo lo demás."""
        if self.env is None:
            return
        sys.stdout.flush()
        _LIBC.fflush(None)
        original = os.dup(1)
        with tempfile.TemporaryFile() as tmp:
            os.dup2(tmp.fileno(), 1)
            try:
                self.env = None             # única referencia: se destruye aquí
                _LIBC.fflush(None)
            finally:
                os.dup2(original, 1)
                os.close(original)
            tmp.seek(0)
            resto = AVISO_FUGA.sub("", tmp.read().decode(errors="replace"))
        if resto:
            sys.stdout.write(resto)
            sys.stdout.flush()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.cerrar()
