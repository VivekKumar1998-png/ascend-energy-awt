"""Generates the four Ascend V8 Flows as Flow metadata XML. Run: python3 scripts/gen_flows.py"""
import os
OUT = "force-app/main/default/flows"
HDR = '<?xml version="1.0" encoding="UTF-8"?>\n<Flow xmlns="http://soap.sforce.com/2006/04/metadata">\n'
y = [0]
def loc():
    y[0] += 150
    return f"<locationX>176</locationX><locationY>{y[0]}</locationY>"
def val(v):
    if isinstance(v, bool): return f"<booleanValue>{str(v).lower()}</booleanValue>"
    if isinstance(v, (int, float)): return f"<numberValue>{float(v)}</numberValue>"
    if isinstance(v, str) and v.startswith("@"): return f"<elementReference>{v[1:]}</elementReference>"
    return f"<stringValue>{v}</stringValue>"
def var(name, dtype, inp=False, out=False, desc="", scale=None):
    s = f"<variables><name>{name}</name><dataType>{dtype}</dataType><isCollection>false</isCollection>"
    s += f"<isInput>{str(inp).lower()}</isInput><isOutput>{str(out).lower()}</isOutput>"
    if scale is not None: s += f"<scale>{scale}</scale>"
    if desc: s += f"<description>{desc}</description>"
    return s + "</variables>\n"
def formula(name, dtype, expr, scale=None):
    s = f"<formulas><name>{name}</name><dataType>{dtype}</dataType>"
    if scale is not None: s += f"<scale>{scale}</scale>"
    expr = expr.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return s + f"<expression>{expr}</expression></formulas>\n"
def const(name, num):
    return f"<constants><name>{name}</name><dataType>Number</dataType><value><numberValue>{float(num)}</numberValue></value></constants>\n"
def assign(name, items, nxt=None):
    s = f"<assignments><name>{name}</name><label>{name.replace('_',' ')}</label>{loc()}"
    for ref, v in items:
        s += f"<assignmentItems><assignToReference>{ref}</assignToReference><operator>Assign</operator><value>{val(v)}</value></assignmentItems>"
    if nxt: s += f"<connector><targetReference>{nxt}</targetReference></connector>"
    return s + "</assignments>\n"
def cond(left, op, right):
    return f"<conditions><leftValueReference>{left}</leftValueReference><operator>{op}</operator><rightValue>{val(right)}</rightValue></conditions>"
def decision(name, rules, default):
    """rules: list of (rulename, [conds], target)"""
    s = f"<decisions><name>{name}</name><label>{name.replace('_',' ')}</label>{loc()}"
    s += f"<defaultConnector><targetReference>{default}</targetReference></defaultConnector><defaultConnectorLabel>Other</defaultConnectorLabel>"
    for rn, cs, tgt in rules:
        s += f"<rules><name>{rn}</name><conditionLogic>and</conditionLogic>{''.join(cs)}<connector><targetReference>{tgt}</targetReference></connector><label>{rn.replace('_',' ')}</label></rules>"
    return s + "</decisions>\n"
def lookup(name, obj, filters, nxt, fault=None, sort=None):
    s = f"<recordLookups><name>{name}</name><label>{name.replace('_',' ')}</label>{loc()}"
    s += f"<assignNullValuesIfNoRecordsFound>false</assignNullValuesIfNoRecordsFound><connector><targetReference>{nxt}</targetReference></connector>"
    if fault: s += f"<faultConnector><targetReference>{fault}</targetReference></faultConnector>"
    s += "<filterLogic>and</filterLogic>"
    for f, op, v in filters:
        s += f"<filters><field>{f}</field><operator>{op}</operator><value>{val(v)}</value></filters>"
    s += f"<getFirstRecordOnly>true</getFirstRecordOnly><object>{obj}</object><storeOutputAutomatically>true</storeOutputAutomatically>"
    if sort: s += f"<sortField>{sort[0]}</sortField><sortOrder>{sort[1]}</sortOrder>"
    return s + "</recordLookups>\n"
ORDER = ["apiVersion","assignments","constants","decisions","description","environments","formulas","interviewLabel","label",
         "processMetadataValues","processType","recordCreates","recordLookups","recordUpdates","runInMode","start","status","variables"]
def regroup(xml_body):
    """Salesforce needs elements of the same type grouped together, in schema order."""
    import xml.etree.ElementTree as ET
    root = ET.fromstring("<r>" + xml_body + "</r>")
    kids = sorted(list(root), key=lambda e: ORDER.index(e.tag))
    return "\n".join(ET.tostring(k, encoding="unicode") for k in kids)
