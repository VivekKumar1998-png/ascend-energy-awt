"""Builds the LIVE agent's planner bundle (force-app/.../genAiPlannerBundles/Ascend_Energy_Assistant) from the
retrieved live baseline (scripts/live-baseline, retrieved from the org on 18 Nov 2026 so the builder edits are kept).

What it changes on top of the baseline:
  1. Topic descriptions, scopes and instructions, and action descriptions: wording from scripts/agent_content.py
  2. Local action input/output schemas: from scripts/agent_content.py (adds claimsToBeSomeoneElse and blocked,
     and marks contactId inputs as filled by the system, not by the customer)
  3. attributeMappings: Verify Customer output contactId is stored in the VerifiedCustomerId variable, and the
     contactId input of Get Latest Bill, Grant Payment Extension and Create Escalation Case is read from it
  4. ruleExpressions: Verify Customer is only offered while VerifiedCustomerId is empty (so it never runs twice),
     Get Latest Bill and Grant Payment Extension are only offered once VerifiedCustomerId is set

Run: python3 scripts/build_planner_bundle.py   (does not touch the org)"""
import os, re, json, shutil, html, sys
sys.path.insert(0, os.path.dirname(__file__))
from agent_content import ACTIONS, TOPICS, SPEC, schema

BASELINE = "scripts/live-baseline/genAiPlannerBundles/Ascend_Energy_Assistant"
OUT = "force-app/main/default/genAiPlannerBundles/Ascend_Energy_Assistant"
VAR = "VerifiedCustomerId"

def esc(s): return html.escape(s, quote=True).replace("&#x27;", "&apos;")

if os.path.exists(OUT): shutil.rmtree(OUT)
shutil.copytree(BASELINE, os.path.dirname(OUT) + "/Ascend_Energy_Assistant")
bundle_path = f"{OUT}/Ascend_Energy_Assistant.genAiPlannerBundle"
xml = open(bundle_path).read()

def instr_xml(items):
    out = ""
    for i, text in enumerate(items, 1):
        out += (f"        <genAiPluginInstructions>\n            <description>{esc(text)}</description>\n"
                f"            <developerName>instruction_{i}</developerName>\n            <language xsi:nil=\"true\"/>\n"
                f"            <masterLabel>instruction_{i}</masterLabel>\n            <sortOrder>{i}</sortOrder>\n        </genAiPluginInstructions>\n")
    return out

topic_full = {}      # localDeveloperName -> fullName (with id suffix)
action_full = {}     # (topic localDeveloperName, action localDeveloperName) -> fullName

def patch_topic(m):
    blk = m.group(0)
    key = re.search(r"<localDeveloperName>(\w+)</localDeveloperName>\s*<masterLabel>", blk[blk.rindex("</localActions>") if "</localActions>" in blk else 0:]).group(1)
    t = TOPICS[key]
    topic_full[key] = re.search(r"<fullName>(\w+)</fullName>", blk).group(1)
    # topic description: first <description> in the block
    blk = re.sub(r"<description>.*?</description>", lambda _: f"<description>{esc(t['desc'])}</description>", blk, count=1, flags=re.S)
    # instructions: replace the whole run of genAiPluginInstructions
    blk = re.sub(r"(?:        <genAiPluginInstructions>.*?</genAiPluginInstructions>\n)+", lambda _: instr_xml(t["instructions"]), blk, count=1, flags=re.S)
    # scope
    blk = re.sub(r"<scope>.*?</scope>", lambda _: f"<scope>{esc(t['scope'])}</scope>", blk, count=1, flags=re.S)
    # local actions: description + remember names
    def patch_action(am):
        ab = am.group(0)
        ld = re.search(r"<localDeveloperName>(\w+)</localDeveloperName>", ab).group(1)
        action_full[(key, ld)] = re.search(r"<fullName>(\w+)</fullName>", ab).group(1)
        return re.sub(r"<description>.*?</description>", lambda _: f"<description>{esc(ACTIONS[ld][2])}</description>", ab, count=1, flags=re.S)
    blk = re.sub(r"<localActions>.*?</localActions>", patch_action, blk, flags=re.S)
    return blk
xml = re.sub(r"<localTopics>.*?</localTopics>", patch_topic, xml, flags=re.S)

# ---- 1b. Verification lives ONLY in the Verification topic. Bill Status and Payment Extension have no Verify Customer action:
# they read the stored VerifiedCustomerId (their actions are only offered once it is set, see the rules below).
def drop_verify_from_bill_status(x):
    topics = re.findall(r"<localTopics>.*?</localTopics>", x, flags=re.S)
    bill = next(t for t in topics if "<localDeveloperName>Ascend_Bill_Status</localDeveloperName>" in t)
    suffix = re.search(r"Ascend_Verify_Customer_(179g\w+)</fullName>", bill).group(1)
    new = re.sub(r"        <localActionLinks>\s*<functionName>Ascend_Verify_Customer_\w+</functionName>\s*</localActionLinks>\n", "", bill)
    new = re.sub(r"        <localActions>\s*<fullName>Ascend_Verify_Customer_\w+</fullName>.*?</localActions>\n", "", new, flags=re.S)
    return x.replace(bill, new), suffix
