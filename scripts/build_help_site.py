"""Builds the minimal Ascend Energy Help page on top of a site created by the org's own API
(POST /connect/communities, template "Build Your Own (LWR)", then retrieved into scripts/site-baseline/help_new_site).
Chat: Messaging for Web deployment Ascend_Help_Web -> channel Ascend_Help_Messaging -> agent Ascend_Help_Agent.
It re-uses the org's existing hidden frame site ESW_SDO_Messaging_17946063748961 (a generic Messaging for Web frame).
Output in force-app/main/default: digitalExperiences, EmbeddedServiceConfig. Does not touch the org."""
import os, re, json, shutil
BASE = "force-app/main/default"; BUNDLE = "Ascend_Energy_Help1"
ORG15 = "00DgK00000gGyWH"; MYDOMAIN = "trailsignup-09768f8440f478"
SITE_HOST = f"https://{MYDOMAIN}.my.site.com"; SCRT = f"https://{MYDOMAIN}.my.salesforce-scrt.com"
FRAME_PREFIX, FRAME_SITE = "ESWAscendHelpWe1795005043003", "ESW_Ascend_Help_We_17950050430031"   # created by Setup > Embedded Service Deployments > New Deployment
DEPLOYMENT, CHANNEL = "Ascend_Help_Web", "Ascend_Help_Messaging"
BRAND = "#0b6e4f"
dst = f"{BASE}/digitalExperiences/site/{BUNDLE}"
if os.path.exists(dst): shutil.rmtree(dst)
shutil.copytree("scripts/site-baseline/help_new_site", dst)
def jload(p): return json.load(open(p))
def jsave(p, d): open(p, "w").write(json.dumps(d, indent=2))

CSS = f"""/* Ascend Energy Help: minimal styles */
html {{ background: #ffffff; }}
body {{ margin: 0; color: #1a1a1a; font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
.ae-page {{ max-width: 880px; margin: 0 auto; padding: 72px 24px 48px; text-align: left; }}
.ae-eyebrow {{ margin: 0 0 12px; font-size: 14px; letter-spacing: .08em; text-transform: uppercase; color: {BRAND}; font-weight: 600; }}
.ae-title {{ margin: 0 0 16px; font-size: 44px; line-height: 1.1; font-weight: 700; }}
.ae-lead {{ margin: 0 0 40px; max-width: 620px; font-size: 18px; line-height: 1.5; color: #444444; }}
.ae-cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 32px; }}
.ae-card {{ border: 1px solid #e3e3e3; border-radius: 8px; padding: 20px; }}
.ae-card h2 {{ margin: 0 0 8px; font-size: 18px; font-weight: 600; }}
.ae-card p {{ margin: 0; font-size: 15px; line-height: 1.5; color: #555555; }}
.ae-note {{ margin: 0 0 56px; padding-left: 14px; border-left: 3px solid {BRAND}; font-size: 15px; line-height: 1.5; color: #444444; }}
.ae-footer {{ font-size: 13px; color: #888888; }}
"""
# guest access: the page and the chat are public
sc = f"{dst}/sfdc_cms__site/{BUNDLE}/content.json"; d = jload(sc)
d["contentBody"]["authenticationType"] = "AUTHENTICATED_WITH_PUBLIC_ACCESS_ENABLED"; jsave(sc, d)

# chat bubble: bootstrap + init added to the template's own head
ap = f"{dst}/sfdc_cms__appPage/mainAppPage/content.json"; d = jload(ap)
head = d["contentBody"]["headMarkup"].replace("<title>Welcome to LWC Communities!</title>", "<title>Ascend Energy Help</title>")
head += "\n<style>\n" + CSS + "</style>\n"
head += ('<script type="text/javascript">\n'
         '// The chat script is added after the page has rendered. Loading it as a plain head script on this LWR site leaves no chat button.\n'
         'function initEmbeddedMessaging() {\n'
         '  if (window.__aeChatStarted) return; window.__aeChatStarted = true;\n'
         '  try {\n'
         "    embeddedservice_bootstrap.settings.language = 'en_US';\n"
         f"    embeddedservice_bootstrap.init('{ORG15}', '{DEPLOYMENT}', '{SITE_HOST}/{FRAME_PREFIX}', {{ scrt2URL: '{SCRT}' }});\n"
         '  } catch (err) { console.error("Error loading Embedded Messaging: ", err); }\n'
         '}\n'
         'function loadEmbeddedMessaging() {\n'
         '  var s = document.createElement("script");\n'
         f'  s.src = "{SITE_HOST}/{FRAME_PREFIX}/assets/js/bootstrap.min.js";\n'
         '  s.onload = initEmbeddedMessaging;\n'
         '  document.head.appendChild(s);\n'
         '}\n'
         'window.addEventListener("load", function () { setTimeout(loadEmbeddedMessaging, 1500); });\n'
         '</script>\n')
d["contentBody"].update({"headMarkup": head, "isLockerServiceEnabled": False, "isRelaxedCSPLevel": True})
jsave(ap, d)

HTML = """<main class="ae-page">
  <section class="ae-hero">
    <p class="ae-eyebrow">Ascend Energy</p>
    <h1 class="ae-title">How can we help?</h1>
    <p class="ae-lead">Check your latest bill, ask for more time to pay, or get power outage guidance. Open the chat at the bottom right and our assistant will help.</p>
  </section>
  <section class="ae-cards">
    <div class="ae-card"><h2>Latest bill</h2><p>See the amount, due date and status of your latest bill.</p></div>
    <div class="ae-card"><h2>Payment extension</h2><p>Move your due date 7 days later, once per bill.</p></div>
    <div class="ae-card"><h2>Outage help</h2><p>Safety steps for a power outage, including medical equipment.</p></div>
  </section>
  <p class="ae-note">Have your account number and the 10-digit registered phone number ready. If someone at home depends on medical equipment and the power is out, call the emergency services first.</p>
  <footer class="ae-footer">Ascend Energy</footer>
</main>"""
hv = f"{dst}/sfdc_cms__view/home/content.json"; d = jload(hv)
def set_html(n):
    if isinstance(n, dict):
        if n.get("definition") == "community_builder:htmlEditor": n["attributes"]["richTextValue"] = HTML
        for v in n.values(): set_html(v)
    elif isinstance(n, list):
        for v in n: set_html(v)
set_html(d); d["title"] = "Ascend Energy Help"; jsave(hv, d)


print("help site written (the chat deployment itself is created in Setup; see scripts/site-baseline/ascend_help_web.EmbeddedServiceConfig)")