def flow(name, label, desc, body, start):
    full = (f"<apiVersion>68.0</apiVersion><description>{desc}</description><environments>Default</environments>"
            f"<interviewLabel>{label} {{!$Flow.CurrentDateTime}}</interviewLabel><label>{label}</label>"
            f"<processMetadataValues><name>BuilderType</name><value><stringValue>LightningFlowBuilder</stringValue></value></processMetadataValues>"
            f"<processType>AutoLaunchedFlow</processType><runInMode>SystemModeWithoutSharing</runInMode>{body}"
            f"<start><locationX>50</locationX><locationY>0</locationY><connector><targetReference>{start}</targetReference></connector></start>"
            "<status>Active</status>")
    return HDR + regroup(full) + "\n</Flow>\n"
def flow_old(name, label, desc, body, start):
    return (HDR + f"<apiVersion>68.0</apiVersion>\n<description>{desc}</description>\n<environments>Default</environments>\n"
            f"<interviewLabel>{label} {{!$Flow.CurrentDateTime}}</interviewLabel>\n<label>{label}</label>\n"
            f"<processMetadataValues><name>BuilderType</name><value><stringValue>LightningFlowBuilder</stringValue></value></processMetadataValues>\n"
            f"<processType>AutoLaunchedFlow</processType>\n<runInMode>SystemModeWithoutSharing</runInMode>\n{body}"
            f"<start><locationX>50</locationX><locationY>0</locationY><connector><targetReference>{start}</targetReference></connector></start>\n"
            "<status>Active</status>\n</Flow>\n")
def write(name, content):
    os.makedirs(OUT, exist_ok=True)
    open(f"{OUT}/{name}.flow-meta.xml", "w").write(content)

# ---------------- 1. Verify Customer ----------------
y[0] = 0
b = var("accountNumber", "String", inp=True, desc="Customer account number exactly as the customer typed it")
b += var("phone", "String", inp=True, desc="Registered phone number exactly as the customer typed it. Exactly 10 digits")
b += var("claimsToBeSomeoneElse", "Boolean", inp=True, desc="True if at any point in the conversation the customer said they are not the account holder or are asking about another person. Leave empty or false otherwise")
b += var("endUserId", "String", inp=True, desc="Id of the messaging chat user. Filled in by the system from the chat. When the customer is verified the chat user is linked to the verified contact, so a human transfer can be allowed")
b += var("verified", "Boolean", out=True, desc="True only if the account number and the phone number both match one customer")
b += var("blocked", "Boolean", out=True, desc="True if verification was refused because the customer is not the account holder")
b += var("contactId", "String", out=True, desc="Id of the verified customer. Empty if not verified")
b += var("firstName", "String", out=True, desc="First name of the verified customer. Empty if not verified")
# Phone rules: ignore spaces - ( ) + . then it must be exactly 10 digits. Matching uses the LAST 10 digits of the stored phone,
# so a stored +1 number still matches the 10 digits typed.
b += formula("phoneDigits", "String", 'SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE({!phone}, " ", ""), "-", ""), "(", ""), ")", ""), "+", ""), ".", "")')
b += formula("phoneValid", "Boolean", 'REGEX({!phoneDigits}, "[0-9]{10}")')
b += formula("phoneLast10", "String", "RIGHT({!phoneDigits}, 10)")
b += formula("cleanAccount", "String", "TRIM({!accountNumber})")
b += decision("Third_Party_Check", [("Not_the_account_holder", [cond("claimsToBeSomeoneElse", "EqualTo", True)], "Blocked_Third_Party")], "Inputs_Present")
b += decision("Inputs_Present", [("Both_provided", [cond("cleanAccount", "IsBlank", False), cond("phoneValid", "EqualTo", True)], "Find_Contact")], "Not_Verified")
b += lookup("Find_Contact", "Contact", [("Customer_Account_Number__c", "EqualTo", "@cleanAccount"), ("Phone_Last10__c", "EqualTo", "@phoneLast10")], "Contact_Found", fault="Not_Verified")
b += decision("Contact_Found", [("Match", [cond("Find_Contact", "IsNull", False)], "Set_Verified")], "Not_Verified")
b += assign("Set_Verified", [("verified", True), ("blocked", False), ("contactId", "@Find_Contact.Id"), ("firstName", "@Find_Contact.FirstName")], nxt="Has_End_User")
b += decision("Has_End_User", [("End_user_given", [cond("endUserId", "IsBlank", False)], "Link_End_User")], "Link_Done")
_l = f"<recordUpdates><name>Link_End_User</name><label>Link End User</label>{loc()}"
_l += "<connector><targetReference>Link_Done</targetReference></connector><faultConnector><targetReference>Link_Done</targetReference></faultConnector>"
_l += "<filterLogic>and</filterLogic><filters><field>Id</field><operator>EqualTo</operator><value><elementReference>endUserId</elementReference></value></filters>"
_l += "<inputAssignments><field>ContactId</field><value><elementReference>Find_Contact.Id</elementReference></value></inputAssignments>"
_l += "<object>MessagingEndUser</object></recordUpdates>\n"
b += _l
b += assign("Link_Done", [("blocked", False)])
b += assign("Not_Verified", [("verified", False), ("blocked", False)])
b += assign("Blocked_Third_Party", [("verified", False), ("blocked", True)])
write("Verify_Customer", flow("Verify_Customer", "Verify Customer",
  "Checks account number plus registered phone number (exactly 10 digits, last 10 digits of the stored number compared). Both must match the same customer. Refuses when the customer says they are not the account holder. Returns verified, blocked and the customer Id.", b, "Third_Party_Check"))

