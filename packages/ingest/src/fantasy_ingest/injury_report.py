"""Official NBA injury report PDFs (DATA-007; DISC-005 findings).

Parsing is positional (pdfplumber): the column boundaries come from each report's own header row
("Game Date … Reason"), words are grouped into lines by their vertical position, and a line with a
status word is a player row. Reason text that wraps onto lines above or below attaches to the
nearest player row on the page. Game date/time, matchup and team print only on a group's first row,
so they carry forward. "NOT YET SUBMITTED" lines are team-level and produce no rows.

Point in time: the timestamp printed in the header is `valid_at`; our fetch time is `observed_at`.
A layout this parser doesn't understand raises `UnknownLayout` (the PDF is still stored).
"""

from __future__ import annotations

import io
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from typing import Any, Protocol

import pdfplumber

from dikit.errors import ContractViolation
from dikit.logging import get_logger
from dikit.store.snapshot import SnapshotStore
from dikit.time.clock import Clock
from fantasy_core.gamedate import NBA_TZ

log = get_logger(__name__)

SOURCE = "nba_injury_report"
EXTRACTOR_VERSION = "1.0.0"
URL = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_{day}_{slot}.pdf"
STATUSES = frozenset({"Available", "Probable", "Questionable", "Doubtful", "Out"})
COLUMNS = ("game_date", "game_time", "matchup", "team", "player", "status", "reason")
HEADER_WORDS = ("Game", "Game", "Matchup", "Team", "Player", "Current", "Reason")
LINE_TOLERANCE = 2.0
SLOT_MINUTES = 15
MAX_SLOTS = 16  # look back 4 hours for the latest report
_HEADER_TS = re.compile(r"Injury Report: (\d{2}/\d{2}/\d{2}) (\d{2}:\d{2}) ([AP]M)")
_FOOTER = re.compile(r"^Page \d+ of \d+$")
_NOT_SUBMITTED = "NOT YET SUBMITTED"


class UnknownLayout(ContractViolation):
    pass


class OptionalFetcher(Protocol):
    def get_optional(self, url: str, params: Any = None) -> bytes | None: ...


@dataclass(frozen=True)
class Row:
    game_date: date
    game_time: str
    matchup: str
    team: str
    player: str
    status: str
    reason: str


@dataclass(frozen=True)
class Report:
    valid_at: datetime
    rows: list[Row]


def _lines(words: list[dict[str, Any]]) -> list[tuple[float, list[dict[str, Any]]]]:
    out: list[tuple[float, list[dict[str, Any]]]] = []
    for w in sorted(words, key=lambda w: (w["top"], w["x0"])):
        if out and abs(out[-1][0] - w["top"]) <= LINE_TOLERANCE:
            out[-1][1].append(w)
        else:
            out.append((w["top"], [w]))
    return out


def _text(ws: list[dict[str, Any]]) -> str:
    return " ".join(w["text"] for w in sorted(ws, key=lambda w: w["x0"]))


def _valid_at(first_page_words: list[dict[str, Any]]) -> datetime:
    head = _text([w for w in first_page_words if w["top"] < first_page_words[0]["top"] + 5])
    m = _HEADER_TS.search(head)
    if not m:
        msg = f"injury report header timestamp not found in {head!r}"
        raise UnknownLayout(msg)
    local = datetime.strptime(" ".join(m.groups()), "%m/%d/%y %I:%M %p").replace(tzinfo=NBA_TZ)
    return local.astimezone(UTC)


def _header(lines: list[tuple[float, list[dict[str, Any]]]]) -> tuple[float, list[float]]:
    """(top of the header row, the x where each column starts)."""
    for top, ws in lines:
        texts = [w["text"] for w in sorted(ws, key=lambda w: w["x0"])]
        if texts[:1] == ["Game"] and "Reason" in texts:
            starts: list[float] = []
            i = 0
            for w in sorted(ws, key=lambda w: w["x0"]):
                if i < len(HEADER_WORDS) and w["text"] == HEADER_WORDS[i]:
                    starts.append(float(w["x0"]) - 3)
                    i += 1
            if len(starts) == len(COLUMNS):
                return top, starts
    msg = "injury report column header not found"
    raise UnknownLayout(msg)


def _cells(ws: list[dict[str, Any]], starts: list[float]) -> dict[str, str]:
    cells: dict[str, list[dict[str, Any]]] = {c: [] for c in COLUMNS}
    for w in ws:
        idx = max(i for i, s in enumerate(starts) if w["x0"] >= s) if w["x0"] >= starts[0] else 0
        cells[COLUMNS[idx]].append(w)
    return {c: _text(v) for c, v in cells.items()}


@dataclass
class _Draft:
    """A player row while its (possibly wrapped) reason is still being collected."""

    ctx: dict[str, str]
    player: str
    status: str
    parts: list[tuple[float, str]] = field(default_factory=list)

    def row(self) -> Row:
        day = datetime.strptime(self.ctx["game_date"], "%m/%d/%Y").replace(tzinfo=NBA_TZ)
        return Row(
            game_date=day.date(),
            game_time=self.ctx["game_time"],
            matchup=self.ctx["matchup"],
            team=self.ctx["team"],
            player=self.player,
            status=self.status,
            reason=" ".join(t for _, t in sorted(self.parts)),
        )


