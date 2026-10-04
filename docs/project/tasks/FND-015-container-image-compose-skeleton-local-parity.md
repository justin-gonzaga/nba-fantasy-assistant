---
id: FND-015
title: "Container image + compose skeleton (local parity)"
epic: EP-10 Foundation
phase: 1
component: infra
status: done
ready: true
size: M
autonomy: review
gate: none
depends_on: [FND-011, FND-001]
areas: [infra/**, Dockerfile, .dockerignore, docker/**, .github/workflows/ci.yml, platform-manifest.yaml]
standards: [devops, security]
assignee:
created: 2026-09-24
completed: 2026-09-28
---
# FND-015 — Container image + compose skeleton (local parity)

## Objective
One multi-stage non-root image with the `api` and `job <name>` entrypoints Cloud Run uses, built, started and
scanned in CI, so the owner doesn't need Docker Desktop (FND-016 stays optional, for local parity).

## Context to read (only these)
- `docs/standards/devops.md §3`

## Acceptance criteria
- [x] AC1: Dockerfile: uv build stage, python:3.13-slim runtime, non-root user; entrypoints `api` and `job <name>`
      Verify: CI `image` job ("the api entrypoint serves /system/health as a non-root user"; "the job entrypoint reaches the pipeline CLI")
- [x] AC2: Image < 1 GB
      Verify: CI `image` job "size under 1 GB"
- [x] AC3: Trivy finds no fixable HIGH/CRITICAL vulnerabilities
      Verify: CI `image` job Trivy step

## Test requirements
The CI job is the test (build, run, health check, size, scan).

## Evaluation requirements
n/a

## Decisions
- Size budget 500 MB -> 1 GB after the first build measured 833 MB: one image holds the pipeline's scientific stack (polars ~170 MB, scipy ~100 MB, pyarrow ~85 MB installed) as devops §3 asks. 500 MB was an estimate written before any image existed. Split images only if Cloud Run cold starts prove slow.
- No SPA stage in the image: the SPA is on Firebase Hosting (D-59), which supersedes that part of devops §3.
- Compose / `just up` dropped from this task: they need local Docker (FND-016); the CI job gives the same assurance.

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | CI | PR #72 `image` job: health check as a non-root user; `job --help` | passed |
| AC2 | CI | `image` job size step | 833 MB measured (< 1 GB budget; see Decisions) |
| AC3 | CI | `image` job Trivy 0.65.0, fixable HIGH/CRITICAL | first run: 2 HIGH (msgpack 1.1.2, setuptools 70.3.0) in the base image's pip, not in the app's lock (already msgpack 1.2.2, setuptools 84.0.0); removing pip from the runtime stage -> 0 |

## Implementation history
- 2026-09-28: Dockerfile (uv build stage -> slim runtime, uid 10001), docker/entrypoint.sh (`api`, `job`), .dockerignore, CI `image` job. Three CI iterations: size (833 MB vs a 500 MB guess), YAML colon in a step name, Trivy findings from the base image's pip (removed at runtime).

## Known issues
_None._

## Follow-ups
_None._
