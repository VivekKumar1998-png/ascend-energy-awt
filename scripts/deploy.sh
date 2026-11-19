#!/bin/bash
# Deploys given paths to org alias Ascend and prints the real result via REST
# (the CLI's own local cache write is blocked in the Cursor sandbox, the server deploy still runs).
export SF_DISABLE_LOG_FILE=true SF_DISABLE_TELEMETRY=true
OUT=$(sf project deploy start -o Ascend --source-dir "$@" --json 2>&1)
ID=$(echo "$OUT" | grep -o '0Af[A-Za-z0-9]\{12,15\}' | head -1)
[ -z "$ID" ] && ID=$(sf data query -o Ascend --use-tooling-api -q "SELECT Id FROM DeployRequest ORDER BY StartDate DESC LIMIT 1" --json | python3 -c "import sys,json;print(json.load(sys.stdin)['result']['records'][0]['Id'])")
for i in $(seq 1 40); do
  R=$(sf api request rest "/services/data/v68.0/metadata/deployRequest/$ID?includeDetails=true" -o Ascend 2>/dev/null | sed -n '/^{/,$p')
  S=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['deployResult']['status'])" 2>/dev/null)
  case "$S" in Succeeded|SucceededPartial|Failed|Canceled) break;; esac
  sleep 3
done
echo "Deploy $ID: $S"
echo "$R" | python3 -c "
import sys,json
d=json.load(sys.stdin)['deployResult']
print('components:',d['numberComponentsDeployed'],'/',d['numberComponentsTotal'],'errors:',d['numberComponentErrors'])
det=d.get('details',{})
for c in det.get('componentFailures',[]) or []: print('FAIL',c['componentType'],c['fullName'],c.get('lineNumber'),'->',c['problem'])
for t in (det.get('runTestResult') or {}).get('failures',[]) or []: print('TESTFAIL',t['name'],t['methodName'],t['message'])
"
