from test_casos import CASOS

from sbc import ejecutar_caso


def test_b0_carga_y_respeta_r1():
    ruta = next(c for c in CASOS if c.stem == "05_personas_y_viento")
    _, (r,) = ejecutar_caso(ruta, variante="b0")
    assert r["errores"] == ""
    assert r["ordenes"]["s1"]["accion"] == "mantenir-posicio"
    assert r["episodios"]["s1"]["restricciones-activas"] == ["R1"]
