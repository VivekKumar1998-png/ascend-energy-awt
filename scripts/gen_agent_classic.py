"""Generates the GLOBAL classic-builder assets (actions = GenAiFunction, topics = GenAiPlugin) for Ascend_Energy_Assistant.
Wording lives in scripts/agent_content.py.
NOTE: the live agent uses its own LOCAL copies of these topics and actions inside the planner bundle.
To change the live agent use scripts/build_planner_bundle.py, not this script.
Run: python3 scripts/gen_agent_classic.py"""
import os, html, sys
sys.path.insert(0, os.path.dirname(__file__))
from agent_content import ACTIONS, TOPICS
BASE = "force-app/main/default"
def esc(s): return html.escape(s, quote=False)
def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True); open(path, "w").write(text)

for dev, (label, flow, desc) in ACTIONS.items():
    write(f"{BASE}/genAiFunctions/{dev}/{dev}.genAiFunction-meta.xml", f'''<?xml version="1.0" encoding="UTF-8"?>
<GenAiFunction xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>{esc(desc)}</description>
    <invocationTarget>{flow}</invocationTarget>
    <invocationTargetType>flow</invocationTargetType>
    <isConfirmationRequired>false</isConfirmationRequired>
    <masterLabel>{esc(label)}</masterLabel>
</GenAiFunction>
''')
print("actions:", len(ACTIONS))

for dev, t in TOPICS.items():
    funcs = "".join(f"    <genAiFunctions><functionName>{a}</functionName></genAiFunctions>\n" for a in t["actions"])
    instr = "".join(f"""    <genAiPluginInstructions>
        <description>{esc(text)}</description>
        <developerName>instruction_{i}</developerName>
        <language>en_US</language>
        <masterLabel>instruction_{i}</masterLabel>
    </genAiPluginInstructions>
""" for i, text in enumerate(t["instructions"], 1))
    write(f"{BASE}/genAiPlugins/{dev}.genAiPlugin-meta.xml", f'''<?xml version="1.0" encoding="UTF-8"?>
<GenAiPlugin xmlns="http://soap.sforce.com/2006/04/metadata">
    <canEscalate>false</canEscalate>
    <description>{esc(t["desc"])}</description>
    <developerName>{dev}</developerName>
{funcs}{instr}    <language>en_US</language>
    <masterLabel>{esc(t["label"])}</masterLabel>
    <pluginType>Topic</pluginType>
    <scope>{esc(t["scope"])}</scope>
</GenAiPlugin>
''')
print("topics:", len(TOPICS))
