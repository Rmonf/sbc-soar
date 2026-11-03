"""Lee el TTL y carga en CLIPS un hecho por individuo: clase → plantilla, propiedad → slot."""

import re
from functools import cache
from pathlib import Path

import clips
from rdflib import OWL, RDF, Graph, Literal

TTL = Path(__file__).resolve().parent.parent / "ontologia" / "agrovoltaica-soar.ttl"


def _local(uri) -> str:
    return str(uri).rsplit("/", 1)[-1]


def _plantilla(clase: str) -> str:
    """EstadoSOAR → estado-soar, SeguidorSolar → seguidor-solar."""
    return re.sub(r"(?<=[a-z])(?=[A-Z])", "-", clase).lower()


def _valor(o):
    if not isinstance(o, Literal):
        return clips.Symbol(_local(o))
    v = o.toPython()
    if isinstance(v, bool):
        return clips.Symbol("TRUE" if v else "FALSE")
    if isinstance(v, int):
        return v
    try:
        return float(v)
    except (TypeError, ValueError):
        return clips.Symbol(str(v))


@cache
def individuos() -> tuple:
    """(plantilla, {slot: valor}) de cada individuo del TTL."""
    g = Graph().parse(TTL)
    res = []
    for ind in g.subjects(RDF.type, OWL.NamedIndividual):
        clase = next(c for c in g.objects(ind, RDF.type) if c != OWL.NamedIndividual)
        slots = {"id": clips.Symbol(_local(ind))}
        slots |= {_local(p): _valor(o) for p, o in g.predicate_objects(ind) if p != RDF.type}
        res.append((_plantilla(_local(clase)), slots))
    return tuple(res)


def cargar(env: clips.Environment, aprendizaje: bool | None = None):
    """Aserta el conocimiento estático. aprendizaje sobrescribe aprendizaje-activo."""
    for plantilla, slots in individuos():
        t = env.find_template(plantilla)
        slots = {k: v for k, v in slots.items() if k in {s.name for s in t.slots}}
        if plantilla == "parametros-aprendizaje" and aprendizaje is not None:
            slots["aprendizaje-activo"] = clips.Symbol("TRUE" if aprendizaje else "FALSE")
        t.assert_fact(**slots)
