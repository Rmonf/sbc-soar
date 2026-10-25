"""Refuerzo con recorte de referencias (roadmap §5.10.2).

Con max-referencias = 2 (variante generada con --set), un chunk aplicado y confirmado en cada
paso conserva solo las dos referencias más recientes. Los ángulos de captación y de sombra se
alternan para que el mismo par (sombra mitja, producción alt) empate con Δ similares en cada paso
y el chunk vuelva a aplicarse. En t=20 R4 ya no deja mover (cuatro movimientos en la última hora),
pero ese paso todavía confirma el uso de t=15.
"""

import ontologia as on
import executar_casos as ec

CH = "chunk-orientar-ombra-mitja-orientar-produccio-alt-similar"


def _paso(t, panel, captacio, ombra):
    return {"instante": t, "sectores": {"s3": {
        "sensores": {"temp-cultiu": {"valor": 32, "calidad": "ok"}, "radiacio": {"valor": 600, "calidad": "ok"}},
        "panel": {"angulo-actual": panel},
        "predicciones": {"angle-captacio": captacio, "angle-ombra": ombra}}}}


def test_refuerzo_conserva_las_referencias_mas_recientes(tmp_path):
    base = on.generar_variante(["max-referencias=2"], tmp_path / "base_max2.clp")
    caso = {"id": "recorte", "base": "_base_tranquil", "pasos": [
        _paso(0, 0, 30, -30), _paso(5, -30, 0, -60), _paso(10, -60, -30, -30),
        _paso(15, -30, 0, -60), _paso(20, -60, -30, -30)]}
    pasos = ec.ejecutar_caso(caso, base=base)
    assert all(not p.errores for p in pasos)
    assert [ec.episodio_de(p, "s3")["chunk-aplicado"] for p in pasos] == ["nil", CH, CH, CH, "nil"]
    traza = "".join(p.traza for p in pasos)
    for t, refs in ((10, "0 5"), (15, "5 10"), (20, "10 15")):
        assert f"Aprenentatge (t={t}): reforcat {CH} per l'us de t={t - 5}, referencies=({refs})" in traza
    (chunk,) = pasos[-1].chunks
    assert chunk["referencias"] == [10, 15]
