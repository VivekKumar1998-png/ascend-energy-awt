// Ascend Energy V8 sample data. Safe to re-run: removes its own records first.
// Every bill: Due_Date = Bill_Date + 21 days. Dates are relative to TODAY().
delete [SELECT Id FROM Bill__c WHERE Bill_Number__c LIKE 'ASC-%'];
delete [SELECT Id FROM Contact WHERE Customer_Account_Number__c LIKE 'ASC-%'];

Account acc;
List<Account> accs = [SELECT Id FROM Account WHERE Name = 'Ascend Energy Customers' LIMIT 1];
if (accs.isEmpty()) { acc = new Account(Name = 'Ascend Energy Customers'); insert acc; } else { acc = accs[0]; }

// key, first, last, account number, phone as registered
List<List<String>> people = new List<List<String>>{
  new List<String>{'A','Amelia','Hart','ASC-1001','(415) 555-0101'},
  new List<String>{'B','Brian','Cole','ASC-1002','+1 415 555 0102'},
  new List<String>{'C','Chloe','Reed','ASC-1003','415-555-0103'},
  new List<String>{'D','Daniel','Ford','ASC-1004','4155550104'},
  new List<String>{'E','Elena','Ortiz','ASC-1005','415 555 0105'},
  new List<String>{'F','Farid','Khan','ASC-1006','(415) 555-0106'},
  new List<String>{'G','Grace','Lin','ASC-1007','415.555.0107'}
};
Map<String, Contact> byKey = new Map<String, Contact>();
for (List<String> p : people) {
  byKey.put(p[0], new Contact(AccountId = acc.Id, FirstName = p[1], LastName = p[2],
      Customer_Account_Number__c = p[3], Phone = p[4], Email = p[1].toLowerCase() + '.' + p[2].toLowerCase() + '@example.com'));
}
insert byKey.values();

// key, bill number, days from today to due date (negative = past due), amount, status, extended
List<List<Object>> rows = new List<List<Object>>{
  new List<Object>{'A','ASC-1001-01',   3, 142.50,'Unpaid',  false},
  new List<Object>{'B','ASC-1002-01', -45, 310.20,'Overdue', false},
  new List<Object>{'C','ASC-1003-01',  -4,  88.75,'Overdue', false},
  new List<Object>{'D','ASC-1004-01',   5, 164.00,'Unpaid',  true},
  new List<Object>{'E','ASC-1005-01', -33,  95.30,'Overdue', false},
  new List<Object>{'E','ASC-1005-02',  -2, 120.00,'Paid',    false},
  new List<Object>{'F','ASC-1006-01',   9, 205.00,'Unpaid',  false},
  new List<Object>{'G','ASC-1007-01', -12, 176.40,'Overdue', false}
};
List<Bill__c> bills = new List<Bill__c>();
for (List<Object> r : rows) {
  Date due = Date.today().addDays((Integer) r[2]);
  bills.add(new Bill__c(Contact__c = byKey.get((String) r[0]).Id, Bill_Number__c = (String) r[1],
      Due_Date__c = due, Bill_Date__c = due.addDays(-21), Amount__c = (Decimal) r[3],
      Status__c = (String) r[4], Extended__c = (Boolean) r[5]));
}
insert bills;
