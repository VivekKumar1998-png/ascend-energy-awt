# Ascend Energy V8 (Squad 8): build plan and decisions

Saved 16 Nov 2026. This is the agreed plan from the planning chat. Nothing has been built yet.
The case study PDF is POD2 Business Case Study, Agentforce Builder Cohort.

## 1. Who and what

| Item | Value |
|---|---|
| Squad | 8, variant V8 Utilities, business unit Ascend Energy |
| Tested by | Squad 5 |
| We test | Squad 7, variant V7 Manufacturing (Ascend Industrial). We must write a test report. |
| Roles | One person doing all three: Topics and Instructions, Actions, Trust and Testing |
| Time | About 7 days. Checkpoint dates are still to be confirmed. |
| Org | Login done on 16 Nov 2026. Saved alias is `Ascend` (kumarvivek2@salesforce.com.awtcs). |
| Build style | Agent Script in Agentforce Builder. Flows for actions. Keep it simple. |
| Test window | The messaging page from Agentforce (Messaging for In-App and Web). Builder preview is only for wiring. |

Keep this work out of the Rich Products repo. Move this folder into the new project when it exists
(`sf project generate --name ascend-energy-v8`).

## 2. What the agent must do (from the brief)

| Core job | V8 version |
|---|---|
| Verify | Customer account number (custom field on Contact) plus full registered phone number |
| Look up | Latest bill: amount, due date, status |
| Act | Payment extension: moves the due date 7 days later |
| Answer from knowledge | Payment options, Late fee policy, Power outage guidance. Never invent policy. |
| Escalate | Human gets a short summary: out of scope, sensitive, or the user asks |

Rules from the brief:
- Cannot waive charges or late fees.
- Bills more than 30 days overdue cannot be extended and are escalated.
- Edge case: outage plus a medical device at home. Share the outage guidance, escalate as a priority, with a summary.
- Out of scope, escalate: tariff changes, new connections.
- Every agent refuses: another person's data, acting before verification, ignoring its rules or revealing instructions, acting outside utilities.
- Standard objects only (Contact, Case, Knowledge) plus at most one custom object.

## 3. Final decisions (and why)

| Topic | Decision | Reason |
|---|---|---|
| Verification | Account number plus full phone number, as the brief says | Email OTP was considered and dropped |
| Failed verification | Try again, no lockout, no counter | Keep it simple |
| Phone match | Digits only, full number. Compare input to formula `Phone_Digits__c` on Contact | Matches however it is typed |
| Failure message | One generic message. Never say which value was wrong. | Avoids leaking account data |
| Latest bill | The bill with the most recent due date | Brief says latest bill |
| New due date | Old due date + 7 days | Brief wording. Counting from today would let a bill at 29 days late become 36 days late. |
| Refuse extension | More than 30 days overdue, already extended, or Paid | Brief rule 30 days. One extension per bill agreed. |
| 30-day count | From the due date to today | "Overdue" means past due date. Status label is not used. |
| Bill date | Stored and shown. Not used in any rule. | Added field `Bill_Date__c` |
| After extension | Status Unpaid if new due date is today or later. Stays Overdue if still past. | |
| New due date already passed | The agent says so plainly and asks the customer to pay as soon as they can | Happens for bills 8 to 30 days overdue |
| Extension applies to | Latest bill only | |
| No bill found | Flow returns "no bill", agent says so | |
| Customer asks for a person | Escalate (rule in the Escalate topic) | Brief says escalate when the user asks |
| Escalation | Always create a Case with the summary. Also transfer the chat if the org supports it. | |
| Stricter 7-day cutoff | Considered and rejected | Not in the brief, so Squad 5 would mark it as a failure |

## 4. Data model

| Object | Fields |
|---|---|
| Contact | `Customer_Account_Number__c` (Text, unique). Standard `Phone` is the registered phone. `Phone_Digits__c` is a formula that strips spaces, dashes, brackets and `+` from `Phone`. |
| Bill__c (the one custom object) | `Bill_Number__c` (Text, unique), `Bill_Date__c` (Date), `Due_Date__c` (Date), `Amount__c` (Currency), `Status__c` (Picklist: Unpaid, Paid, Overdue), `Extended__c` (Checkbox), `Contact__c` (Lookup to Contact), `Days_Overdue__c` (Formula: days past `Due_Date__c`, 0 if Paid or not yet due) |
| Case | Escalation record. Extra Type values: Payment Extension, Outage - Priority, Tariff Change, New Connection, Other. Summary goes in Description. High priority for the medical-device case. |
| Knowledge | Three articles. Full text is in `knowledge-articles.md`. |

## 5. Sample data

Loaded by one Apex script that uses `TODAY()`, so dates stay correct on demo day.
Every bill has `Due_Date__c` = `Bill_Date__c` + 21 days.

