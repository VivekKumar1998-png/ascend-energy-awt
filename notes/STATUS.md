# Ascend Energy V8: build status (17 Nov 2026)

Project folder: `ascend-energy-v8/` (moved to `~/Documents/ascend-energy-v8` on 17 Nov, own workspace, no git repo yet).
Org alias: `Ascend` (kumarvivek2@salesforce.com.awtcs), Enterprise trial, expires 16 Dec 2026. The alias is in the user-level sf CLI config, so it works from any folder.

## Done and tested
| Item | Status |
|---|---|
| `Bill__c` object, 8 fields, Contact fields `Customer_Account_Number__c` and `Phone_Digits__c` | Deployed |
| Permission sets `Ascend_V8_Access` (you) and `Ascend_V8_Agent` (agent user) | Deployed, assigned |
| Sample data: 7 customers, 8 bills (`scripts/load_sample_data.apex`, re-runnable) | Loaded |
| 3 Knowledge articles (`scripts/load_articles.apex`) | Published |
| Flows: Verify_Customer, Get_Latest_Bill, Grant_Payment_Extension, Create_Escalation_Case, Get_Policy_Article | Active. `scripts/test_flows.py`: 21 of 21 pass |
| Agent Script `Ascend_Energy_Assistant` (7 subagents) | Written, validates, but CANNOT be published in this org (Agent API 404). Reference only |

## Agent in the classic builder
- The agent `Ascend_Energy_Assistant` was created by the UI wizard (classic topic-based, Inactive, v1). Planner id `16jgK000002R7kDQAS`, bot `0XxgK000002ZHRRSA4`.
- Shared (global) assets come from this project: 5 actions in `genAiFunctions/`, 7 topics in `genAiPlugins/`.
  Regenerate with `python3 scripts/gen_agent_classic.py` then `python3 scripts/gen_action_schemas.py`, then deploy both folders.
- The topics and actions were added to the agent by the user in the builder (New Topic / New Action, Add from Asset Library).
  Verified in the org: 7 local topics attached to the planner, topic-to-action links present, Verify Customer also added to Bill Status.
- Welcome and error messages are in `bots/Ascend_Energy_Assistant/v1.botVersion-meta.xml` (deployed).
- Agent user: `ascend_energy_assistant@...ext` with `Ascend_V8_Agent`. The user `ascend.agent@salesforce.com.awtcs` is unused.

## DO NOT redeploy
`genAiPlannerBundles/`, `aiAuthoringBundles/`, and the agent's local topics. A redeploy overwrites what was added in the builder.

## Current problem (17 Nov)
- Preview works for verification: "Hi Amelia! I've successfully verified your account." (Verify Customer runs).
- Next step fails: the agent says it cannot fetch the latest bill's due date.
- Checked org-side: `Get_Latest_Bill` run directly through REST for Amelia's Contact Id returns billFound true, ASC-1001-01, 142.50, due 2026-11-19, Unpaid.
  Flow access exists in both permission sets, Bill Status has Get Latest Bill linked.
- Suspect: the agent passes a wrong or empty Contact Id into Get Latest Bill (Verify Customer outputs are `isDisplayable false`, `isUsedByPlanner true`).
- Needed: the plan trace of the failing turn (preview, Show details or Plan tracer), specifically Get Latest Bill input and output.
- Likely fixes: (1) edit the Bill Status and Payment Extension instructions to say "pass the Contact Id returned by Verify Customer into Get Latest Bill / Grant Payment Extension" (do this in the builder or update the instruction rows);
  (2) if the action does not run or errors, recreate it through the builder (New Action, Flow) so the builder generates the schemas.

## Not done yet
1. Fix the bill lookup in the preview, test all 7 topics, Activate.
2. Connect it to the Messaging for In-App and Web channel (Setup, Embedded Service Deployments) and test in the chat window.
3. Testing Center cases (about 20), CP1 scope note, CP3 design rationale, test report on Squad 7's V7 agent.

