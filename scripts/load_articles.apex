// Ascend Energy V8 knowledge articles (text from notes/knowledge-articles.md). Re-run safe: skips existing URL names.
Map<String, List<String>> arts = new Map<String, List<String>>{
 'payment-options' => new List<String>{
   'Payment options',
   'How to pay your bill, and what to do if you need more time.',
   'How can I pay my bill, or get more time to pay?',
   '<p>You can pay your Ascend Energy bill in full at any time before the due date shown on your bill.</p>'
   + '<p><b>If you need more time to pay</b></p><ul>'
   + '<li>We can move the due date of your latest bill by 7 days.</li>'
   + '<li>This can be done once per bill.</li>'
   + '<li>We cannot extend a bill that has already been paid.</li>'
   + '<li>We cannot extend a bill that has already been extended.</li>'
   + '<li>We cannot extend a bill that is more than 30 days past its due date. A team member will review it with you instead.</li>'
   + '<li>If your new due date has also passed, please pay as soon as you can.</li></ul>'
   + '<p><b>What an extension does not do</b></p><ul>'
   + '<li>It does not remove or reduce any late fee. See the Late fee policy.</li>'
   + '<li>It does not set up a payment plan or split the bill into instalments. A team member can help with this.</li></ul>'
   + '<p><b>Other ways to get help with a bill</b></p>'
   + '<p>If you cannot pay even with an extension, a team member can talk through other options with you.</p>'},
 'late-fee-policy' => new List<String>{
   'Late fee policy',
   'When a late fee can be added, and what we can and cannot do about it.',
   'Can you remove a late fee?',
   '<p><b>When a late fee is added</b></p>'
   + '<p>A late fee can be added to a bill that is not paid by its due date.</p>'
   + '<p><b>What the virtual assistant can and cannot do</b></p><ul>'
   + '<li>It cannot waive, reduce or reverse a late fee or any other charge.</li>'
   + '<li>It cannot promise that a fee will be removed.</li>'
   + '<li>It can explain this policy.</li>'
   + '<li>If you believe a fee is wrong, it can log your request so a team member reviews it. You will be given a case number.</li></ul>'
   + '<p><b>Extensions and late fees</b></p>'
   + '<p>An extension gives you more time to pay your bill. It does not remove a late fee that has already been added.</p>'
   + '<p><b>Bills more than 30 days overdue</b></p>'
   + '<p>These bills cannot be extended. A team member will contact you about them.</p>'},
 'power-outage-guidance' => new List<String>{
   'Power outage guidance',
   'What to do during a power outage, and what to do if someone at home depends on medical equipment.',
   'What should I do during a power outage?',
   '<p><b>If your power goes out</b></p><ol>'
   + '<li>Check whether your neighbours also have no power. If they do, the outage is probably in your area.</li>'
   + '<li>Switch off or unplug sensitive electrical equipment, such as computers and televisions. This protects it when the power comes back.</li>'
   + '<li>Keep fridge and freezer doors closed to keep food cold for longer.</li>'
   + '<li>Use torches or battery lights. Do not use candles.</li>'
   + '<li>Keep away from any fallen or damaged power lines. Treat them as live and call the emergency services.</li></ol>'
   + '<p><b>If someone at home uses medical equipment that needs power</b></p><ul>'
   + '<li>Tell us immediately. We will treat your report as a priority and pass it to a team member.</li>'
   + '<li>Keep a backup plan ready, such as a charged battery or somewhere else you can go.</li>'
   + '<li>If anyone\'s health is at risk, call the emergency services first.</li></ul>'
   + '<p><b>What we cannot promise</b></p>'
   + '<p>We cannot promise when your power will be restored. Outages can be unpredictable.</p>'}
};
Set<String> existing = new Set<String>();
for (Knowledge__kav k : [SELECT UrlName FROM Knowledge__kav WHERE UrlName IN :arts.keySet()]) existing.add(k.UrlName);
List<Knowledge__kav> toInsert = new List<Knowledge__kav>();
for (String url : arts.keySet()) {
  if (existing.contains(url)) continue;
  List<String> a = arts.get(url);
  toInsert.add(new Knowledge__kav(Title = a[0], UrlName = url, Summary = a[1], FAQ_Question__c = a[2], FAQ_Answer__c = a[3],
      Language = 'en_US', IsVisibleInCsp = true, IsVisibleInPkb = true));
}
insert toInsert;
for (Knowledge__kav k : [SELECT KnowledgeArticleId FROM Knowledge__kav WHERE Id IN :toInsert]) {
  KbManagement.PublishingService.publishArticle(k.KnowledgeArticleId, true);
}
