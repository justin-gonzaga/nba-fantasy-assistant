import pytest

from dikit.errors import (
    ConfigError,
    ContractViolation,
    DikitError,
    LeakageError,
    NaiveDatetimeError,
    SourceUnavailable,
)


@pytest.mark.parametrize(
    "exc", [ConfigError, SourceUnavailable, ContractViolation, LeakageError, NaiveDatetimeError]
)
def test_all_errors_derive_from_base(exc: type[Exception]) -> None:
    assert issubclass(exc, DikitError)


def test_source_unavailable_carries_source() -> None:
    err = SourceUnavailable("vendor", "HTTP 503")
    assert err.source == "vendor"
    assert "vendor" in str(err)
    assert "503" in str(err)