# ---------------- 2. Get Latest Bill ----------------
y[0] = 0
b = var("contactId", "String", inp=True, desc="Id of the verified customer. Never use a value typed by the customer")
b += var("billFound", "Boolean", out=True, desc="True if the customer has at least one bill")
b += var("billNumber", "String", out=True, desc="Bill number of the latest bill")
b += var("amount", "Number", out=True, scale=2, desc="Amount of the latest bill")
b += var("dueDate", "Date", out=True, desc="Due date of the latest bill")
b += var("status", "String", out=True, desc="Status of the latest bill: Unpaid, Paid or Overdue")
b += var("extended", "Boolean", out=True, desc="True if the latest bill already had its one extension")
b += var("daysOverdue", "Number", out=True, scale=0, desc="Days past the due date. 0 if paid or not yet due")
b += var("needsVerification", "Boolean", out=True, desc="True if no verified customer Id was given, so the customer must verify first")
b += decision("Has_Contact", [("Contact_given", [cond("contactId", "IsBlank", False)], "Find_Latest_Bill")], "Not_Verified_Yet")
b += lookup("Find_Latest_Bill", "Bill__c", [("Contact__c", "EqualTo", "@contactId")], "Bill_Found_Check", fault="No_Bill", sort=("Due_Date__c", "Desc"))
b += decision("Bill_Found_Check", [("Found", [cond("Find_Latest_Bill", "IsNull", False)], "Set_Bill")], "No_Bill")
b += assign("Set_Bill", [("billFound", True), ("billNumber", "@Find_Latest_Bill.Bill_Number__c"), ("amount", "@Find_Latest_Bill.Amount__c"),
    ("dueDate", "@Find_Latest_Bill.Due_Date__c"), ("status", "@Find_Latest_Bill.Status__c"), ("extended", "@Find_Latest_Bill.Extended__c"),
    ("daysOverdue", "@Find_Latest_Bill.Days_Overdue__c")])
b += assign("No_Bill", [("billFound", False), ("needsVerification", False)])
b += assign("Not_Verified_Yet", [("billFound", False), ("needsVerification", True)])
write("Get_Latest_Bill", flow("Get_Latest_Bill", "Get Latest Bill",
  "Returns the latest bill (most recent due date) for the verified customer.", b, "Has_Contact"))

