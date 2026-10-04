"""Deterministic, evidence-based explanations (ADR-0016, DEC-009).

A template is filled only from named evidence; it may not contain numbers of its own. Each
`Explanation` keeps the formatted evidence it used, so `ungrounded` can check that every number in
the text came from the evidence (the number round-trip test).
"""

from __future__ import annotations

import re
import string
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

NUMBER = re.compile(r"[-+]?\d+(?:\.\d+)?")


class MissingEvidenceError(KeyError):
    """A template names evidence that wasn't given."""


class LiteralNumberError(ValueError):
    """A template writes a number itself instead of taking it from evidence."""


@dataclass(frozen=True)
class Explanation:
    text: str
    evidence: Mapping[str, str]  # each field as formatted into the text


def render(template: str, **evidence: Any) -> Explanation:
    used: dict[str, str] = {}
    parts: list[str] = []
    for literal, field, spec, conv in string.Formatter().parse(template):
        if NUMBER.search(literal):
            msg = f"numbers must come from evidence, not the template: {literal!r}"
            raise LiteralNumberError(msg)
        parts.append(literal)
        if field is None:
            continue
        if field not in evidence:
            raise MissingEvidenceError(field)
        if conv:
            msg = f"conversion flags aren't supported: {field}!{conv}"
            raise ValueError(msg)
        used[field] = format(evidence[field], spec or "")
        parts.append(used[field])
    return Explanation("".join(parts), used)


def numbers(text: str) -> list[str]:
    return NUMBER.findall(text)


def ungrounded(e: Explanation) -> list[str]:
    """Numbers in the text that don't appear in the formatted evidence (should be empty)."""
    known = {n for v in e.evidence.values() for n in numbers(v)}
    return [n for n in numbers(e.text) if n not in known]
