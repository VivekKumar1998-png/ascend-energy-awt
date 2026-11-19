#!/bin/bash
# CHECK-ONLY deploy (dry run) to org alias Ascend. Nothing is saved in the org.
# Usage: scripts/validate.sh <path> [<path> ...]      (paths are passed as --source-dir)
# Reads the real result over REST because the CLI cannot write its cache in the Cursor sandbox.
export SF_DISABLE_LOG_FILE=true SF_DISABLE_TELEMETRY=true
ARGS=(); for p in "$@"; do ARGS+=(--source-dir "$p"); done
OUT=$(sf project deploy start --dry-run -o Ascend "${ARGS[@]}" --json 2>&1)
ID=$(echo "$OUT" | grep -o '0Af[A-Za-z0-9]\{12,15\}' | head -1)
[ -z "$ID" ] && { echo "$OUT" | head -c 1500; exit 1; }
for i in $(seq 1 60); do
  R=$(sf api request rest "/services/data/v68.0/metadata/deployRequest/$ID?includeDetails=true" -o Ascend 2>/dev/null | sed -n '/^{/,$p')
  S=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['deployResult']['status'])" 2>/dev/null)
  case "$S" in Succeeded|SucceededPartial|Failed|Canceled) break;; esac
  sleep 3
done
echo "CHECK-ONLY $ID: $S"
echo "$R" | python3 -c "
import sys,json
d=json.load(sys.stdin)['deployResult']
print('components:',d['numberComponentsDeployed'],'/',d['numberComponentsTotal'],'errors:',d['numberComponentErrors'])
det=d.get('details',{})
for c in det.get('componentFailures',[]) or []: print('FAIL',c['componentType'],c['fullName'],c.get('lineNumber'),'->',c['problem'])
"
