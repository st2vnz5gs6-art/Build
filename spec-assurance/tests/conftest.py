"""Tests run against a temporary database built from two real specifications."""

import os
import shutil
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_tmp = Path(tempfile.mkdtemp(prefix="sa-test-"))
(_tmp / "library").mkdir()
for name in ("SUB-03-034.pdf", "SUB-01-012.pdf"):
    shutil.copy(ROOT / "library" / name, _tmp / "library" / name)
os.environ["SA_LIBRARY_DIR"] = str(_tmp / "library")
os.environ["SA_DATA_DIR"] = str(_tmp / "data")
os.environ["SA_LLM_MODE"] = "mock"


@pytest.fixture(scope="session", autouse=True)
def indexed_library():
    from spec_assurance import library

    results = library.reindex(force=True)
    assert all(r.status == "ingested" for r in results), results
    yield results
    shutil.rmtree(_tmp, ignore_errors=True)


@pytest.fixture
def conn():
    from spec_assurance import store

    c = store.connect()
    yield c
    c.close()
