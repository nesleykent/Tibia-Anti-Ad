#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")/../.."
mode="${1:-run}"
case "$mode" in
  run|--debug|--logs|--telemetry|--verify) ;;
  *) echo "Usage: $0 [run|--debug|--logs|--telemetry|--verify]" >&2; exit 2 ;;
esac
pkill -x 'Tibia Anti-Ad' >/dev/null 2>&1 || true
python3 tools/build_safari_extension.py --sign-identity "${TIBIA_SAFARI_SIGN_IDENTITY:--}"
app="$PWD/dist/Tibia Anti-Ad.app"
case "$mode" in
  --debug) lldb -- "$app/Contents/MacOS/Tibia Anti-Ad" ;;
  --logs|--telemetry)
    /usr/bin/open -n "$app"
    /usr/bin/log stream --info --style compact --predicate 'process == "Tibia Anti-Ad"'
    ;;
  --verify)
    /usr/bin/open -n "$app"
    sleep 1
    pgrep -x 'Tibia Anti-Ad' >/dev/null
    ;;
  run) /usr/bin/open -n "$app" ;;
esac
