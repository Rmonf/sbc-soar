from pathlib import Path

import pytest

from sbc import discrepancias, ejecutar_caso

CASOS = sorted((Path(__file__).parent.parent / "casos").glob("*.json"))


@pytest.mark.parametrize("ruta", CASOS, ids=lambda p: p.stem)
def test_caso(ruta):
    assert discrepancias(*ejecutar_caso(ruta)) == []
