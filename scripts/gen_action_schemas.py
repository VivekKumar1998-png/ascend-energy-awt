"""Writes input/output schema.json for the 5 Flow actions (genAiFunctions/<name>/input|output/schema.json).
The wording and fields live in scripts/agent_content.py."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from agent_content import SPEC, schema
BASE = "force-app/main/default/genAiFunctions"
for dev, (ins, outs) in SPEC.items():
    for kind, props in (("input", ins), ("output", outs)):
        path = f"{BASE}/{dev}/{kind}/schema.json"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        json.dump(schema(props, "in" if kind == "input" else "out"), open(path, "w"), indent=2)
print("schemas written for", len(SPEC), "actions")
