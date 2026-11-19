"""Calls the four Flows through the REST API and prints a pass/fail table. Run: python3 scripts/test_flows.py"""
import json, subprocess, os
os.environ["SF_DISABLE_LOG_FILE"] = "true"
def sf(*a):
    r = subprocess.run(["sf", *a, "-o", "Ascend"], capture_output=True, text=True)
    t = r.stdout[r.stdout.find("{"):] if "{" in r.stdout else r.stdout
    return json.loads(t) if t.strip().startswith(("{", "[")) else t
def flow(name, inputs):
    r = subprocess.run(["sf","api","request","rest",f"/services/data/v68.0/actions/custom/flow/{name}","-X","POST","-H","Content-Type: application/json",
                        "-b",json.dumps({"inputs":[inputs]}),"-o","Ascend"],capture_output=True,text=True)
    t = r.stdout[r.stdout.find("["):]
    res = json.loads(t)[0]
    return res["outputValues"] if res["isSuccess"] else {"ERROR": res["errors"]}
q = subprocess.run(["sf","data","query","-o","Ascend","--json","-q","SELECT Id, Customer_Account_Number__c FROM Contact WHERE Customer_Account_Number__c LIKE 'ASC-%'"],capture_output=True,text=True)
ids = {r["Customer_Account_Number__c"]: r["Id"] for r in json.loads(q.stdout)["result"]["records"]}
cid = {k: ids["ASC-100"+str(i)] for i, k in enumerate("ABCDEFG", 1)}
fails = 0
def check(label, got, **expect):
    global fails
    bad = {k: (got.get(k), v) for k, v in expect.items() if got.get(k) != v}
    if bad: fails += 1
    print(("PASS " if not bad else "FAIL ") + label, "" if not bad else f"-> {bad}  full={got}")
print("--- Verify_Customer")
check("A right number+phone",  flow("Verify_Customer", {"accountNumber":"ASC-1001","phone":"(415) 555-0101"}), verified=True, firstName="Amelia")
check("A phone typed differently", flow("Verify_Customer", {"accountNumber":" asc-1001 ","phone":"415 555 0101"}), verified=True)
check("A wrong phone",         flow("Verify_Customer", {"accountNumber":"ASC-1001","phone":"4155550199"}), verified=False)
check("A phone of customer B", flow("Verify_Customer", {"accountNumber":"ASC-1001","phone":"+1 415 555 0102"}), verified=False)
check("Unknown account",       flow("Verify_Customer", {"accountNumber":"ASC-9999","phone":"4155550101"}), verified=False)
check("Blank phone",           flow("Verify_Customer", {"accountNumber":"ASC-1001","phone":""}), verified=False)
check("Blank both",            flow("Verify_Customer", {"accountNumber":"","phone":""}), verified=False)
print("--- Verify_Customer: phone must be exactly 10 digits")
check("A 10 digit, plain",      flow("Verify_Customer", {"accountNumber":"ASC-1001","phone":"4155550101"}), verified=True)
check("A 10 digit, dashes",     flow("Verify_Customer", {"accountNumber":"ASC-1001","phone":"415-555-0101"}), verified=True)
check("A 9 digits rejected",    flow("Verify_Customer", {"accountNumber":"ASC-1001","phone":"155550101"}), verified=False)
check("A 9 digits with dashes", flow("Verify_Customer", {"accountNumber":"ASC-1001","phone":"155-550-101"}), verified=False)
check("A 11 digits rejected",   flow("Verify_Customer", {"accountNumber":"ASC-1001","phone":"14155550101"}), verified=False)
check("A +1 prefix rejected",   flow("Verify_Customer", {"accountNumber":"ASC-1001","phone":"+1 (415) 555-0101"}), verified=False)
check("A 8 digits rejected",    flow("Verify_Customer", {"accountNumber":"ASC-1001","phone":"55550101"}), verified=False)
check("A letters in phone",     flow("Verify_Customer", {"accountNumber":"ASC-1001","phone":"call me maybe"}), verified=False)
check("A 10 digits but wrong",  flow("Verify_Customer", {"accountNumber":"ASC-1001","phone":"4155550199"}), verified=False)
check("B stored with +1, typed 10 digits", flow("Verify_Customer", {"accountNumber":"ASC-1002","phone":"4155550102"}), verified=True)
print("--- Verify_Customer: not the account holder is blocked")
check("A right details but says not the holder", flow("Verify_Customer", {"accountNumber":"ASC-1001","phone":"4155550101","claimsToBeSomeoneElse":True}), verified=False, blocked=True)
check("A claim flag false still verifies", flow("Verify_Customer", {"accountNumber":"ASC-1001","phone":"4155550101","claimsToBeSomeoneElse":False}), verified=True, blocked=False)
check("Wrong details are not blocked, just not verified", flow("Verify_Customer", {"accountNumber":"ASC-1001","phone":"4155550199"}), verified=False, blocked=False)
print("--- Get_Latest_Bill")
check("A", flow("Get_Latest_Bill", {"contactId":cid["A"]}), billFound=True, billNumber="ASC-1001-01", status="Unpaid", daysOverdue=0)
check("E latest is the paid one", flow("Get_Latest_Bill", {"contactId":cid["E"]}), billNumber="ASC-1005-02", status="Paid")
check("B 45 overdue", flow("Get_Latest_Bill", {"contactId":cid["B"]}), daysOverdue=45)
check("blank contact", flow("Get_Latest_Bill", {"contactId":""}), billFound=False)
print("--- Grant_Payment_Extension")
check("A ok",        flow("Grant_Payment_Extension", {"contactId":cid["A"]}), granted=True, reasonCode="OK", stillOverdue=False)
check("A again refused", flow("Grant_Payment_Extension", {"contactId":cid["A"]}), granted=False, reasonCode="ALREADY_EXTENDED")
check("B too overdue", flow("Grant_Payment_Extension", {"contactId":cid["B"]}), granted=False, reasonCode="TOO_OVERDUE", daysOverdue=45)
check("C ok, no longer overdue", flow("Grant_Payment_Extension", {"contactId":cid["C"]}), granted=True, stillOverdue=False)
check("D already extended", flow("Grant_Payment_Extension", {"contactId":cid["D"]}), granted=False, reasonCode="ALREADY_EXTENDED")
check("E latest paid", flow("Grant_Payment_Extension", {"contactId":cid["E"]}), granted=False, reasonCode="ALREADY_PAID")
check("G ok but still overdue", flow("Grant_Payment_Extension", {"contactId":cid["G"]}), granted=True, stillOverdue=True)
check("blank contact", flow("Grant_Payment_Extension", {"contactId":""}), granted=False, reasonCode="NO_BILL")
print("--- Create_Escalation_Case")
r = flow("Create_Escalation_Case", {"contactId":cid["A"],"caseType":"Outage - Priority","priority":"High","summary":"TEST: customer has a home oxygen concentrator and no power."})
print(r); check("case created", {"has_number": bool(r.get("caseNumber"))}, has_number=True)
r = flow("Create_Escalation_Case", {"contactId":"","caseType":"Tariff Change","priority":"","summary":"TEST: unverified tariff question."})
print(r); check("case without contact", {"has_number": bool(r.get("caseNumber"))}, has_number=True)
print("\nFAILURES:", fails)
