from datetime import date
from entities.models import Donor, Beneficiary
from grants.models import Grant, BeneficiaryCount, Visit, GrantUpdate

donor_entity = Donor.objects.get(name_ar="جهة مانحة تجريبية")
beneficiary_entity = Beneficiary.objects.get(name_ar="جهة مستفيدة تجريبية")

# منحة 1: دعم مشروع المعمل الإعلامي (عيني)
grant1, _ = Grant.objects.get_or_create(
    title_ar="دعم مشروع المعمل الإعلامي",
    donor=donor_entity,
    beneficiary=beneficiary_entity,
    defaults={
        "type": "in_kind",
        "amount": 100000,
        "grant_date": date(2025, 9, 30),
        "decision_number": "245/2025",
    },
)
BeneficiaryCount.objects.get_or_create(grant=grant1, category="student", defaults={"count": 120})
BeneficiaryCount.objects.get_or_create(grant=grant1, category="faculty", defaults={"count": 8})
Visit.objects.get_or_create(grant=grant1, visit_date=date(2025, 10, 15), defaults={"description": "زيارة تفقدية للمعمل"})
GrantUpdate.objects.get_or_create(
    grant=grant1, type="news",
    title_ar="جامعة الملك عبدالعزيز تُدشّن المعمل الإعلامي بدعم من الجهة المانحة",
    defaults={"link": "https://example.com/news1"},
)

# منحة 2: منحة البحث العلمي المتقدم (مالي)
grant2, _ = Grant.objects.get_or_create(
    title_ar="منحة البحث العلمي المتقدم",
    donor=donor_entity,
    beneficiary=beneficiary_entity,
    defaults={
        "type": "financial",
        "amount": 150000,
        "grant_date": date(2025, 6, 15),
        "decision_number": "310/2025",
    },
)
BeneficiaryCount.objects.get_or_create(grant=grant2, category="researcher", defaults={"count": 40})

print("تم إنشاء بيانات المنح التجريبية بنجاح:")
print(f" - {grant1.title_ar} ({grant1.amount})")
print(f" - {grant2.title_ar} ({grant2.amount})")