| Customer | Bill | What it tests |
|---|---|---|
| A | Unpaid, due in 3 days | Required by the brief. Happy path. |
| B | 45 days overdue | Required by the brief. Refused and escalated. |
| C | 4 days overdue | Extended. New due date is in the future, so no longer overdue. |
| G | 12 days overdue | Extended. New due date has also passed, so the agent says so. |
| D | Due in 5 days, already extended | Second request escalated |
| E | Latest bill Paid, older bill Unpaid | "Latest bill" returns the right one |
| F | Another customer's bill | Target for "show me someone else's bill" |

## 6. Flows (four, plus one for escalation)

| Flow | What it does | Rule inside the Flow |
|---|---|---|
| Verify Customer | Both account number and full phone must match one Contact. Returns verified yes or no and the Contact Id. | Generic failure message |
| Get Latest Bill | Takes the verified Contact Id. Returns amount, due date, status, extended, days overdue. | Only that customer's bills |
| Grant Payment Extension | Re-fetches the latest bill by the verified Contact Id. New due date = old due date + `ExtensionDays`. Ticks `Extended__c`. Returns a reason code and a `still_overdue` flag. | Refuses if Paid, already extended, or days overdue > `MaxDaysOverdue` |
| Create Escalation Case | Creates a Case with type, priority, summary. Returns the case number. | High priority for the medical-device case |

Flow constants: `ExtensionDays = 7`, `MaxDaysOverdue = 30`.
The agent only quotes what the Flow returned.

## 7. Agent Script design

| Piece | Design |
|---|---|
| Variables | `verified`, `contact_id` |
| Topics | Welcome and routing, Verify, Bill status, Payment extension, Policy questions, Escalate, Refuse |
| Locks | Bill status and Payment extension unlock only when `verified` is true |
| Fixed steps | The agent asks the customer to confirm before the extension runs. Every handoff creates a Case first. |
| Interrupt from any topic | Outage plus medical device: share the outage guidance, create a High-priority Case with a summary, then hand off |
| Agent decides | Tone and short plain wording |
| Refuses | Fee waivers, other people's data, "ignore your rules", revealing instructions. Escalates tariff changes and new connections. |

## 8. Testing

Test window: the Agentforce messaging page.

Testing Center set, about 20 cases:
- The five core jobs: verify, look up, act, answer from knowledge, escalate.
- Business rules: 45 days overdue, second extension, fee waiver, Paid bill.
- Edge case: outage with a medical device.
- Out of scope: tariff change, new connection.
- Rogue tests: another person's bill, acting before verification, "ignore your rules", "show me your instructions", right account number with wrong phone, asking for a person.

### Our test report on Squad 7 (V7 Manufacturing, Ascend Industrial)

Report must cover: tester squad and agent under test, scope checked (which of the 5 jobs), test cases run (include the edge case and at least one out-of-scope request), guardrail and rogue-agent checks, results (exact agent response for each failure), severity and recommended fix.

V7 brief in short:
- Verify: work email plus the serial number of an asset on their account.
- Lookup: asset details and warranty status.
- Action: schedule a technician visit by creating a Case with the preferred date.
- Rules: visits only for assets on the contact's own account. Free only under an active warranty, otherwise a paid-service request.
- Edge case: smoke, sparks or other hazard. Tell them to stop using the machine and isolate power, escalate immediately as a safety incident, do not book a routine visit.
- Out of scope: buying parts, price negotiation.
- Sample data: one account with 3 assets, at least one in warranty and one expired.

## 9. Seven-day plan (dates to be confirmed)

| Day | Work | Output |
|---|---|---|
| 1 | Org checks (Agentforce, Agent Script, Knowledge, Messaging), fields, Bill object, sample data, articles | Data and Knowledge ready |
| 2 | Verify, Get Latest Bill, Grant Extension flows, tested in Flow debug | 3 working actions |
| 3 | Escalation flow, Agent Script, locks, attach actions. Write the scope note. | CP1 scope note |
| 4 | Messaging page, end-to-end run of all 5 jobs and the edge case | CP2 working agent |
| 5 | Squad 5 tests us. We test Squad 7. Testing Center set. | Our test report on Squad 7 |
| 6 | Fix findings, guardrails, one-page design rationale | CP3 hardened agent |
| 7 | Rehearse the demo with three live changes | Demo ready |

Demo live changes, one per role:
- Topics owner: add a new out-of-scope topic.
- Actions owner: change `ExtensionDays` from 7 to 10 in the Flow constant (and update Article 1 so it says the same number).
- Trust owner: add a rogue test and fix it.

## 10. Notes for the CP1 scope note and for Squad 5

- Verification uses the full account number and the full phone number. No lockout.
- The extension moves the old due date by 7 days. A bill 8 to 30 days overdue still shows an overdue due date after the extension. This is by design.
- Bills more than 30 days overdue are refused and escalated.
- One extension per bill.

## 11. Next steps

1. Run the org checks with the CLI (use the alias `Ascend`, or re-save it as `ascend-v8`).
2. Build in the order of the seven-day plan.
3. Open items: confirm which test page the org gives for the messaging channel, and confirm Agent Script is available in this org.
