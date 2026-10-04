import pytest

from fantasy_decision import explain as ex


def test_render_fills_a_template_only_from_named_evidence() -> None:
    e = ex.render(
        "+{add} / -{drop}: {gain:+.2f} cat. wins", add="A Guard", drop="B Big", gain=0.4213
    )
    assert e.text == "+A Guard / -B Big: +0.42 cat. wins"
    assert e.evidence == {"add": "A Guard", "drop": "B Big", "gain": "+0.42"}
    assert ex.ungrounded(e) == []


def test_missing_evidence_is_an_error() -> None:
    with pytest.raises(ex.MissingEvidenceError, match="gain"):
        ex.render("{gain:+.2f}", games=3)


def test_numbers_may_not_be_written_into_a_template() -> None:
    with pytest.raises(ex.LiteralNumberError, match="9"):
        ex.render("{wins:.1f} of 9 categories", wins=4.5)


def test_round_trip_catches_a_number_that_is_not_in_the_evidence() -> None:
    forged = ex.Explanation("gain +0.50", {"gain": "+0.42"})
    assert ex.ungrounded(forged) == ["+0.50"]


def test_digits_inside_evidence_text_are_grounded() -> None:
    e = ex.render("{label} {mark}", label="3PM", mark="▲")
    assert ex.ungrounded(e) == []
