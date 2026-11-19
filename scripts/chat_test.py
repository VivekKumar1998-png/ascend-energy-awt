"""Talks to the live Help chat the same way the web widget does (Messaging for Web, unauthenticated guest).
Usage: python3 scripts/chat_test.py "message 1" "message 2" ...   (all messages go into ONE conversation, replies are printed)"""
import sys, json, uuid, time, threading, urllib.request
ORG = "00DgK00000gGyWH"; ES = "Ascend_Help_Web"
SCRT = "https://trailsignup-09768f8440f478.my.salesforce-scrt.com"
def call(method, path, body=None, token=None, extra=None):
    h = {"Content-Type": "application/json"}
    if token: h["Authorization"] = "Bearer " + token
    if extra: h.update(extra)
    r = urllib.request.Request(SCRT + path, data=json.dumps(body).encode() if body is not None else None, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=60) as x:
            t = x.read().decode(); return json.loads(t) if t else {}
    except urllib.error.HTTPError as e:
        sys.exit(f"{method} {path} -> HTTP {e.code}: {e.read().decode()[:400]}")
tok = call("POST", "/iamessage/v1/authorization/unauthenticated/accessToken",
           {"orgId": ORG, "developerName": ES, "capabilitiesVersion": "1", "deploymentType": "Web"})
token = tok["accessToken"]; conv = str(uuid.uuid4())
replies = []; stop = False
def listen():
    r = urllib.request.Request(SCRT + "/eventrouter/v1/sse", headers={"Authorization": "Bearer " + token, "X-Org-Id": ORG, "Accept": "text/event-stream"})
    ev = None
    with urllib.request.urlopen(r, timeout=300) as x:
        for raw in x:
            line = raw.decode().strip()
            if line.startswith("event:"): ev = line[6:].strip()
            elif line.startswith("data:") and ev == "CONVERSATION_MESSAGE":
                try:
                    d = json.loads(line[5:]); e = json.loads(d["conversationEntry"]["entryPayload"]) if isinstance(d["conversationEntry"]["entryPayload"], str) else d["conversationEntry"]["entryPayload"]
                    who = d["conversationEntry"]["sender"]["role"]
                    txt = (e.get("abstractMessage", {}).get("staticContent", {}) or {}).get("text")
                    if who != "EndUser" and txt: replies.append(txt)
                except Exception as ex: pass
            if stop: break
threading.Thread(target=listen, daemon=True).start(); time.sleep(2)
cfg = json.loads(urllib.request.urlopen(SCRT + f"/embeddedservice/v1/embedded-service-config?orgId={ORG}&esConfigName={ES}&language=en_US").read())
addr = cfg["embeddedServiceConfig"]["embeddedServiceMessagingChannel"]["channelAddressIdentifier"]
call("POST", "/iamessage/v1/conversation", {"conversationId": conv, "channelAddressIdentifier": addr, "language": "en_US", "routingAttributes": {}}, token)
first = True
for m in sys.argv[1:]:
    n = len(replies)
    call("POST", f"/iamessage/v1/conversation/{conv}/message",
         {"message": {"id": str(uuid.uuid4()), "messageType": "StaticContentMessage", "staticContent": {"formatType": "Text", "text": m}},
          "isNewMessagingSession": first, "routingAttributes": {}, "language": "en_US"}, token)
    first = False
    print("YOU  :", m)
    t0 = time.time(); last = n
    while time.time() - t0 < 60:
        time.sleep(2)
        if len(replies) > last: last = len(replies); t0 = time.time() - 40   # allow a few more seconds for follow-up parts
        if len(replies) > n and time.time() - t0 > 18: break
    for r in replies[n:]: print("AGENT:", r)
stop = True
