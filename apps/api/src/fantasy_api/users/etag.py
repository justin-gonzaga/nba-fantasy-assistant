"""Reading the version out of an `If-Match` header."""

from __future__ import annotations


def etag_version(if_match: str, prefix: str) -> int | None:
    """`"<prefix>3"` (weak or strong) -> 3; None for anything else."""
    tag = if_match.strip().removeprefix("W/").strip('"')
    if not tag.startswith(prefix) or not tag[len(prefix) :].isdigit():
        return None
    return int(tag[len(prefix) :])
