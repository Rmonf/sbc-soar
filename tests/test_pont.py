"""Puente con CLIPS: filtro de la fuga conocida de CLIPS (roadmap §13)."""

import json

import executar_casos as ec
import pont_clips as pc

AVISO = ("\n[ENVRNMNT8] Environment data not fully deallocated.\n"
         "\n[ENVRNMNT8] MemoryAmount = 136.\n"
         "\n[ENVRNMNT8] MemoryCalls = 4.\n")


def test_filtro_quita_solo_el_aviso():
    assert pc.AVISO_FUGA.sub("", "antes\n" + AVISO + "despues\n") == "antes\ndespues\n"
    assert pc.AVISO_FUGA.sub("", "[ENVRNMNT9] otro aviso\n") == "[ENVRNMNT9] otro aviso\n"


def _caso_13():
    return json.loads((ec.CASOS / "caso_13_ventana_episodica.json").read_text(encoding="utf-8"))


def _ejecutar(pont):
    for p in _caso_13()["pasos"]:
        pont.paso(p["instante"], p["sensores"], p["paneles"])


def test_sin_filtro_clips_avisa(capfd):
    """El caso 13 reproduce la fuga: destruido sin filtro, CLIPS escribe el aviso en el fd 1."""
    pont = pc.Pont()
    _ejecutar(pont)
    pont.env = None
    pc._LIBC.fflush(None)
    assert "[ENVRNMNT8]" in capfd.readouterr().out


def test_cerrar_filtra_el_aviso(capfd):
    with pc.Pont() as pont:
        _ejecutar(pont)
    assert "[ENVRNMNT8]" not in capfd.readouterr().out