def _page(
    lines: list[tuple[float, list[dict[str, Any]]]],
    starts: list[float],
    header_top: float,
    ctx: dict[str, str],
) -> list[_Draft]:
    """Player rows of one page; `ctx` (game + team) carries over between pages."""
    anchors: list[tuple[float, _Draft]] = []
    fragments: list[tuple[float, str]] = []
    for top, ws in lines:
        line = _text(ws)
        skip = _FOOTER.match(line) or line.startswith("Game Date Game Time")
        if top <= header_top + LINE_TOLERANCE or skip:
            continue
        c = _cells(ws, starts)
        ctx.update({k: c[k] for k in ctx if c[k]})
        if c["status"] in STATUSES and c["player"]:
            draft = _Draft(dict(ctx), c["player"], c["status"])
            if c["reason"]:
                draft.parts.append((top, c["reason"]))
            anchors.append((top, draft))
        elif c["reason"] and _NOT_SUBMITTED not in c["reason"] and not c["player"]:
            fragments.append((top, c["reason"]))
    for top, text in fragments:
        if anchors:
            min(anchors, key=lambda a: abs(a[0] - top))[1].parts.append((top, text))
    return [d for _, d in anchors]


def parse(pdf: bytes) -> Report:
    ctx = dict.fromkeys(("game_date", "game_time", "matchup", "team"), "")
    drafts: list[_Draft] = []
    valid_at: datetime | None = None
    starts: list[float] | None = None
    with pdfplumber.open(io.BytesIO(pdf)) as doc:
        for page in doc.pages:
            words = page.extract_words(x_tolerance=1.5)
            if not words:
                continue
            valid_at = valid_at or _valid_at(words)
            lines = _lines(words)
            if (
                starts is None
            ):  # the column header prints on the first page (some layouts: every page)
                header_top, starts = _header(lines)
            else:
                header_top = lines[0][0]  # later pages start with the title line
            drafts += _page(lines, starts, header_top, ctx)
    if valid_at is None or not drafts:
        msg = "injury report produced no rows (unsupported layout?)"
        raise UnknownLayout(msg)
    return Report(valid_at, [d.row() for d in drafts])


def _slot_label(t: datetime) -> tuple[str, str]:
    """(new 15-minute label e.g. 05_15PM, legacy hourly label e.g. 05PM)."""
    return t.strftime("%I_%M%p"), t.strftime("%I%p")


def candidate_urls(day: date, latest: datetime) -> list[str]:
    """Report URLs for `day`, newest first, from `latest` back MAX_SLOTS quarter-hours.

    Both formats: the new 15-minute names and the legacy hourly names (the legacy `_05PM` file
    is the 5:30 report)."""
    local = latest.astimezone(NBA_TZ)
    end = min(local, datetime.combine(day, time(23, 59), tzinfo=NBA_TZ))
    t = end.replace(minute=end.minute - end.minute % SLOT_MINUTES, second=0, microsecond=0)
    urls: list[str] = []
    for _ in range(MAX_SLOTS):
        if t.date() != day:
            break
        new, legacy = _slot_label(t)
        urls.append(URL.format(day=day.isoformat(), slot=new))
        if t.minute == 30:  # noqa: PLR2004 - the legacy hourly file is the :30 report
            urls.append(URL.format(day=day.isoformat(), slot=legacy))
        t -= timedelta(minutes=SLOT_MINUTES)
    return urls


def _rows_json(rep: Report) -> bytes:
    return json.dumps(
        {
            "extractor_version": EXTRACTOR_VERSION,
            "valid_at": rep.valid_at.isoformat(),
            "rows": [{**asdict(r), "game_date": r.game_date.isoformat()} for r in rep.rows],
        }
    ).encode()


def fetch_latest(
    store: SnapshotStore,
    client: OptionalFetcher,
    clock: Clock,
    day: date,
    *,
    latest: datetime | None = None,
) -> Report | None:
    """Store the newest published report for `day` (PDF + extracted rows). None when nothing new.

    `latest` bounds the report slot for a historical backfill (default: now). Snapshots are always
    stamped with the real fetch time (clock.now()), never the report's time."""
    for url in candidate_urls(day, latest or clock.now()):
        pdf = client.get_optional(url)
        if pdf is None:
            continue
        key = f"report={url.rsplit('Injury-Report_', 1)[1].removesuffix('.pdf')}"
        if store.has(SOURCE, "report_pdf", key):
            return None
        store.write(SOURCE, "report_pdf", key, pdf, clock.now(), ext="pdf", params={"url": url})
        try:
            rep = parse(pdf)
        except UnknownLayout:
            log.error("injury_report_quarantined", key=key)  # the PDF is kept for a later parser
            raise
        store.write(SOURCE, "report_rows", key, _rows_json(rep), clock.now(), rows=len(rep.rows))
        log.info("injury_report_stored", key=key, rows=len(rep.rows), valid_at=rep.valid_at)
        return rep
    return None


def stored_report(store: SnapshotStore, day: date) -> tuple[str, list[dict[str, Any]]] | None:
    """(key, rows) of the newest stored report for `day` by report time, or None."""
    prefix = f"report={day.isoformat()}_"
    docs = [
        (str(m["key"]), json.loads(store.read(m["path"])))
        for m in store.manifest(SOURCE)
        if m["endpoint"] == "report_rows" and str(m["key"]).startswith(prefix)
    ]
    if not docs:
        return None
    key, doc = max(docs, key=lambda kd: kd[1]["valid_at"])
    rows: list[dict[str, Any]] = doc["rows"]
    return key, rows


def stored_rows(store: SnapshotStore, day: date) -> list[dict[str, Any]]:
    """Rows of the newest stored report for `day`, or []."""
    found = stored_report(store, day)
    return found[1] if found else []
