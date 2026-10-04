---
id: APP-013
title: "Safe profile and team picture uploads (re-encode, strip, separate host)"
epic: EP-75 Accounts and leagues
phase: 7
component: api
status: todo
ready: true
size: M
autonomy: review
gate: G-34
depends_on: [APP-012, APP-024, APP-026]
areas: [apps/api/src/fantasy_api/media/**, apps/api/tests/test_media*.py, packages/core/**]
standards: [backend, security, testing]
assignee:
created: 2026-10-04
completed:
---
# APP-013 — Picture uploads

## Objective
Let a person set a profile picture and (APP-015) a team picture without giving an attacker a place to host files or run
script. The server never stores what was uploaded: it decodes the image, crops it to a square, re-encodes it as a 256 px
WebP with no metadata, and stores that under a random id on a separate, cookie-less host. Rules: the file-upload and
image rules of `docs/standards/user-data-and-auth.md`.

## Context to read (only these)
- `docs/specification/leagues-and-accounts.md` §5 (pictures), §8, §9
- `docs/standards/user-data-and-auth.md` (uploads), `docs/standards/security.md`
- `apps/api/src/fantasy_api/users/*`

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| Member on a phone | "I take a photo and use it" | phone JPEGs with EXIF rotation are rotated correctly, then the EXIF (including GPS) is dropped; a 12 MP photo works within the 2 MB limit by a clear message, not a crash |
| Someone uploads a disguised file | "it is not a picture" | wrong magic bytes, a script renamed `.png`, an SVG, an HTML polyglot, a truncated file, a zip bomb / decompression bomb (pixel cap 4096 × 4096 and 16 MP), animated GIF/WebP: each 422 with a reason, nothing stored |
| Same user uploads often | "no storage abuse" | 10 uploads a day; replacing deletes the old object; at most one picture per profile and per team |
| Person removes their picture | "gone means gone" | `DELETE` removes the object and clears the URL; the CDN path is cache-busted by the random id |
| Reported picture | "hide it now" | a hidden avatar is served as the default for everyone and its object is moved to the private quarantine bucket, so the public URL stops working (INFRA-010); the owner may restore or delete; the uploader is told |
| Wrong content type header | do not trust it | type is decided by decoding, not by the header or the filename |
| Offline storage | degrade | storage down: 503 `media-unavailable`, profile text still saves |
| Account deleted | complete | object deleted in the account-deletion cascade (APP-025) |

## Acceptance criteria
- [ ] AC1: `PUT /me/avatar` accepts JPEG, PNG or WebP ≤ 2 MB and returns `{id, url}` of a 256×256 WebP; the stored
      object has no EXIF/ICC/XMP and a random 128-bit id; the original bytes are never stored.
      Verify: `uv run pytest -q apps/api/tests/test_media.py -k "reencode or metadata or random_id"` (fixtures include a
      GPS-tagged JPEG, asserted clean)
- [ ] AC2: the rejection table is covered row by row: SVG, HTML polyglot, script as `.png`, truncated, > 2 MB,
      > 16 MP, animated, wrong content type, empty body; each returns a stable problem code and stores nothing.
      Verify: `uv run pytest -q apps/api/tests/test_media.py -k "reject"` (parametrised)
- [ ] AC3: decoding is bounded: the pixel limit is set before decoding (a 30 000 × 30 000 header is refused in under
      200 ms without allocating the image) and the call has a time budget.
      Verify: `uv run pytest -q apps/api/tests/test_media.py -k "bomb or budget"`
- [ ] AC4: storage and serving: the store contract writes the object with `Content-Type: image/webp`, a long immutable
      `Cache-Control` and a random name into the media bucket, which is served from the storage origin (not the app
      origin, no cookies); the API can create and delete objects but never lists them. The bucket, its access model and
      the response-header check are INFRA-010.
      Verify: `uv run pytest -q apps/api/tests/test_media.py -k "headers or store"` (store contract on the in-memory and
      the GCS-fake stores)
- [ ] AC5: replace, delete and the hidden state (move to quarantine, restore moves back) work on the in-memory and the
      GCS-fake stores; `hidden` avatars are never returned as their URL; the 10-uploads-a-day quota is a row in APP-024's
      table, not a counter here.
      Verify: `uv run pytest -q apps/api/tests/test_media.py -k "replace or delete or quota_row or hidden or quarantine"`
- [ ] AC6: default avatars: the API returns `avatar: null` plus a deterministic `fallback {initials, colour}` and 12
      preset icon ids; no third-party image is fetched (no Gravatar, no Google photo URL stored).
      Verify: `uv run pytest -q apps/api/tests/test_media.py -k "fallback"`
- [ ] AC7: the new dependency (Pillow) is pinned, is on the dependency-review list in SEC-003, and the decode runs
      with `Image.MAX_IMAGE_PIXELS` set and warnings treated as errors.
      Verify: `uv lock --check`; `uv run pytest -q apps/api/tests/test_media.py -k "pillow_limits"`

- [ ] AC8: avatar objects (profile and team prefixes) are registered in `USER_DATA_OWNERS` (APP-026) with export (URL
      list) and delete functions.
      Verify: `uv run pytest -q apps/api/tests/test_lifecycle_registry.py -k "avatars"`

## Test requirements
Fixture images generated in tests (no binary blobs in git beyond a tiny set, each documented); contract tests shared
by the in-memory and fake-GCS stores; a fuzz-style test feeding random bytes never raises anything but the typed error.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified.

## Decisions
- Re-encoding over scanning: a decoder plus a fresh encoder removes whole classes of attack; an antivirus scan is not
  needed for a format the server writes itself.
- A separate host (not a path on the app origin) so a flaw can never become script execution on the app's origin.

## Known issues
_None._

## Follow-ups
- Moderation queue UI for the owner (APP-017 covers the API).
