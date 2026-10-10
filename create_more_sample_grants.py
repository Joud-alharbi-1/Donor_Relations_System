"""
create_more_sample_grants.py — بيانات تجريبية إضافية بأسماء وأرقام واقعية
لاختبار لوحة الإداري (البحث، الفلترة، التعديل والحفظ، الحالة، القرار، المستفيدون، الزيارات، الأخبار، الإعلانات).
آمن للتشغيل أكثر من مرة (يستخدم get_or_create في كل مكان).
"""
from datetime import date
from entities.models import Donor, Beneficiary
from grants.models import Grant, BeneficiaryCount, Visit, GrantUpdate

# ── الجهات المانحة ────────────────────────────────────────────────────────
donors = {}
for name in [
    "شركة جرير للتسويق",
    "مؤسسة أرامكو السعودية",
    "شركة سابك",
    "البنك الأهلي السعودي",
    "شركة الاتصالات السعودية STC",
    "بنك الراجحي",
]:
    donors[name], _ = Donor.objects.get_or_create(name_ar=name)

# ── الجهات المستفيدة ──────────────────────────────────────────────────────
beneficiaries = {}
for name, btype in [
    ("كلية الحاسبات وتقنية المعلومات", "college"),
    ("كلية الاقتصاد والإدارة", "college"),
    ("المستشفى الجامعي", "hospital"),
    ("كلية الاتصال والإعلام", "college"),
    ("عمادة شؤون الطلاب", "deanship"),
    ("عمادة القبول والتسجيل", "deanship"),
]:
    beneficiaries[name], _ = Beneficiary.objects.get_or_create(name_ar=name, defaults={"type": btype})

