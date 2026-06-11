#!/usr/bin/env bash
# check-emulator.sh — Detect whether the DTS local emulator is installed and running.
#
# Used by the dtsbox-builder skill before Step 9 (local test). Exit codes:
#   0  — emulator is running and reachable on http://localhost:8080
#   1  — emulator binary is installed but not running
#   2  — emulator is not installed (pip package missing)
#
# This script does not install or start anything. It only reports state.

set -u

ENDPOINT="${DTS_EMULATOR_ENDPOINT:-http://localhost:8080}"

# Check 1 — is the emulator reachable?
if command -v curl >/dev/null 2>&1; then
    if curl --silent --max-time 2 --output /dev/null --write-out "%{http_code}" "${ENDPOINT}" \
        | grep -qE '^(200|400|404|405)$'; then
        echo "ok: DTS emulator is reachable at ${ENDPOINT}"
        exit 0
    fi
fi

# Check 2 — is the emulator package installed via pip?
EMULATOR_PKG_CANDIDATES=(
    "durabletask-emulator"
    "durable-task-emulator"
    "dts-emulator"
)
INSTALLED=""
for pkg in "${EMULATOR_PKG_CANDIDATES[@]}"; do
    if python3 -m pip show "${pkg}" >/dev/null 2>&1; then
        INSTALLED="${pkg}"
        break
    fi
done

if [[ -n "${INSTALLED}" ]]; then
    cat <<EOF >&2
not-running: DTS emulator package '${INSTALLED}' is installed but no emulator is reachable at ${ENDPOINT}.

Start the emulator in a separate terminal (typical commands):
  ${INSTALLED}
  # or
  python3 -m ${INSTALLED//-/_}

Then re-run this check.
EOF
    exit 1
fi

cat <<'EOF' >&2
not-installed: DTS emulator is not installed.

Install via pip:
  pip install durabletask-emulator

(If that package name fails, ask the user which emulator distribution they use — the dtsbox docs
will eventually pin the exact package name. The skill should not auto-install.)

Then start it in a separate terminal and re-run this check.
EOF
exit 2