xml, _bs = drop_verify_from_bill_status(xml)
for d in os.listdir(f"{OUT}/localActions"):
    if d.startswith("Ascend_Bill_Status_"):
        shutil.rmtree(os.path.join(OUT, "localActions", d, f"Ascend_Verify_Customer_{_bs}"))

# ---- 2. schemas of the local actions
n = 0
for root, _, files in os.walk(f"{OUT}/localActions"):
    if "schema.json" in files:
        parts = root.split(os.sep)
        kind, action_dir = parts[-1], parts[-2]
        base = action_dir.rsplit("_", 1)[0]
        ins, outs = SPEC[base]
        s = schema(ins if kind == "input" else outs, "in" if kind == "input" else "out")
        json.dump(s, open(f"{root}/schema.json", "w"), indent=2); n += 1

# ---- 3. attribute mappings and 4. rules
NAME_STYLE = os.environ.get("NAME_STYLE", "local")   # local = localDeveloperName (accepted by the org, verified with a check-only deploy); full = fullName with id suffix (rejected: AttributeSource missing)
def a(topic, action):
    if NAME_STYLE == "local": return f"{topic}.{action}"
    if NAME_STYLE == "mixed": return f"{topic_full[topic]}.{action}"
    return f"{topic_full[topic]}.{action_full[(topic, action)]}"
maps = [
 ("Ascend_Verification", "Ascend_Verify_Customer", "output_contactId"),
 ("Ascend_Verification", "Ascend_Verify_Customer", "input_endUserId", "EndUserId"),
 ("Ascend_Bill_Status", "Ascend_Get_Latest_Bill", "input_contactId"),
 ("Ascend_Payment_Extension", "Ascend_Get_Latest_Bill", "input_contactId"),
 ("Ascend_Payment_Extension", "Ascend_Grant_Payment_Extension", "input_contactId"),
 ("Ascend_Escalation", "Ascend_Create_Escalation_Case", "input_contactId"),
 ("Ascend_Outage_Priority", "Ascend_Create_Escalation_Case", "input_contactId"),
]
mx = "".join(f"""    <attributeMappings>
        <attributeName>{a(m[0], m[1])}.{m[2]}</attributeName>
        <attributeType>CustomPluginFunctionAttribute</attributeType>
        <mappingTargetName>{m[3] if len(m) > 3 else VAR}</mappingTargetName>
        <mappingType>Variable</mappingType>
    </attributeMappings>
""" for m in maps)
xml = re.sub(r"(<GenAiPlannerBundle [^>]*>\n)", lambda m: m.group(1) + mx, xml, count=1)

not_verified = [("Ascend_Verification", "Ascend_Verify_Customer")]
# Bill and extension actions are only offered once VerifiedCustomerId is set (rules are evaluated when a turn starts, so the
# customer verifies in one turn and the account actions appear from the next turn on).
verified = [("Ascend_Bill_Status", "Ascend_Get_Latest_Bill"), ("Ascend_Payment_Extension", "Ascend_Get_Latest_Bill"),
            ("Ascend_Payment_Extension", "Ascend_Grant_Payment_Extension")]
rules = f"""    <ruleExpressionAssignments>
""".rstrip("\n")
rx = ""
for name, targets in (("Customer_Not_Verified_Yet", not_verified), ("Customer_Is_Verified", verified)):
    for t, ac in targets:
        rx += f"""    <ruleExpressionAssignments>
        <ruleExpressionName>{name}</ruleExpressionName>
        <targetName>{a(t, ac)}</targetName>
        <targetType>PluginFunction</targetType>
    </ruleExpressionAssignments>
"""
for name, label, op in (("Customer_Not_Verified_Yet", "Customer not verified yet", "isEmpty"), ("Customer_Is_Verified", "Customer is verified", "isNotEmpty")):
    rx += f"""    <ruleExpressions>
        <conditions>
            <leftOperand>{VAR}</leftOperand>
            <leftOperandType>Variable</leftOperandType>
            <operator>{op}</operator>
        </conditions>
        <expressionLabel>{label}</expressionLabel>
        <expressionName>{name}</expressionName>
        <expressionType>sel</expressionType>
    </ruleExpressions>
"""
xml = xml.replace("    <plannerType>AiCopilot__ReAct</plannerType>\n", "    <plannerType>AiCopilot__ReAct</plannerType>\n" + rx)
open(bundle_path, "w").write(xml)
print("topics:", len(topic_full), "actions:", len(action_full), "schemas:", n, "mappings:", len(maps))
