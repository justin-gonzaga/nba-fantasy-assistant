"""Error hierarchy (software-engineering standard §6)."""


class DikitError(Exception):
    """Base class for all project errors."""


class ConfigError(DikitError):
    """Invalid or missing configuration."""


class SourceUnavailable(DikitError):
    """An external data source could not be reached or returned an error."""

    def __init__(self, source: str, detail: str) -> None:
        super().__init__(f"{source}: {detail}")
        self.source = source
        self.detail = detail


class ContractViolation(DikitError):
    """A payload did not match the data contract we depend on."""


class NaiveDatetimeError(DikitError):
    """A timezone-naive datetime was passed where an aware one is required."""


class LeakageError(DikitError):
    """Data observed after the as-of time was read (temporal leakage)."""