# ---------------- 3. Grant Payment Extension ----------------
y[0] = 0
b = var("contactId", "String", inp=True, desc="Id of the verified customer. Never use a value typed by the customer")
b += var("granted", "Boolean", out=True, desc="True if the extension was applied")
b += var("reasonCode", "String", out=True, desc="OK, NOT_VERIFIED, NO_BILL, ALREADY_PAID, ALREADY_EXTENDED or TOO_OVERDUE")
b += var("billNumber", "String", out=True, desc="Bill number")
b += var("oldDueDate", "Date", out=True, desc="Due date before the extension")
b += var("newDueDate", "Date", out=True, desc="Due date after the extension. Empty if refused")
b += var("stillOverdue", "Boolean", out=True, desc="True if the new due date is still in the past")
b += var("daysOverdue", "Number", out=True, scale=0, desc="Days past the original due date")
b += const("ExtensionDays", 7)
b += const("MaxDaysOverdue", 30)
b += formula("computedNewDue", "Date", "{!Find_Latest_Bill.Due_Date__c} + {!ExtensionDays}")
b += formula("computedStatus", "String", 'IF({!computedNewDue} >= TODAY(), "Unpaid", "Overdue")')
b += formula("computedStillOverdue", "Boolean", "{!computedNewDue} < TODAY()")
b += decision("Has_Contact", [("Contact_given", [cond("contactId", "IsBlank", False)], "Find_Latest_Bill")], "Not_Verified_Yet")
b += lookup("Find_Latest_Bill", "Bill__c", [("Contact__c", "EqualTo", "@contactId")], "Check_Rules", fault="No_Bill", sort=("Due_Date__c", "Desc"))
b += decision("Check_Rules", [
    ("Bill_missing", [cond("Find_Latest_Bill", "IsNull", True)], "No_Bill"),
    ("Is_paid", [cond("Find_Latest_Bill.Status__c", "EqualTo", "Paid")], "Refuse_Paid"),
    ("Is_extended", [cond("Find_Latest_Bill.Extended__c", "EqualTo", True)], "Refuse_Extended"),
    ("Too_overdue", [cond("Find_Latest_Bill.Days_Overdue__c", "GreaterThan", "@MaxDaysOverdue")], "Refuse_Too_Overdue"),
  ], "Apply_Extension")
b += assign("No_Bill", [("granted", False), ("reasonCode", "NO_BILL")])
b += assign("Not_Verified_Yet", [("granted", False), ("reasonCode", "NOT_VERIFIED")])
b += assign("Refuse_Paid", [("granted", False), ("reasonCode", "ALREADY_PAID"), ("billNumber", "@Find_Latest_Bill.Bill_Number__c")])
b += assign("Refuse_Extended", [("granted", False), ("reasonCode", "ALREADY_EXTENDED"), ("billNumber", "@Find_Latest_Bill.Bill_Number__c"), ("oldDueDate", "@Find_Latest_Bill.Due_Date__c")])
b += assign("Refuse_Too_Overdue", [("granted", False), ("reasonCode", "TOO_OVERDUE"), ("billNumber", "@Find_Latest_Bill.Bill_Number__c"),
    ("oldDueDate", "@Find_Latest_Bill.Due_Date__c"), ("daysOverdue", "@Find_Latest_Bill.Days_Overdue__c")])
# update
upd = f"<recordUpdates><name>Apply_Extension</name><label>Apply Extension</label>{loc()}"
upd += "<connector><targetReference>Set_Granted</targetReference></connector><faultConnector><targetReference>No_Bill</targetReference></faultConnector>"
upd += "<filterLogic>and</filterLogic><filters><field>Id</field><operator>EqualTo</operator><value><elementReference>Find_Latest_Bill.Id</elementReference></value></filters>"
upd += "<inputAssignments><field>Due_Date__c</field><value><elementReference>computedNewDue</elementReference></value></inputAssignments>"
upd += "<inputAssignments><field>Extended__c</field><value><booleanValue>true</booleanValue></value></inputAssignments>"
upd += "<inputAssignments><field>Status__c</field><value><elementReference>computedStatus</elementReference></value></inputAssignments>"
upd += "<object>Bill__c</object></recordUpdates>\n"
b += upd
b += assign("Set_Granted", [("granted", True), ("reasonCode", "OK"), ("billNumber", "@Find_Latest_Bill.Bill_Number__c"),
    ("oldDueDate", "@Find_Latest_Bill.Due_Date__c"), ("newDueDate", "@computedNewDue"), ("stillOverdue", "@computedStillOverdue"),
    ("daysOverdue", "@Find_Latest_Bill.Days_Overdue__c")])
write("Grant_Payment_Extension", flow("Grant_Payment_Extension", "Grant Payment Extension",
  "Moves the due date of the verified customer's latest bill by ExtensionDays. Refuses if paid, already extended, or more than MaxDaysOverdue days past due.", b, "Has_Contact"))