# ── المنح ──────────────────────────────────────────────────────────────
grants_data = [
    dict(
        title_ar="توقيع أجهزة حاسب آلي لمعامل الكلية",
        donor="شركة جرير للتسويق", beneficiary="كلية الحاسبات وتقنية المعلومات",
        type="in_kind", amount=200000, grant_date=date(2025, 9, 30), status="ongoing",
        decision_number="246/2025", decision_date=date(2025, 9, 20), decision_quantity_count=150, decision_quantity_type="جهاز",
        counts=[("student", 340), ("staff", 15)],
        visits=[(date(2025, 10, 5), "تسليم الأجهزة ومتابعة التركيب")],
        news=[("كلية الحاسبات تستقبل دفعة من الأجهزة الحديثة بدعم من شركة جرير", "https://example.com/news-jarir-cs")],
        announcements=["فتح باب التسجيل في معامل الحاسب المطوّرة للفصل الدراسي القادم"],
    ),
    dict(
        title_ar="منحة البحث العلمي المتقدم",
        donor="مؤسسة أرامكو السعودية", beneficiary="عمادة شؤون الطلاب",
        type="financial", amount=150000, grant_date=date(2025, 6, 15), status="ended",
        decision_number="310/2025", decision_date=date(2025, 6, 1), decision_quantity_count=None, decision_quantity_type="",
        counts=[("researcher", 40)],
        visits=[],
        news=[],
        announcements=["سيُعلن عن نتائج البحوث المموّلة في نهاية الفصل الدراسي"],
    ),
    dict(
        title_ar="برنامج المنح الدراسية للطلاب المتفوقين",
        donor="البنك الأهلي السعودي", beneficiary="عمادة القبول والتسجيل",
        type="financial", amount=250000, grant_date=date(2025, 3, 1), status="ongoing",
        decision_number="088/2025", decision_date=date(2025, 2, 20), decision_quantity_count=None, decision_quantity_type="",
        counts=[("student", 75)],
        visits=[(date(2025, 3, 10), "حفل توزيع المنح الدراسية")],
        news=[("البنك الأهلي يمنح 75 طالباً متفوقاً منحة دراسية كاملة", "https://example.com/news-ahli-scholarships")],
        announcements=[],
    ),
    dict(
        title_ar="دعم مركز الابتكار والريادة",
        donor="شركة الاتصالات السعودية STC", beneficiary="كلية الحاسبات وتقنية المعلومات",
        type="financial", amount=180000, grant_date=date(2025, 5, 10), status="ongoing",
        decision_number="352/2025", decision_date=date(2025, 5, 1), decision_quantity_count=None, decision_quantity_type="",
        counts=[("student", 90), ("faculty", 6)],
        visits=[],
        news=[],
        announcements=[],
    ),
    dict(
        title_ar="برنامج التدريب التعاوني",
        donor="شركة سابك", beneficiary="عمادة شؤون الطلاب",
        type="financial", amount=120000, grant_date=date(2025, 1, 20), status="ended",
        decision_number="401/2025", decision_date=date(2025, 1, 10), decision_quantity_count=None, decision_quantity_type="",
        counts=[("student", 50)],
        visits=[(date(2025, 2, 1), "زيارة تعريفية للمنشأة")],
        news=[],
        announcements=[],
    ),
    dict(
        title_ar="كرسي الأبحاث المالية",
        donor="بنك الراجحي", beneficiary="كلية الاقتصاد والإدارة",
        type="financial", amount=500000, grant_date=date(2025, 8, 15), status="ongoing",
        decision_number="455/2025", decision_date=date(2025, 8, 1), decision_quantity_count=None, decision_quantity_type="",
        counts=[("researcher", 12), ("faculty", 4)],
        visits=[(date(2025, 9, 1), "الاجتماع التأسيسي للكرسي البحثي")],
        news=[("بنك الراجحي يموّل كرسي الأبحاث المالية في جامعة الملك عبدالعزيز", "https://example.com/news-rajhi-chair")],
        announcements=[],
    ),
    dict(
        title_ar="تجهيز وحدة العناية المركزة",
        donor="مؤسسة أرامكو السعودية", beneficiary="المستشفى الجامعي",
        type="in_kind", amount=500000, grant_date=date(2025, 3, 10), status="ended",
        decision_number="512/2025", decision_date=date(2025, 2, 25), decision_quantity_count=30, decision_quantity_type="جهاز طبي",
        counts=[("patient", 220), ("staff", 25)],
        visits=[(date(2025, 3, 20), "تسليم الأجهزة الطبية وتشغيلها")],
        news=[("أرامكو تدعم تجهيز وحدة العناية المركزة بالمستشفى الجامعي", "https://example.com/news-aramco-icu")],
        announcements=["بدء تشغيل الوحدة رسمياً اعتباراً من الفصل القادم"],
    ),
    dict(
        title_ar="دعم إنتاج المحتوى الإعلامي الطلابي",
        donor="شركة جرير للتسويق", beneficiary="كلية الاتصال والإعلام",
        type="in_kind", amount=90000, grant_date=date(2025, 9, 1), status="ongoing",
        decision_number="480/2025", decision_date=date(2025, 8, 20), decision_quantity_count=None, decision_quantity_type="كاميرات ومعدات إضاءة",
        counts=[("student", 60)],
        visits=[],
        news=[],
        announcements=["ورشة تدريبية على المعدات الجديدة الأسبوع القادم"],
    ),
]

created = []
for g in grants_data:
    grant, _ = Grant.objects.get_or_create(
        title_ar=g["title_ar"],
        donor=donors[g["donor"]],
        beneficiary=beneficiaries[g["beneficiary"]],
        defaults={
            "type": g["type"],
            "amount": g["amount"],
            "grant_date": g["grant_date"],
            "status": g["status"],
            "decision_number": g["decision_number"],
            "decision_date": g["decision_date"],
            "decision_quantity_count": g["decision_quantity_count"],
            "decision_quantity_type": g["decision_quantity_type"],
        },
    )
    for category, count in g["counts"]:
        BeneficiaryCount.objects.get_or_create(grant=grant, category=category, defaults={"count": count})
    for visit_date, description in g["visits"]:
        Visit.objects.get_or_create(grant=grant, visit_date=visit_date, defaults={"description": description})
    for title, link in g["news"]:
        GrantUpdate.objects.get_or_create(grant=grant, type="news", title_ar=title, defaults={"link": link})
    for text in g["announcements"]:
        GrantUpdate.objects.get_or_create(grant=grant, type="announcement", title_ar=text, defaults={"link": ""})
    created.append(grant)

print(f"تم إنشاء/تحديث {len(created)} منحة تجريبية بنجاح:")
for grant in created:
    print(f" - {grant.title_ar} — {grant.donor.name_ar} → {grant.beneficiary.name_ar} ({grant.amount} ﷼, {grant.get_status_display()})")
