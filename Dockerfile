# One image, two entrypoints (devops standard §3): `api` (Cloud Run service) and `job <name>`
# (Cloud Run jobs, the pipeline CLI). The SPA is served by Firebase Hosting (D-59), not this image.
# Built and scanned in CI (FND-015); no local Docker needed.

FROM python:3.13-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.12.18 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY packages ./packages
COPY apps/api ./apps/api
COPY apps/pipeline ./apps/pipeline
RUN uv sync --frozen --no-dev --no-editable  # the root depends on every workspace member

FROM python:3.13-slim AS runtime
# pip (and what it vendors) isn't needed at runtime: remove it (a no-op if a future base image
# lacks it; the Trivy gate in CI catches any regression), then add the app user
RUN (python -m pip uninstall -y pip setuptools wheel || true) \
    && useradd --system --uid 10001 --home-dir /app app \
    && mkdir -p /app/data && chown app /app/data  # the job runner's lock (data/ops/run.lock)
# Apply Debian security fixes released since the base image was built (the Trivy gate fails on
# fixable HIGH/CRITICAL findings, e.g. CVE-2026-103111 in libpcre2 before the base caught up).
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=build /app/.venv /app/.venv
COPY docker/entrypoint.sh /usr/local/bin/entrypoint
ENV PATH=/app/.venv/bin:$PATH PYTHONUNBUFFERED=1 APP_ENV=prod
USER app
EXPOSE 8080
ENTRYPOINT ["entrypoint"]
CMD ["api"]