## Facts worth remembering
- Sample customers (account number, phone as registered):
  A ASC-1001 (415) 555-0101 | B ASC-1002 +1 415 555 0102 | C ASC-1003 415-555-0103 | D ASC-1004 4155550104 |
  E ASC-1005 415 555 0105 | F ASC-1006 (415) 555-0106 | G ASC-1007 415.555.0107
  Customer B's registered number starts with 1, so the digits are 14155550102.
- After tests change the data, reset with `sf apex run -o Ascend -f scripts/load_sample_data.apex`.
  Delete test Cases with `scripts/reset_data.apex`.
- Deploy helper: `scripts/deploy.sh <paths>` (the CLI cannot write its cache in the Cursor sandbox, the helper reads the real result over REST).
- Knowledge is read by the `Get_Policy_Article` Flow, not by org-wide search. The org has 53 unrelated articles (401k, solar), this keeps them out of the agent.
- The extension changes the real due date. Re-run the sample data script before every demo.
- The earlier chat (full history) is at `/Users/kumarvivek2/.cursor/projects/Users-kumarvivek2-Documents-GitHub-Salesforce-EDDC-eddc-global-salesforce-platform/agent-transcripts/8734a360-465a-4d15-b7cb-412841d0743d/8734a360-465a-4d15-b7cb-412841d0743d.jsonl`. Search it by keyword if something is unclear.


## 18 Nov fixes (prepared, NOT deployed, waiting for approval)
1. Third party block: Verify_Customer has a `claimsToBeSomeoneElse` input and `blocked` output, plus topic instructions with a fixed refusal message.
2. Verify once: `VerifiedCustomerId` is filled from Verify output and fed into Get Latest Bill / Grant Extension / Create Case; rules hide Verify once set.
3. Phone: customer must type exactly 10 digits (separators ignored; 9, 11 or +1 are rejected). Match on the last 10 digits of the stored phone (`Contact.Phone_Last10__c`), so customer B's stored +1 number still matches.
4. Bills related list added to both Contact layouts.
5. Site: `scripts/gen_site.py` writes the minimal Help site, hidden ESW frame site, EmbeddedServiceConfig and MessagingChannel. Site creation can't be proven by check-only; the channel needs the agent ACTIVE first.
Order: `scripts/apply_after_approval.sh step1..step5`. Check-only helper: `scripts/validate.sh`. Rollback copy: `.backup-before-fixes/`.

## 18 Nov, later: customer-facing agent and site (DEPLOYED)
- Deployed + activated: `Ascend_Help_Agent` (Agentforce Service Agent, same topics/actions/rules as `Ascend_Energy_Assistant`; built by `scripts/build_service_agent.py`). The internal planner agent cannot be used on a messaging channel.
- Deployed: MessagingChannel `Ascend_Help_Messaging` (EmbeddedMessaging, agent `Ascend_Help_Agent`).
- Site `Ascend Energy Help` (`/ascendhelp`) created through `POST /connect/communities` (template "Build Your Own (LWR)"), content deployed from `scripts/build_help_site.py`. Status still UnderConstruction (not published).
- DONE: Embedded Service Deployment `Ascend_Help_Web` was created in Setup, published, and the chat runs on the Help page. Tested live: verify, 9-digit phone rejected, bill shown, no re-verification, third-party block (also after the customer changes his mind).
- Fix found in live test: the bill actions must NOT be gated on VerifiedCustomerId (rules are evaluated when a turn starts, so the bill was not available in the turn that verifies and the chat ended). Also the Verification topic description no longer attracts bill/extension requests; Bill Status and Payment Extension topics verify the customer themselves.
- Stray: a second BYO site `ESW_Ascend_Help_Web` (prefix ESWAscendHelpWeb) was created while trying the frame site; unused, can be deleted.

