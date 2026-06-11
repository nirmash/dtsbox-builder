#!/usr/bin/env bash
# check-emulator.sh — Detect whether the DTS local emulator (Docker) is installed and running.
#
# The DTS emulator is a Docker image: mcr.microsoft.com/dts/dts-emulator:latest
# It is NOT a pip package — there is no native binary distribution.
#
# Used by the dtsbox-builder skill before Step 9 (local test). Exit codes:
#   0  — emulator container is running and reachable on http://localhost:8080
#   1  — Docker is installed but no emulator container is running
#   2  — Docker is not installed or not running
#
# This script does NOT start or install anything. It only reports state.

set -u

ENDPOINT="${DTS_EMULATOR_ENDPOINT:-http://localhost:8080}"
EMULATOR_IMAGE="mcr.microsoft.com/dts/dts-emulator:latest"

# Check 1 — emulator reachable on the expected port?
# DTS speaks gRPC, so a plain HTTP GET returns 400/404/405 — any of those means "port open, gRPC server listening".
if command -v curl >/dev/null 2>&1; then
    if curl --silent --max-time 2 --output /dev/null --write-out "%{http_code}" "${ENDPOINT}" \
        | grep -qE '^(200|400|404|405)$'; then
        echo "ok: DTS emulator is reachable at ${ENDPOINT}"
        exit 0
    fi
fi

# Check 2 — is Docker available?
if ! command -v docker >/dev/null 2>&1; then
    cat <<'EOF' >&2
not-installed: Docker is required to run the DTS emulator.

Install Docker Desktop (macOS/Windows) or Docker Engine (Linux):
  https://docs.docker.com/get-docker/

Then start the emulator with:
  docker run -d --name dtsbox-emulator -p 8080:8080 mcr.microsoft.com/dts/dts-emulator:latest

And re-run this check.
EOF
    exit 2
fi

if ! docker info >/dev/null 2>&1; then
    cat <<'EOF' >&2
not-installed: Docker is installed but the daemon is not running.

Start Docker Desktop (macOS/Windows) or run `sudo systemctl start docker` (Linux),
then start the emulator with:
  docker run -d --name dtsbox-emulator -p 8080:8080 mcr.microsoft.com/dts/dts-emulator:latest

And re-run this check.
EOF
    exit 2
fi

# Check 3 — Docker is available but no container is responding. Tell the user how to start one.
cat <<EOF >&2
not-running: Docker is installed but no DTS emulator is reachable at ${ENDPOINT}.

Start the emulator container (it will pull the image on first run, ~30-45s):
  docker run -d --name dtsbox-emulator -p 8080:8080 ${EMULATOR_IMAGE}

If a previous container is stuck, remove it first:
  docker rm -f dtsbox-emulator

Then re-run this check.
EOF
exit 1
