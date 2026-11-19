"""Builds a customer-facing copy of the agent (Agentforce Service Agent, ExternalCopilot) from the
already built internal planner bundle. Same topics, actions, rules. Output: bots/ + genAiPlannerBundles/ under force-app."""
import os, shutil, re
NEW = "Ascend_Help_Agent"; OLD = "Ascend_Energy_Assistant"
D = "force-app/main/default"
SRC = f"{D}/genAiPlannerBundles/{OLD}"; DST = f"{D}/genAiPlannerBundles/{NEW}"
BOT_USER = os.environ.get("BOT_USER", "ascend_energy_assistant@00dgk00000ggywh1725955292.ext")
if os.path.exists(DST): shutil.rmtree(DST)
shutil.copytree(SRC, DST)
os.rename(f"{DST}/{OLD}.genAiPlannerBundle", f"{DST}/{NEW}.genAiPlannerBundle")
# local topic/action names carry an id suffix that must be unique in the org: give the copy its own suffixes
def uniq(t): return re.sub(r"_179gK000002gT9(\w)", r"_179gK000002gX9\1", t.replace("_16jgK000002R7kD", "_16jgK000002R9xZ"))
for root, dirs, files in os.walk(DST, topdown=False):
    for f in files:
        q = os.path.join(root, f)
        if f.endswith((".json", ".genAiPlannerBundle", ".xml")):
            t = open(q).read(); u = uniq(t)
            if t != u: open(q, "w").write(u)
    for d in dirs + files:
        if uniq(d) != d: os.rename(os.path.join(root, d), os.path.join(root, uniq(d)))
p = f"{DST}/{NEW}.genAiPlannerBundle"
s = open(p).read().replace("<masterLabel>Ascend Energy Assistant</masterLabel>", "<masterLabel>Ascend Help Agent</masterLabel>")
open(p, "w").write(s)

# ---- human transfer: escalation topic can escalate, and the Messaging surfaces carry the outbound Omni-Channel flow
FLOW = "Ascend_Human_Escalation"
ESC_MSG = "One moment, I'm transferring you to a team member."
s = open(p).read()
s = re.sub(r"(<fullName>Ascend_Escalation_\w+</fullName>\s*<canEscalate>)false(</canEscalate>)", r"\1true\2", s)
surf = "".join(f"""    <plannerSurfaces>
        <adaptiveResponseAllowed>false</adaptiveResponseAllowed>
        <callRecordingAllowed>false</callRecordingAllowed>
        <outboundRouteConfigs>
            <escalationMessage>{ESC_MSG}</escalationMessage>
            <outboundRouteName>{FLOW}</outboundRouteName>
            <outboundRouteType>OmniChannelFlow</outboundRouteType>
        </outboundRouteConfigs>
        <surface>SurfaceAction__{t}</surface>
        <surfaceType>{t}</surfaceType>
    </plannerSurfaces>
""" for t in ("Messaging", "CustomerWebClient"))
if "<plannerSurfaces>" not in s:
    s = s.replace("    <plannerType>", surf + "    <plannerType>", 1)
open(p, "w").write(s)
SRC_BOT = f"{D}/bots/{OLD}"
os.makedirs(f"{D}/bots/{NEW}", exist_ok=True)
b = open(f"{SRC_BOT}/{OLD}.bot-meta.xml").read()
b = b.replace("<agentTemplate>service_planner_agent__ServicePlanner</agentTemplate>", "<agentTemplate>service_agent__EinsteinServiceAgent</agentTemplate>")
b = b.replace("<agentType>ServicePlanner</agentType>", "<agentType>EinsteinServiceAgent</agentType>")
b = b.replace("<type>InternalCopilot</type>", "<type>ExternalCopilot</type>")
b = b.replace(f"<name>{OLD}</name>", f"<name>{NEW}</name>").replace("<label>Ascend Energy Assistant</label>", "<label>Ascend Help Agent</label>")
b = re.sub(r"<botUser>.*?</botUser>", f"<botUser>{BOT_USER}</botUser>", b)
open(f"{D}/bots/{NEW}/{NEW}.bot-meta.xml", "w").write(b)
v = open(f"{SRC_BOT}/v1.botVersion-meta.xml").read()
v = v.replace(f"<genAiPlannerName>{OLD}</genAiPlannerName>", f"<genAiPlannerName>{NEW}</genAiPlannerName>")
v = re.sub(r"(<developerName>VerifiedCustomerId</developerName>\s*)<includeInPrompt>false</includeInPrompt>", r"\1<includeInPrompt>true</includeInPrompt>", v)
v = v.replace("Hi, I&apos;m the Ascend Energy assistant. I can help with your latest bill, a payment extension, billing questions and power outage guidance. How can I help?", "How can I help you today?")
v = v.replace("<defaultStdObjForContactIdFltrEnabled>true</", "<defaultStdObjForContactIdFltrEnabled>false</")
open(f"{D}/bots/{NEW}/v1.botVersion-meta.xml", "w").write(v)
print("built", NEW, "botUser", BOT_USER)
