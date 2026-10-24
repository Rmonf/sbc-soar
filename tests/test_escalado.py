"""Reserva de terminación: escalar-impasse y S7 (roadmap §4.2, §5.6, §5.7).

Con el conocimiento actual ningún impasse acaba en escalat: demanar-dades y
restriccio-prioritaria siempre se aplican, y el único empate posible (sombra mitja frente a
producción) siempre lo resuelve prioritat-objectius. Para probar la reserva se usa una variante
de configuración en la que produccio-energia tiene la misma prioridad que proteccio-cultiu: con
los Δ iguales, ninguna estrategia da un resultado único. La variante viola a propósito la
comprobación de prioridades 1…5 de §10.1 y solo existe en este test.
"""

import json

import executar_casos as ec
import pont_clips as pc


def test_empate_sin_resolver_se_escala(tmp_path):
    base = pc.BASE.read_text(encoding="utf-8")
    original = "(nombre-objetivo produccio-energia) (prioridad 4)"
    assert original in base
    variante = tmp_path / "base_prioridades_empatadas.clp"
    variante.write_text(base.replace(original, "(nombre-objetivo produccio-energia) (prioridad 3)"),
                        encoding="utf-8")

    caso = json.loads((ec.CASOS / "caso_55_tie_prioritat_objectius.json").read_text(encoding="utf-8"))
    e = ec.expandir_paso(caso, caso["pasos"][0])
    paso = pc.Pont(base=variante).paso(0, e["sensores"], e["paneles"], e["predicciones"])

    assert "escalar-impasse" in paso.reglas and "s7-escalado" in paso.reglas
    (orden,) = [o for o in paso.ordenes if o["sector"] == "s3"]
    assert (orden["accion"], orden["escalado-humano"]) == ("mantenir-posicio", "TRUE")
    episodio = ec.episodio_de(paso, "s3")
    assert (episodio["tipo-impasse"], episodio["criterio-determinante"]) == ("tie", "escalat")
    bloque = ec.bloque_de(paso.traza, "s3")
    assert "Impasse: tie (escalat)" in bloque and "Criteri: escalat" in bloque
    assert ("sector=s3, tie, escalat: cap estrategia dona un resultat unic -> derivat a una persona"
            in paso.traza)