# ---------------- 4. Create Escalation Case ----------------
y[0] = 0
b = var("contactId", "String", inp=True, desc="Id of the verified customer. Leave empty if the customer is not verified")
b += var("caseType", "String", inp=True, desc="Payment Extension, Outage - Priority, Tariff Change, New Connection or Other")
b += var("priority", "String", inp=True, desc="High for a medical device or safety risk. Otherwise Medium")
b += var("summary", "String", inp=True, desc="Short summary of the conversation and what the customer needs")
b += var("caseNumber", "String", out=True, desc="Case number to give to the customer")
b += formula("priorityFinal", "String", 'IF(OR({!priority} = "High", {!priority} = "Low", {!priority} = "Critical"), {!priority}, "Medium")')
b += formula("subjectText", "String", '"Ascend Energy agent: " & IF(ISBLANK({!caseType}), "Other", {!caseType})')
cc = f"<recordCreates><name>Create_Case</name><label>Create Case</label>{loc()}"
cc += "<connector><targetReference>Get_Case_Number</targetReference></connector>"
cc += "<inputAssignments><field>Subject</field><value><elementReference>subjectText</elementReference></value></inputAssignments>"
cc += "<inputAssignments><field>Description</field><value><elementReference>summary</elementReference></value></inputAssignments>"
cc += "<inputAssignments><field>Priority</field><value><elementReference>priorityFinal</elementReference></value></inputAssignments>"
cc += "<inputAssignments><field>Origin</field><value><stringValue>Chat</stringValue></value></inputAssignments>"
cc += "<inputAssignments><field>Type</field><value><elementReference>caseType</elementReference></value></inputAssignments>"
cc += "<inputAssignments><field>ContactId</field><value><elementReference>contactId</elementReference></value></inputAssignments>"
cc += "<object>Case</object><storeOutputAutomatically>true</storeOutputAutomatically></recordCreates>\n"
b += cc
b += lookup("Get_Case_Number", "Case", [("Id", "EqualTo", "@Create_Case")], "Set_Case_Number")
b += assign("Set_Case_Number", [("caseNumber", "@Get_Case_Number.CaseNumber")])
write("Create_Escalation_Case", flow("Create_Escalation_Case", "Create Escalation Case",
  "Creates a Case for a human team member with the conversation summary and returns the case number.", b, "Create_Case"))
print("flows written")

# ---------------- 5. Get Policy Article ----------------
y[0] = 0
b = var("articleKey", "String", inp=True, desc="One of: payment-options, late-fee-policy, power-outage-guidance")
b += var("found", "Boolean", out=True, desc="True if the article was found")
b += var("title", "String", out=True, desc="Article title")
b += var("content", "String", out=True, desc="Article text. The only source for policy answers")
b += lookup("Find_Article", "Knowledge__kav", [("UrlName", "EqualTo", "@articleKey"), ("PublishStatus", "EqualTo", "Online"), ("Language", "EqualTo", "en_US")], "Article_Check", fault="No_Article")
b += decision("Article_Check", [("Article_exists", [cond("Find_Article", "IsNull", False)], "Set_Article")], "No_Article")
b += assign("Set_Article", [("found", True), ("title", "@Find_Article.Title"), ("content", "@Find_Article.FAQ_Answer__c")])
b += assign("No_Article", [("found", False)])
write("Get_Policy_Article", flow("Get_Policy_Article", "Get Policy Article",
  "Returns one of the three Ascend Energy Knowledge articles by URL name, so the agent answers policy questions only from approved text.", b, "Find_Article"))
print("policy flow written")

# ---------------- 5. Get Policy Article ----------------
y[0] = 0
b = var("articleKey", "String", inp=True, desc="One of: payment-options, late-fee-policy, power-outage-guidance")
b += var("found", "Boolean", out=True, desc="True if the article was found")
b += var("title", "String", out=True, desc="Article title")
b += var("content", "String", out=True, desc="Article text. The only source for policy answers")
b += lookup("Find_Article", "Knowledge__kav", [("UrlName", "EqualTo", "@articleKey"), ("PublishStatus", "EqualTo", "Online"), ("Language", "EqualTo", "en_US")], "Article_Check", fault="No_Article")
b += decision("Article_Check", [("Article_exists", [cond("Find_Article", "IsNull", False)], "Set_Article")], "No_Article")
b += assign("Set_Article", [("found", True), ("title", "@Find_Article.Title"), ("content", "@Find_Article.FAQ_Answer__c")])
b += assign("No_Article", [("found", False)])
write("Get_Policy_Article", flow("Get_Policy_Article", "Get Policy Article",
  "Returns one of the three Ascend Energy Knowledge articles by URL name, so the agent answers policy questions only from approved text.", b, "Find_Article"))
print("policy flow written")
