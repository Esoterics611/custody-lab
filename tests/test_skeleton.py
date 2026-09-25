import importlib

import pytest

SUBPACKAGES = ["foundations", "mpc", "policy", "trading", "settlement", "reserves", "pq"]


@pytest.mark.parametrize("name", SUBPACKAGES)
def test_subpackage_imports(name: str) -> None:
    assert importlib.import_module(f"custody_lab.{name}").__doc__
