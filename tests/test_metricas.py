"""Métricas de §11.2 sobre registros sintéticos con resultado conocido."""

import pytest

import bucle
import metricas
import simulador as sm


@pytest.fixture(scope="module")
def instal():
    return {"s1": sm.instalacion()["s1"]}          # tomate: 30 °C, 45 %; viento crítico 70; tol 2


def _ep(t, accion, previo, ordenado, resultado="ok", impasse="nil", escalado="FALSE"):
    return {"sector": "s1", "instante": t, "accion": accion, "angulo-previo": previo,
            "angulo-ordenado": ordenado, "resultado": resultado, "tipo-impasse": impasse,
            "escalado-humano": escalado}


def _obs(t, panel=True, ocupacion="lliure", estado="operatiu", vent=10.0):
    paneles = [{"sector": "s1", "instante": t, "angulo-actual": 0.0, "ocupacion": ocupacion,
                "estado-mecanico": estado}] if panel else []
    return {"instante": t, "paneles": paneles,
            "sensores": [{"sector": "s1", "variable": "vent", "valor": vent, "calidad": "ok"}],
            "predicciones": [{"sector": "s1", "variable": "vent-previst", "valor": 10.0}]}


def _real(t, viento=10.0, ocupacion="lliure", encallado=False, temp=20.0, humitat=60.0):
    return {"instante": t, "viento": viento,
            "sectores": {"s1": {"ocupacion": ocupacion, "estado-mecanico": "operatiu",
                                "actuador-encallat": encallado, "temp-cultiu": temp,
                                "humitat": humitat, "produccion": 6.0}}}


def _ejecucion(episodios, observaciones, estados):
    ej = bucle.Ejecucion(0, "depth", {"dt-min": 5, "dias": 1})
    ej.episodios, ej.observaciones, ej.estados = episodios, observaciones, estados
    ej.ciclos = [{"disparos": 10 * (i + 1), "cpu": 0.001} for i in range(len(estados))]
    return ej


def test_metricas_conocidas(instal):
    ej = _ejecucion(
        [_ep(0, "mantenir-posicio", 0.0, 0.0),
         _ep(5, "orientar-produccio", 0.0, 30.0, resultado="fallada-actuador"),
         _ep(10, "orientar-ombra", 30.0, -30.0, impasse="tie", escalado="TRUE")],
        [_obs(0), _obs(5, ocupacion="persones", vent=75.0), _obs(10, panel=False)],
        [_real(0), _real(5, viento=80.0, ocupacion="persones", temp=35.0),
         _real(10, encallado=True, humitat=40.0)])
    m = metricas.calcular(ej, instal)
    assert m["decisiones"] == 3
    # t=5: personas observadas y viento observado crítico con orientar-*; t=10: sin panel vigente
    assert m["violaciones-decision"] == {"total": 3, "personas": 1, "sin-panel": 1, "actuador": 0,
                                         "viento": 1, "desgaste": 0}
    # contra el estado real: personas y viento en t=5, actuador encallado en t=10
    assert m["exposicion-real"] == {"total": 3, "personas": 1, "actuador": 1, "viento": 1, "desgaste": 0}
    assert m["movimientos-sector-dia"] == 2
    assert m["tie-100"] == pytest.approx(100 / 3)
    assert m["escalados"] == 1
    assert m["reglas-ciclo"] == 20
    assert m["energia-kwh"] == pytest.approx(3 * 6.0 * 5 / 60)
    assert m["horas-estres-sector-dia"] == pytest.approx(2 * 5 / 60)   # calor en t=5, sequía en t=10


def test_actuador_con_fallada_verificada(instal):
    """Mover cuando MONITORATGE acaba de verificar una fallada (episodio previo) es una violación."""
    ej = _ejecucion([_ep(0, "orientar-ombra", 0.0, -30.0, resultado="fallada-actuador"),
                     _ep(5, "orientar-ombra", 0.0, -30.0)],
                    [_obs(0), _obs(5)], [_real(0), _real(5)])
    assert metricas.calcular(ej, instal)["violaciones-decision"]["actuador"] == 1


def test_desgaste(instal):
    """Un quinto movimiento en la última hora (no de defensa) es una violación; uno de defensa no."""
    angulos = [0.0, 30.0, -30.0, 30.0, -30.0]
    eps = [_ep(10 * i, "orientar-produccio", angulos[i], angulos[i + 1]) for i in range(4)]
    for accion, esperado in (("orientar-ombra", 1), ("posicio-seguretat", 0)):
        ej = _ejecucion(eps + [_ep(40, accion, -30.0, 0.0)],
                        [_obs(10 * i) for i in range(5)], [_real(10 * i) for i in range(5)])
        assert metricas.calcular(ej, instal)["violaciones-decision"]["desgaste"] == esperado


def test_metricas_de_chunks():
    """Un chunk aprendido en s3 en t=0, usado en s3 (t=10, confirmado) y en s1 (t=15, transferido),
    y otro compilado en t=5 y olvidado antes del final."""
    ej = bucle.Ejecucion(0, "depth", {"dt-min": 5, "dias": 1})
    def ep(s, t, accion, impasse="nil", chunk="nil", resultado="ok"):
        return {"sector": s, "instante": t, "accion": accion, "tipo-impasse": impasse,
                "chunk-aplicado": chunk, "resultado": resultado,
                "alternativas": ["orientar-ombra", "orientar-produccio", "mantenir-posicio"]}
    ej.episodios = [ep("s3", 0, "orientar-ombra", impasse="tie"), ep("s3", 5, "mantenir-posicio", impasse="tie"),
                    ep("s3", 10, "orientar-ombra", chunk="k1"),
                    ep("s1", 15, "orientar-ombra", chunk="k1", resultado="pendent")]
    ej.chunks = [{"id": "k1", "instante": 0, "accion-preferida": "orientar-ombra",
                  "accion-descartada": "orientar-produccio", "vivo-hasta": 15},
                 {"id": "k2", "instante": 5, "accion-preferida": "mantenir-posicio",
                  "accion-descartada": "orientar-produccio", "vivo-hasta": 10}]
    ej.ciclos = [{"instante": t, "chunks": n} for t, n in ((0, 1), (5, 2), (10, 2), (15, 1))]
    m = metricas.chunks(ej)
    assert m == {"chunks-vivos-max": 2, "chunks-vivos-final": 1, "chunks-compilados": 2,
                 "chunks-olvidados": 1, "usos-chunk": 2, "usos-chunk-confirmados": 1,
                 "transferencia": 0.5}