## Human transfer and "never log a case on your own" (18 Nov)
- Case rule: the agent explains the policy first and asks "Would you like me to log a request?"; Create Escalation Case runs only after a clear yes (shared CASE_RULE in scripts/agent_content.py; applies to late fee, payment extension too overdue, tariff/new connection, outage priority, off-topic). Late fee reply: "I can't waive, reduce, or reverse late fees, but if you believe the fee is incorrect, I can log a request for a team member to review it."
- Live transfer (Help agent only): Omni-Channel outbound flow `Ascend_Human_Escalation` (RoutingFlow, queue `SDO_Service_Messaging`, service channel `sfdc_livemessage`, checks for available reps first), `canEscalate=true` on the Escalation topic, `outboundRouteConfigs` on the Messaging and CustomerWebClient surfaces (written by scripts/build_service_agent.py). If nobody is available the agent says so and offers to log a request (only after yes).
- Queue: user kumarvivek2@salesforce.com.awtcs added as a direct member of `SDO_Service_Messaging` (the queue also has the public group "Service - Agents").
- Tested live: late fee refusal, case only after yes (00001082), transfer attempt with nobody online (falls back correctly).
- NOT tested: a real hand-over to a person (needs an agent set to "Messaging - Available" in the Omni-Channel utility of a Service Console).

## Fix: bill shown/"no bill" without verification (18 Nov, 9 PM)
- Symptom: "latest bill" -> agent asked "are you the account holder?" -> "Yes" -> "I couldn't find any bill". It never asked for account number and phone; Get Latest Bill ran with an empty customer Id (no data leaked, but wrong).
- Fix: VERIFY_FIRST rule (asking "are you the holder" is not verification); Get Latest Bill now returns needsVerification=true and Grant Payment Extension returns NOT_VERIFIED when no verified customer Id exists, and the agent must then ask for account number + phone, verify, and run the action again; Payment Extension topic now has its own Verify Customer action (cloned in scripts/build_planner_bundle.py) so it verifies and continues in the same turn.
- Tested: bill path and extension path both ask for account + phone first.

## Removed the unused internal agent (18 Nov, 9:30 PM)
- `Ascend_Energy_Assistant` (internal agent, not attached to any channel) was deleted from the org. `Ascend_Help_Agent` is the only agent and is Active.
- The repo still keeps `force-app/.../Ascend_Energy_Assistant` and the build scripts, because `build_service_agent.py` copies the Help agent from it. Do not deploy that folder again unless you want the internal agent back.

## One-time verification redesign (Help agent)
- Verify Customer now exists ONLY in the Ascend_Verification topic. Removed from Bill Status / Payment Extension.
- Verify output_contactId -> bot variable VerifiedCustomerId (includeInPrompt=true so the agent can read it).
- Rule expressions: Verify available only when VerifiedCustomerId is empty; Get Latest Bill / Grant Extension only when it is set.
- Topics read VerifiedCustomerId: empty -> go to Verification; set -> act directly, never ask again.
- Trade-off: after verifying, the bill/extension action runs from the NEXT message (rules are evaluated at turn start), so the agent asks "Shall I show your latest bill now?".
- Tested live: verify once -> bill -> extension with no re-verification; third-party block; 9-digit phone rejected.

## Enforced "verify before human transfer"
- Instructions: Escalation topic never transfers while VerifiedCustomerId is empty; the Verification topic handles "talk to a person" first, then asks "Shall I transfer you?".
- Hard check: Verify_Customer flow gets input endUserId (context variable EndUserId -> mapping input_endUserId) and, on success, sets MessagingEndUser.ContactId to the verified contact (standard field, no new fields).
- Ascend_Human_Escalation routing flow now looks up MessagingSession -> MessagingEndUser first; if ContactId is blank it ends without routing (agent then offers a case). Only then does it check availability and route.
- Verified live: chat user linked to Amelia after verification (MessagingEndUser.ContactId set); unverified chat users stay null.
- Caveat: the link stays on the browser's chat user, so a later chat from the same browser is treated as verified for transfers only (bill/extension still need Verify because VerifiedCustomerId is per conversation).
- Not observable without an online human: the routing flow's refusal looks the same as "nobody available".
