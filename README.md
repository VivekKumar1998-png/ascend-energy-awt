# Ascend Energy V8 (Squad 8)

Salesforce DX project for the **Ascend Energy Help** agent, an Agentforce Service Agent for a utility company. Customers verify with their account number and phone number, then can check their latest bill, request a 7-day payment extension, read policy answers from Knowledge, and be escalated to a person or a Case.

## What the agent does

- **Verify:** Account number plus full registered phone number. Verification happens once per conversation.
- **Bill status:** Latest bill amount, due date, and status.
- **Payment extension:** Moves the due date 7 days later. Refused if the bill is Paid, already extended, or more than 30 days overdue.
- **Policy questions:** Answered only from Knowledge articles, never invented.
- **Escalation:** Creates a Case after the customer agrees, and transfers to a human when one is available.
- **Refusals:** Fee waivers, other customers' data, and requests to ignore its rules.

## Project structure

- `force-app/main/default/`: Metadata (objects, fields, flows, agents, messaging, site, permission sets)
- `scripts/`: Sample data, Flow tests, deploy and validation helpers, and agent/site generators
- `notes/`: Build plan, status log, and Knowledge article text
- `config/`: Scratch org definition
- `sfdx-project.json`: Project manifest (API version 68.0)

## Prerequisites

- Salesforce CLI (`sf`)
- Python 3 (for the scripts)
- An org authorized with the alias `Ascend`:
  ```bash
  sf org login web --alias Ascend
  ```

## Setup

```bash
# Deploy metadata
./scripts/deploy.sh force-app

# Load sample customers, bills, and Knowledge articles
sf apex run -o Ascend -f scripts/load_sample_data.apex
sf apex run -o Ascend -f scripts/load_articles.apex

# Run Flow tests
python3 scripts/test_flows.py
```

Re-run `load_sample_data.apex` before each demo, because the payment extension changes the real due dates. To remove test Cases, run `scripts/reset_data.apex`.

## Sample customers

| Customer | Account number | Phone (as registered) |
|---|---|---|
| A | ASC-1001 | (415) 555-0101 |
| B | ASC-1002 | +1 415 555 0102 |
| C | ASC-1003 | 415-555-0103 |
| D | ASC-1004 | 4155550104 |
| E | ASC-1005 | 415 555 0105 |
| F | ASC-1006 | (415) 555-0106 |
| G | ASC-1007 | 415.555.0107 |

## Important notes

- **Do not redeploy** `genAiPlannerBundles/`, `aiAuthoringBundles/`, or the agent's local topics unless you intend to overwrite changes made in Agentforce Builder.
- `Ascend_Help_Agent` is the only active agent. The `Ascend_Energy_Assistant` folder is kept as the source the Help agent is built from.
- Never commit org credentials. `.env*`, `*.key`, and `*.pem` are git-ignored, and `.sf/` and `.sfdx/` hold local CLI auth.

## Status

Verification, bill lookup, payment extension, escalation, and the Help site are deployed and tested in the org. A live hand-over to a human agent has not been tested yet because it needs an agent online in the Omni-Channel utility.
