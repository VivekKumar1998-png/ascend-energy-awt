// Removes test Cases created by the Ascend agent / flow tests (only the agent's own subject prefix).
delete [SELECT Id FROM Case WHERE Subject LIKE 'Ascend Energy agent:%'];
