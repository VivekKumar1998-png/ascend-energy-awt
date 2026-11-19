"""Hidden Messaging-for-Web frame site for the Help page chat (clone of the org's existing frame site, renamed).
Output in force-app/main/default: digitalExperiences/site/ESW_Ascend_Help_Web1, digitalExperienceConfigs, networks, EmbeddedServiceConfig. Does not touch the org."""
import os, re, json, shutil, random
BASE = "force-app/main/default"; BL = "scripts/site-baseline"
OLD_B, OLD_N, OLD_P = "ESW_SDO_Messaging_17946063748961", "ESW_SDO_Messaging__1794606374896", "esw-sdo-messaging-1794606374896"
ESW_PREFIX, ESW_NET, ESW_BUNDLE = "ESWAscendHelpWeb", "ESW_Ascend_Help_Web", "ESW_Ascend_Help_Web1"
DEPLOYMENT, CHANNEL = "Ascend_Help_Web", "Ascend_Help_Messaging"
rnd = random.Random(1118)
def key(): return "MC" + "".join(rnd.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ234567") for _ in range(26))
def w(p, t): os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w").write(t)
dst = f"{BASE}/digitalExperiences/site/{ESW_BUNDLE}"
if os.path.exists(dst): shutil.rmtree(dst)
shutil.copytree(f"{BL}/esw_frame_site", dst)
os.rename(f"{dst}/{OLD_B}.digitalExperience-meta.xml", f"{dst}/{ESW_BUNDLE}.digitalExperience-meta.xml")
os.rename(f"{dst}/sfdc_cms__site/{OLD_B}", f"{dst}/sfdc_cms__site/{ESW_BUNDLE}")
subs = [(OLD_B, ESW_BUNDLE), (OLD_N, ESW_NET), (OLD_P, "esw-ascend-help-web")]
for root, _, files in os.walk(dst):
    for f in files:
        p = os.path.join(root, f)
        s = open(p).read()
        if f == "_meta.json": s = re.sub(r'"contentKey" : "[A-Z0-9]+"', f'"contentKey" : "{key()}"', s)
        if f == "content.json" and "sfdc_cms__styles" in root:
            d = json.loads(s); d["contentBody"]["sfdc_cms:media"]["source"].pop("ref", None); s = json.dumps(d, indent=2)
        for a, b in subs: s = s.replace(a, b)
        open(p, "w").write(s)
x = f"{dst}/{ESW_BUNDLE}.digitalExperience-meta.xml"
t = open(x).read()
open(x, "w").write(re.sub(r"<label>.*?</label>", f"<label>{ESW_BUNDLE}</label>", t))
w(f"{BASE}/digitalExperienceConfigs/{ESW_BUNDLE}.digitalExperienceConfig-meta.xml", f"""<?xml version="1.0" encoding="UTF-8"?>
<DigitalExperienceConfig xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>{ESW_NET}</label>
    <site>
        <urlPathPrefix>{ESW_PREFIX}</urlPathPrefix>
    </site>
    <space>site/{ESW_BUNDLE}</space>
</DigitalExperienceConfig>
""")
n = open(f"{BL}/esw_frame.network").read()
n = re.sub(r"<emailSenderName>.*?</emailSenderName>", f"<emailSenderName>{ESW_NET}</emailSenderName>", n)
n = re.sub(r"<picassoSite>.*?</picassoSite>", f"<picassoSite>{ESW_BUNDLE}</picassoSite>", n)
n = re.sub(r"<site>.*?</site>", f"<site>{ESW_NET}</site>", n)
n = re.sub(r"<urlPathPrefix>.*?</urlPathPrefix>", f"<urlPathPrefix>{ESW_PREFIX}vforcesite</urlPathPrefix>", n)
n = re.sub(r"<description>.*?</description>", f"<description>Site for Messaging deployment: {DEPLOYMENT}.</description>", n)
w(f"{BASE}/networks/{ESW_NET}.network-meta.xml", n)
s = open(f"{BL}/esc_web.EmbeddedServiceConfig").read()
s = re.sub(r"<messagingChannel>.*?</messagingChannel>", f"<messagingChannel>{CHANNEL}</messagingChannel>", s)
s = re.sub(r"<masterLabel>.*?</masterLabel>", "<masterLabel>Ascend Help Web</masterLabel>", s)
s = re.sub(r"<site>.*?</site>", f"<site>{ESW_NET}</site>", s)
w(f"{BASE}/EmbeddedServiceConfig/{DEPLOYMENT}.EmbeddedServiceConfig-meta.xml", s)
print("frame site written")
