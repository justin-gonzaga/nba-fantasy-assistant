import fantasy_core


def test_package_exposes_version() -> None:
    assert isinstance(fantasy_core.__version__, str)
    assert fantasy_core.__version__.count(".") == 2
