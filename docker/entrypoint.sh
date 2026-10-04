#!/bin/sh
# api            -> the web API on $PORT (Cloud Run sets it; 8080 otherwise)
# job <name> ... -> one pipeline job through the job runner
set -eu
case "${1:-api}" in
  api) exec fantasy-api --host 0.0.0.0 --port "${PORT:-8080}" ;;
  job) shift; exec fantasy run "$@" ;;
  *) exec "$@" ;;
esac
