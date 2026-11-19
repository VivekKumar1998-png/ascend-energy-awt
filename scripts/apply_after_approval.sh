#!/bin/bash
# NOT RUN YET. Run only after approval, step by step. Each step stops on failure.
set -e
export SF_DISABLE_LOG_FILE=true SF_DISABLE_TELEMETRY=true
D=force-app/main/default
step1() { # fields, permission sets, layouts, flow
  scripts/deploy.sh $D/objects/Contact $D/permissionsets $D/layouts $D/flows/Verify_Customer.flow-meta.xml; }
step2() { # agent: planner bundle (built from the live baseline)
  scripts/deploy.sh $D/genAiPlannerBundles; }
step3() { # data + tests
  sf apex run -o Ascend -f scripts/load_sample_data.apex && python3 scripts/test_flows.py; }
step4() { # activate the agent (latest version)
  sf agent activate -o Ascend -n Ascend_Energy_Assistant; }
step5() { # customer-facing agent (Service Agent copy), then its channel. Help site itself was created through the org API (see notes).
  python3 scripts/build_service_agent.py && scripts/deploy.sh $D/bots/Ascend_Help_Agent $D/genAiPlannerBundles/Ascend_Help_Agent
  sf agent activate -o Ascend -n Ascend_Help_Agent
  scripts/deploy.sh $D/messagingChannels; }
step6() { python3 scripts/build_help_site.py && scripts/deploy.sh $D/digitalExperiences; }
"${1:?usage: $0 step1|step2|step3|step4|step5}"
