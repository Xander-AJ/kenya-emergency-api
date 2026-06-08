#!/usr/bin/env bash
#
# HTTP API smoke tour — happy paths and error paths against a running server.
#
# Start the server first (it serves the test fixtures until v1.0 data lands):
#
#     python examples/02_running_the_api.py
#
# then, in another terminal:
#
#     bash examples/03_curl_examples.sh
#
# Each call prints the HTTP status code so you can see 200s, a 404, and a 400.
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"

# Pretty-print JSON if `jq` is available; otherwise pass through untouched.
fmt() { if command -v jq >/dev/null 2>&1; then jq .; else cat; fi; }

call() {
  # call <GET path> — one request; prints the formatted body then the status.
  local resp body http
  resp="$(curl -s -w $'\n%{http_code}' "${BASE_URL}$1")"
  http="${resp##*$'\n'}"   # last line: status code
  body="${resp%$'\n'*}"    # everything before it: the response body
  printf '%s\n' "$body" | fmt
  printf -- '-> HTTP %s\n\n' "$http"
}

echo "### 1. Liveness probe — should be 200 with status ok"
call "/health"

echo "### 2. List all counties — happy path, 200"
call "/v1/counties"

echo "### 3. Look up one county by code (normalized 47 -> 047) — 200"
call "/v1/counties/047"

echo "### 4. County contacts filtered by category=fire — 200"
call "/v1/counties/047/contacts?category=fire"

echo "### 5. One-call overview for Nairobi — 200 composite"
call "/v1/emergency/overview/Nairobi"

echo "### 6. National emergency numbers — 200"
call "/v1/emergency/national"

echo "### 7. ERROR PATH: well-formed but absent county code 046 — expect 404 not_found"
call "/v1/counties/046"

echo "### 8. ERROR PATH: malformed county code 'abc' — expect 400 bad_request"
call "/v1/counties/abc"
