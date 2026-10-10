import json
import re
from decimal import Decimal, InvalidOperation

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.urls import reverse
from django.contrib import messages

from django.db.models import Sum, Max, Count
from django.db import IntegrityError
from django.utils import timezone

from accounts.decorators import manager_required
from entities.models import Donor as DonorModel, Beneficiary as BeneficiaryModel, DonorContact
from grants.models import Grant, BeneficiaryCount, Visit, GrantUpdate, ImpactReport, GrantItem
from portal.constants import get_donor_category

# ── بيانات ثابتة (نفس بيانات data/donors.ts في نسخة React) ─────────────────

STATIC_DONORS = [
    {"id": "jarir", "name": "شركة جرير للتسويق", "category": "البرونزية", "grants": 3,
     "logoUrl": None, "phone": "966112060000", "email": "csr@jarir.com",
     "totalAmount": 300000, "lastGrantDate": "2025-09-30"},
    {"id": "aramco", "name": "مؤسسة أرامكو السعودية", "category": "الذهبية", "grants": 2,
     "logoUrl": None, "phone": "966138720000", "email": "community@aramco.com",
     "totalAmount": 225000, "lastGrantDate": "2025-07-01"},
    {"id": "edu", "name": "وزارة التعليم", "category": "الفضية", "grants": 2,
     "logoUrl": None, "phone": "920002438", "email": "info@moe.gov.sa",
     "totalAmount": 300000, "lastGrantDate": "2025-04-05"},
    {"id": "sabic", "name": "شركة سابك", "category": "الذهبية", "grants": 1,
     "logoUrl": None, "phone": "966112247000", "email": "partnerships@sabic.com",
     "totalAmount": 120000, "lastGrantDate": "2025-01-20"},
    {"id": "ahli", "name": "البنك الأهلي السعودي", "category": "البرونزية", "grants": 1,
     "logoUrl": None, "phone": "920001000", "email": "csr@alahli.com",
     "totalAmount": 250000, "lastGrantDate": "2025-03-01"},
    {"id": "stc", "name": "شركة STC", "category": "الفضية", "grants": 1,
     "logoUrl": None, "phone": "966114424000", "email": "social@stc.com.sa",
     "totalAmount": 180000, "lastGrantDate": "2025-05-10"},
    {"id": "rajhi", "name": "البنك الراجحي", "category": "الدرجة الأولى", "grants": 1,
     "logoUrl": None, "phone": "920003344", "email": "csr@alrajhibank.com.sa",
     "totalAmount": 500000, "lastGrantDate": "2025-08-15"},
    {"id": "mbc", "name": "مجموعة MBC", "category": "الدرجة الثانية", "grants": 1,
     "logoUrl": None, "phone": "966114546000", "email": "media@mbc.net",
     "totalAmount": 90000, "lastGrantDate": "2025-09-01"},
]

CATEGORY_STYLES = {
    "البلاتينية":     {"bg": "bg-slate-100",  "text": "text-slate-600",  "border": "border-slate-300",    "dot": "bg-slate-400"},
    "الألماسية":      {"bg": "bg-sky-50",     "text": "text-sky-600",    "border": "border-sky-300",      "dot": "bg-sky-400"},
    "الذهبية":        {"bg": "bg-amber-50",   "text": "text-amber-600",  "border": "border-amber-300",    "dot": "bg-amber-400"},
    "الفضية":         {"bg": "bg-gray-100",   "text": "text-gray-500",   "border": "border-gray-300",     "dot": "bg-gray-400"},
    "البرونزية":      {"bg": "bg-[#fdf3e7]",  "text": "text-[#8B4513]",  "border": "border-[#CD7F32]/40", "dot": "bg-[#CD7F32]"},
    "الدرجة الأولى":  {"bg": "bg-teal-50",    "text": "text-teal-700",   "border": "border-teal-300",     "dot": "bg-teal-500"},
    "الدرجة الثانية": {"bg": "bg-cyan-50",    "text": "text-cyan-700",   "border": "border-cyan-300",     "dot": "bg-cyan-500"},
    "الدرجة الثالثة": {"bg": "bg-lime-50",    "text": "text-lime-700",   "border": "border-lime-300",     "dot": "bg-lime-500"},
    "جديدة":          {"bg": "bg-[#F3FCF6]",  "text": "text-[#1B8354]",  "border": "border-[#88D8AD]",    "dot": "bg-[#1B8354]"},
}


# ── بيانات ثابتة (نفس بيانات data/grants.ts في نسخة React) ──────────────────

INITIAL_GRANTS = [
    {"id": 1, "title": "دعم مشروع المعمل الإعلامي", "type": "عيني", "donor": "شركة جرير للتسويق",
     "beneficiary": "كلية الاتصال والإعلام", "decisionNumber": "245/2025", "decisionDate": "", "decisionQuantity": "",
     "date": "2025-09-30", "amount": "100,000", "status": "جارية",
     "beneficiaries": [{"type": "طالب/ة", "count": 120}, {"type": "عضو هيئة تدريس", "count": 8}],
     "visits": [
         {"date": "2025-10-15", "purpose": "زيارة تفقدية للمعمل"},
         {"date": "2025-11-20", "purpose": "اجتماع متابعة مع عمادة الكلية"},
     ],
     "news": [
         {"title": "جامعة الملك عبدالعزيز تُدشّن المعمل الإعلامي بدعم من شركة جرير للتسويق", "url": "#"},
         {"title": "طلاب الإعلام يستفيدون من أحدث التقنيات في المعمل الجديد", "url": "#"},
     ],
     "announcements": ["فتح باب التسجيل في دورات المعمل الإعلامي للفصل الدراسي الثاني"],
     "reports": [{"label": "تقرير 15/10/2025", "fileName": "report-oct-2025.pdf"}]},

    {"id": 2, "title": "توقيع أجهزة حاسب آلي", "type": "عيني", "donor": "شركة جرير للتسويق",
     "beneficiary": "كلية الحاسبات وتقنية المعلومات", "decisionNumber": "246/2025", "decisionDate": "", "decisionQuantity": "",
     "date": "2025-09-30", "amount": "200,000", "status": "جارية",
     "beneficiaries": [{"type": "طالب/ة", "count": 340}, {"type": "موظف إداري", "count": 15}],
     "visits": [{"date": "2025-10-05", "purpose": "تسليم الأجهزة ومتابعة التركيب"}],
     "news": [{"title": "كلية الحاسبات تستقبل دفعة من الأجهزة الحديثة بدعم من شركة جرير", "url": "#"}],
     "announcements": [],
     "reports": [{"label": "تقرير 30/9/2025", "fileName": "report-sep-2025.pdf"}]},

    {"id": 3, "title": "منحة البحث العلمي المتقدم", "type": "مالي", "donor": "مؤسسة أرامكو السعودية",
     "beneficiary": "عمادة شؤون الطلاب", "decisionNumber": "310/2025", "decisionDate": "", "decisionQuantity": "",
     "date": "2025-06-15", "amount": "150,000", "status": "منتهية",
     "beneficiaries": [{"type": "باحث", "count": 40}],
     "visits": [], "news": [],
     "announcements": ["سيُعلن عن نتائج البحوث المموّلة في نهاية الفصل الدراسي"],
     "reports": []},

    {"id": 4, "title": "برنامج المنح الدراسية للطلاب المتفوقين", "type": "مالي", "donor": "البنك الأهلي السعودي",
     "beneficiary": "عمادة القبول والتسجيل", "decisionNumber": "088/2025", "decisionDate": "", "decisionQuantity": "",
     "date": "2025-03-01", "amount": "250,000", "status": "منتهية",
     "beneficiaries": [{"type": "طالب/ة متفوق", "count": 75}],
     "visits": [{"date": "2025-03-10", "purpose": "حفل توزيع المنح الدراسية"}],
     "news": [{"title": "البنك الأهلي يمنح 75 طالباً متفوقاً منحة دراسية كاملة", "url": "#"}],
     "announcements": [], "reports": []},

    {"id": 5, "title": "دعم مركز الابتكار والريادة", "type": "مالي", "donor": "شركة STC",
     "beneficiary": "كلية الحاسبات وتقنية المعلومات", "decisionNumber": "352/2025", "decisionDate": "", "decisionQuantity": "",
     "date": "2025-05-10", "amount": "180,000", "status": "جارية",
     "beneficiaries": [{"type": "طالب/ة", "count": 90}],
     "visits": [], "news": [], "announcements": [], "reports": []},

    {"id": 6, "title": "برنامج التدريب التعاوني", "type": "مالي", "donor": "شركة سابك",
     "beneficiary": "عمادة شؤون الطلاب", "decisionNumber": "401/2025", "decisionDate": "", "decisionQuantity": "",
     "date": "2025-01-20", "amount": "120,000", "status": "منتهية",
     "beneficiaries": [{"type": "طالب/ة متدرب", "count": 50}],
     "visits": [{"date": "2025-02-01", "purpose": "زيارة تعريفية للمنشأة"}],
     "news": [], "announcements": [], "reports": []},

    {"id": 7, "title": "منحة تطوير المناهج الدراسية", "type": "مالي", "donor": "وزارة التعليم",
     "beneficiary": "كلية التربية", "decisionNumber": "220/2025", "decisionDate": "", "decisionQuantity": "",
     "date": "2025-04-05", "amount": "300,000", "status": "جارية",
     "beneficiaries": [{"type": "عضو هيئة تدريس", "count": 25}],
     "visits": [],
     "news": [{"title": "وزارة التعليم تدعم تطوير المناهج في جامعة الملك عبدالعزيز", "url": "#"}],
     "announcements": [], "reports": []},

    {"id": 8, "title": "دعم المكتبة الرقمية", "type": "عيني", "donor": "مؤسسة أرامكو السعودية",
     "beneficiary": "عمادة شؤون المكتبات", "decisionNumber": "333/2025", "decisionDate": "", "decisionQuantity": "",
     "date": "2025-07-01", "amount": "75,000", "status": "منتهية",
     "beneficiaries": [{"type": "طالب/ة", "count": 500}],
     "visits": [], "news": [],
     "announcements": ["تم تفعيل الاشتراك في قواعد البيانات العلمية الجديدة"],
     "reports": []},

    {"id": 9, "title": "كرسي الأبحاث المالية", "type": "مالي", "donor": "البنك الراجحي",
     "beneficiary": "كلية الاقتصاد والإدارة", "decisionNumber": "455/2025", "decisionDate": "", "decisionQuantity": "",
     "date": "2025-08-15", "amount": "500,000", "status": "جارية",
     "beneficiaries": [{"type": "باحث", "count": 12}],
     "visits": [{"date": "2025-09-01", "purpose": "الاجتماع التأسيسي للكرسي البحثي"}],
     "news": [{"title": "البنك الراجحي يموّل كرسي الأبحاث المالية في جامعة الملك عبدالعزيز", "url": "#"}],
     "announcements": [], "reports": []},

    {"id": 10, "title": "دعم إنتاج المحتوى الإعلامي", "type": "عيني", "donor": "مجموعة MBC",
     "beneficiary": "كلية الاتصال والإعلام", "decisionNumber": "480/2025", "decisionDate": "", "decisionQuantity": "",
     "date": "2025-09-01", "amount": "90,000", "status": "منتهية",
     "beneficiaries": [{"type": "طالب/ة", "count": 60}],
     "visits": [], "news": [], "announcements": [], "reports": []},
]


def _reports_payload(grant):
    """يبني قائمة تقارير الأثر الحقيقية لمنحة معيّنة (من جدول ImpactReport) لعرضها بكارد التقرير."""
    out = []
    for r in grant.reports.all().order_by("created_at"):
        d = r.report_date or r.created_at.date()
        file_name = r.file.name.rsplit("/", 1)[-1] if r.file else ""
        out.append({
            "id": r.id,
            "label": f"تقرير {d.day}/{d.month}/{d.year}",
            "fileName": file_name,
            "url": r.file.url if r.file else "",
            "stage": r.stage,
            "stageLabel": r.get_stage_display(),
            "isPdf": file_name.lower().endswith(".pdf"),
        })
    return out


def _items_limit(grant):
    """يستخرج الحد الأقصى لعدد الأصناف من حقل عدد قرار قبول المنحة (رقم صرف مخزّن بحقل مستقل الآن)."""
    return grant.decision_quantity_count


def _items_payload(grant):
    """يبني قائمة أصناف منحة عينية (GrantItem) بصيغة JSON لعرضها/تعديلها بكارد تفاصيل المنحة —
    نفس شكل البيانات المستخدم في واجهة المستفيد بالضبط."""
    return [
        {
            "uid": it.id, "id": it.id,
            "item_type": it.item_type, "condition": it.condition,
            "building": it.building, "floor": it.floor, "room": it.room,
            "model": it.model, "serial_number": it.serial_number,
            "attachment_name": (it.attachment.name.rsplit("/", 1)[-1] if it.attachment else ""),
            "attachment_url": (it.attachment.url if it.attachment else ""),
        }
        for it in grant.items.all()
    ]


def _counts_payload(grant):
    """يبني قائمة عدد ونوع المستفيدين لمنحة (BeneficiaryCount) بصيغة JSON — نفس شكل البيانات
    المستخدم في واجهة المستفيد بالضبط (يدعم فئة \"أخرى\" باسم مخصص)."""
    return [
        {"category": c.category, "categoryLabel": c.display_category(), "count": c.count, "other_label": c.other_label}
        for c in grant.counts.all()
    ]


def _save_counts_from_post(request):
    """يحفظ عدد ونوع المستفيدين لمنحة — منقول بنفس المنطق بالضبط من واجهة المستفيد (form_type=counts:
    حذف كل الفئات القديمة وإعادة إنشاء اللي أُرسلت من الواجهة)، مستقل تمامًا عن حفظ بقية بيانات المنحة."""
    grant = get_object_or_404(Grant, id=request.POST.get("grant_id"))
    sent_categories = request.POST.getlist("category")
    sent_values = request.POST.getlist("count_value")
    sent_other_labels = request.POST.getlist("other_label")
    BeneficiaryCount.objects.filter(grant=grant).delete()
    for i, cat in enumerate(sent_categories):
        try:
            val = int(sent_values[i])
        except (ValueError, IndexError):
            val = 0
        other_label = (sent_other_labels[i].strip() if i < len(sent_other_labels) else "")
        if cat:
            BeneficiaryCount.objects.create(
                grant=grant, category=cat, count=val,
                other_label=other_label if cat == "other" else "",
            )
    return grant


def _grant_full_payload(g):
    """يبني القاموس الكامل لمنحة معيّنة (كل الحقول + المستفيدين + الزيارات + الأخبار + الإعلانات + التقارير)
    لعرضها بكارد تفاصيل المنحة القابل للتعديل — نفس الشكل بالضبط بالداشبورد وصفحتي المانح والمستفيد."""
    return {
        "id": g.id,
        "title": g.title_ar,
        "type": g.get_type_display(),
        "donor": g.donor.name_ar,
        "donorId": g.donor_id,
        "beneficiary": g.beneficiary.name_ar,
        "beneficiaryId": g.beneficiary_id,
        "decisionNumber": g.decision_number,
        "decisionDate": g.decision_date.isoformat() if g.decision_date else "",
        "decisionQuantityCount": g.decision_quantity_count,
        "decisionQuantityType": g.decision_quantity_type,
        "date": g.grant_date.isoformat() if g.grant_date else "",
        "amount": "{:,.0f}".format(g.amount),
        "status": g.get_status_display(),
        "beneficiaries": _counts_payload(g),
        "visits": [
            {"date": v.visit_date.isoformat() if v.visit_date else "", "purpose": v.description}
            for v in g.visits.all().order_by("visit_date")
        ],
        "news": [
            {"title": u.title_ar, "url": u.link}
            for u in g.updates.all() if u.type == "news"
        ],
        "announcements": [
            {"text": u.title_ar, "url": u.link}
            for u in g.updates.all() if u.type == "announcement"
        ],
        "reports": _reports_payload(g),
        "items": _items_payload(g),
        "itemsLimit": _items_limit(g),
    }


def _save_grant_from_post(request):
    """يحفظ تعديلات منحة موجودة من نفس نموذج كارد التفاصيل (يشترك فيه الداشبورد وصفحتا المانح والمستفيد)."""
    grant = get_object_or_404(Grant, id=request.POST.get("grant_id"))

    grant.type = "in_kind" if request.POST.get("type") == "عيني" else "financial"
    date_str = request.POST.get("date")
    if date_str:
        grant.grant_date = date_str

    beneficiary_id = request.POST.get("beneficiary_id")
    if beneficiary_id:
        ben = BeneficiaryModel.objects.filter(id=beneficiary_id).first()
        if ben:
            grant.beneficiary = ben

    grant.decision_number = (request.POST.get("decisionNumber") or "").strip()
    decision_date_str = request.POST.get("decisionDate")
    grant.decision_date = decision_date_str or None
    qty_count_raw = (request.POST.get("decisionQuantityCount") or "").strip()
    try:
        grant.decision_quantity_count = int(qty_count_raw) if qty_count_raw else None
    except ValueError:
        grant.decision_quantity_count = None
    grant.decision_quantity_type = (request.POST.get("decisionQuantityType") or "").strip()

    amount_raw = request.POST.get("amount", "")
    cleaned_amount = re.sub(r"[^\d.]", "", amount_raw)
    try:
        grant.amount = Decimal(cleaned_amount) if cleaned_amount else Decimal("0")
    except InvalidOperation:
        grant.amount = Decimal("0")

    grant.status = "ongoing" if request.POST.get("status") == "جارية" else "ended"
    grant.save()

    # الزيارات — حذف وإعادة إنشاء
    try:
        visits_data = json.loads(request.POST.get("visits_json", "[]"))
    except ValueError:
        visits_data = []
    Visit.objects.filter(grant=grant).delete()
    for v in visits_data:
        visit_date = v.get("date")
        if visit_date:
            Visit.objects.create(grant=grant, visit_date=visit_date, description=(v.get("purpose") or "").strip())

    # الأخبار والإعلانات — حذف وإعادة إنشاء
    try:
        news_data = json.loads(request.POST.get("news_json", "[]"))
    except ValueError:
        news_data = []
    try:
        ann_data = json.loads(request.POST.get("announcements_json", "[]"))
    except ValueError:
        ann_data = []
    GrantUpdate.objects.filter(grant=grant).delete()
    for n in news_data:
        title = (n.get("title") or "").strip()
        url = (n.get("url") or "").strip()
        if title and url:
            GrantUpdate.objects.create(grant=grant, type="news", title_ar=title, link=url)
    for a in ann_data:
        text = (a.get("text") or "").strip() if isinstance(a, dict) else ""
        url_a = (a.get("url") or "").strip() if isinstance(a, dict) else ""
        if text and url_a:
            GrantUpdate.objects.create(grant=grant, type="announcement", title_ar=text, link=url_a)

    return grant


def _save_items_from_post(request):
    """يحفظ أصناف منحة عينية — منقول بنفس المنطق بالضبط من واجهة المستفيد (form_type=save_items)،
    مستقل تمامًا عن حفظ بقية بيانات المنحة، ويُستخدم من كارد الأصناف المنفصل."""
    grant = get_object_or_404(Grant, id=request.POST.get("grant_id"))
    try:
        items_data = json.loads(request.POST.get("items_json", "[]"))
        deleted_ids = json.loads(request.POST.get("deleted_ids_json", "[]"))
    except ValueError:
        items_data, deleted_ids = [], []

    if deleted_ids:
        GrantItem.objects.filter(grant=grant, id__in=deleted_ids).delete()

    items_limit = _items_limit(grant)
    if items_limit is not None and len(items_data) > items_limit:
        items_data = items_data[:items_limit]
        messages.error(request, "items_limit_exceeded")

    try:
        for entry in items_data:
            item_id = entry.get("id")
            if item_id:
                gi = get_object_or_404(GrantItem, id=item_id, grant=grant)
            else:
                gi = GrantItem(grant=grant)
            gi.item_type = entry.get("item_type", "")
            gi.building = entry.get("building", "")
            gi.floor = entry.get("floor", "")
            gi.room = entry.get("room", "")
            gi.model = entry.get("model", "")
            gi.serial_number = entry.get("serial_number", "")
            gi.condition = entry.get("condition", "new")
            uploaded_file = request.FILES.get(f"file_{entry.get('uid')}")
            if uploaded_file:
                gi.attachment = uploaded_file
            elif entry.get("clear_attachment"):
                gi.attachment = None
            gi.save()
    except IntegrityError:
        messages.error(request, "duplicate_serial")

    return grant


@manager_required
def upload_grant_report(request, grant_id):
    """يرفع تقرير أثر رسمي لمنحة معيّنة ويحفظه في قاعدة البيانات (جدول ImpactReport)،
    أو يحذفه (يُستخدم لمهلة التراجع بعد الرفع مباشرة — نفس مبدأ واجهة المستفيد)."""
    grant = get_object_or_404(Grant, id=grant_id)
    new_report_id = None
    if request.method == "POST":
        if request.POST.get("action") == "delete":
            report = ImpactReport.objects.filter(
                id=request.POST.get("report_id"), grant=grant, stage="official"
            ).first()
            if report:
                report.delete()
        elif request.FILES.get("file"):
            new_report = ImpactReport.objects.create(
                grant=grant,
                stage="official",
                report_date=timezone.now().date(),
                file=request.FILES["file"],
                uploaded_by=request.user if request.user.is_authenticated else None,
            )
            new_report_id = new_report.id
    next_url = request.POST.get("next") or reverse("dashboard")
    sep = "&" if "?" in next_url else "?"
    url = f"{next_url}{sep}report={grant.id}"
    if new_report_id:
        url += f"&uploaded={new_report_id}"
    return redirect(url)


@manager_required
def dashboard(request):
    """الصفحة الرئيسية (لوحة التحكم): إحصاءات + بحث/فلترة عن المنح + تفاصيل منحة — بيانات حقيقية من قاعدة البيانات."""

    if request.method == "POST" and request.POST.get("form_type") == "save_grant":
        grant = _save_grant_from_post(request)
        return redirect(reverse("dashboard") + f"?open={grant.id}")

    if request.method == "POST" and request.POST.get("form_type") == "save_items":
        grant = _save_items_from_post(request)
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"items": _items_payload(grant), "itemsLimit": _items_limit(grant)})
        return redirect(reverse("dashboard") + f"?open={grant.id}&items=1&saved=items")

    if request.method == "POST" and request.POST.get("form_type") == "save_counts":
        grant = _save_counts_from_post(request)
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"beneficiaries": _counts_payload(grant)})
        return redirect(reverse("dashboard") + f"?open={grant.id}&saved=counts")

    grants_qs = Grant.objects.select_related("donor", "beneficiary").prefetch_related(
        "counts", "visits", "updates"
    ).order_by("-grant_date")

    grants_data = [_grant_full_payload(g) for g in grants_qs]

    context = {
        "initial_grants": grants_data,
        "total_donors": DonorModel.objects.count(),
        "total_beneficiaries": BeneficiaryModel.objects.count(),
        "beneficiaries_list": list(BeneficiaryModel.objects.all().order_by("name_ar").values("id", "name_ar")),
        "beneficiary_categories": BeneficiaryCount.CATEGORY_CHOICES,
        "open_grant_id": request.GET.get("open"),
        "open_report_grant_id": request.GET.get("report"),
        "open_items": request.GET.get("items"),
    }
    return render(request, "admin_panel/dashboard.html", context)


@manager_required
def add_donor(request):
    """صفحة إضافة جهة مانحة جديدة — تُنشئ جهة وجهات تواصلها فعلياً في قاعدة البيانات."""
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        if not name:
            return redirect("add_donor")

        donor = DonorModel.objects.create(name_ar=name, logo=request.FILES.get("logo"))

        try:
            contacts_data = json.loads(request.POST.get("contacts_json", "[]"))
        except ValueError:
            contacts_data = []
        for c in contacts_data:
            contact_name = (c.get("name") or "").strip()
            position = (c.get("title") or "").strip()
            email = (c.get("email") or "").strip()
            phone = (c.get("phone") or "").strip()
            if contact_name or position or email or phone:
                DonorContact.objects.create(donor=donor, name=contact_name, position=position, email=email, phone=phone)

        return redirect("donor_portal", donor_id=donor.id)

    return render(request, "admin_panel/add_donor.html")


@manager_required
def donor_management(request):
    """صفحة إدارة الجهات المانحة (بحث + فلاتر + قائمة الجهات) — بيانات حقيقية من قاعدة البيانات."""
    current_year = timezone.now().year
    donors_qs = DonorModel.objects.all().order_by("name_ar")

    donors_data = []
    for d in donors_qs:
        grants_qs = Grant.objects.filter(donor=d)
        total_amount = grants_qs.aggregate(total=Sum("amount"))["total"] or 0
        year_total = grants_qs.filter(grant_date__year=current_year).aggregate(total=Sum("amount"))["total"] or 0
        last_grant = grants_qs.aggregate(last=Max("grant_date"))["last"]
        first_contact = d.contacts.first()
        donors_data.append({
            "id": d.id,
            "name": d.name_ar,
            "category": get_donor_category(year_total),
            "grants": grants_qs.count(),
            "logoUrl": d.logo.url if d.logo else None,
            "totalAmount": float(total_amount),
            "lastGrantDate": last_grant.isoformat() if last_grant else None,
            "email": first_contact.email if first_contact else None,
        })

    context = {
        "donors_data": donors_data,
        "category_styles": CATEGORY_STYLES,
    }
    return render(request, "admin_panel/donor_management.html", context)


# ── بيانات ثابتة (نفس بيانات data/beneficiaries.ts في نسخة React) ──────────

BENEFICIARIES = [
    {"id": "cs", "name": "كلية الحاسبات وتقنية المعلومات", "initial": "ح", "email": "cis@kau.edu.sa",
     "grants": [
         {"id": 1, "title": "توقيع أجهزة حاسب آلي", "type": "عيني", "donor": "شركة جرير للتسويق", "amount": "200,000", "date": "30/9/2025", "beneficiaryCount": 340, "beneficiaryType": "طالب/ة", "status": "جارية"},
         {"id": 2, "title": "منحة البحث العلمي المتقدم", "type": "مالي", "donor": "مؤسسة أرامكو السعودية", "amount": "150,000", "date": "15/6/2025", "beneficiaryCount": 40, "beneficiaryType": "باحث", "status": "منتهية"},
     ]},
    {"id": "econ", "name": "كلية الاقتصاد والإدارة", "initial": "ا", "email": "econ@kau.edu.sa",
     "grants": [
         {"id": 3, "title": "دعم مركز ريادة الأعمال", "type": "مالي", "donor": "البنك الأهلي السعودي", "amount": "300,000", "date": "1/4/2025", "beneficiaryCount": 180, "beneficiaryType": "طالب/ة", "status": "جارية"},
     ]},
    {"id": "hospital", "name": "المستشفى الجامعي", "initial": "م", "email": "hospital@kau.edu.sa",
     "grants": [
         {"id": 4, "title": "تجهيز وحدة العناية المركزة", "type": "عيني", "donor": "مجموعة مستشفيات السعودي الألماني", "amount": "500,000", "date": "10/3/2025", "beneficiaryCount": 220, "beneficiaryType": "مريض/ة", "status": "منتهية"},
         {"id": 5, "title": "برنامج التدريب الطبي", "type": "مالي", "donor": "وزارة الصحة", "amount": "120,000", "date": "5/5/2025", "beneficiaryCount": 60, "beneficiaryType": "طبيب متدرب", "status": "جارية"},
     ]},
    {"id": "media", "name": "كلية الاتصال والإعلام", "initial": "إ",
     "grants": [
         {"id": 6, "title": "دعم مشروع المعمل الإعلامي", "type": "عيني", "donor": "شركة جرير للتسويق", "amount": "100,000", "date": "30/9/2025", "beneficiaryCount": 120, "beneficiaryType": "طالب/ة", "status": "جارية"},
     ]},
    {"id": "eng", "name": "كلية الهندسة", "initial": "هـ",
     "grants": [
         {"id": 7, "title": "مختبر الطباعة ثلاثية الأبعاد", "type": "عيني", "donor": "شركة سابك", "amount": "400,000", "date": "20/2/2025", "beneficiaryCount": 290, "beneficiaryType": "طالب/ة", "status": "جارية"},
         {"id": 8, "title": "منحة مشاريع التخرج", "type": "مالي", "donor": "أرامكو السعودية", "amount": "80,000", "date": "1/9/2025", "beneficiaryCount": 75, "beneficiaryType": "طالب/ة", "status": "منتهية"},
     ]},
    {"id": "design", "name": "كلية علوم الإنسان والتصاميم", "initial": "ت",
     "grants": [
         {"id": 9, "title": "ورش التصميم الإبداعي", "type": "مالي", "donor": "مجموعة MBC", "amount": "60,000", "date": "12/7/2025", "beneficiaryCount": 95, "beneficiaryType": "طالب/ة", "status": "منتهية"},
     ]},
    {"id": "students", "name": "عمادة شؤون الطلاب", "initial": "ش",
     "grants": [
         {"id": 10, "title": "برنامج تطوير الكفاءات الأكاديمية", "type": "مالي", "donor": "وزارة التعليم", "amount": "250,000", "date": "1/3/2025", "beneficiaryCount": 500, "beneficiaryType": "طالب/ة", "status": "جارية"},
         {"id": 11, "title": "دعم الأنشطة الطلابية", "type": "مالي", "donor": "البنك الراجحي", "amount": "45,000", "date": "15/8/2025", "beneficiaryCount": 200, "beneficiaryType": "طالب/ة", "status": "منتهية"},
     ]},
    {"id": "admissions", "name": "عمادة القبول والتسجيل", "initial": "ق",
     "grants": [
         {"id": 12, "title": "تطوير منظومة القبول الإلكتروني", "type": "مالي", "donor": "شركة STC", "amount": "180,000", "date": "7/6/2025", "beneficiaryCount": 1200, "beneficiaryType": "طالب/ة", "status": "جارية"},
     ]},
]


@manager_required
def donor_portal(request, donor_id):
    """صفحة تفاصيل جهة مانحة واحدة (بيانات الجهة + جهات التواصل + منحها) — بيانات حقيقية من قاعدة البيانات."""
    donor = get_object_or_404(DonorModel, id=donor_id)

    if request.method == "POST" and request.POST.get("form_type") == "save_donor":
        name = (request.POST.get("name") or "").strip()
        if name:
            donor.name_ar = name
        if request.FILES.get("logo"):
            donor.logo = request.FILES["logo"]
        donor.save()

        try:
            contacts_data = json.loads(request.POST.get("contacts_json", "[]"))
        except ValueError:
            contacts_data = []
        DonorContact.objects.filter(donor=donor).delete()
        for c in contacts_data:
            contact_name = (c.get("name") or "").strip()
            position = (c.get("title") or "").strip()
            email = (c.get("email") or "").strip()
            phone = (c.get("phone") or "").strip()
            if contact_name or position or email or phone:
                DonorContact.objects.create(donor=donor, name=contact_name, position=position, email=email, phone=phone)

        return redirect("donor_portal", donor_id=donor.id)

    if request.method == "POST" and request.POST.get("form_type") == "save_grant":
        grant = _save_grant_from_post(request)
        return redirect(reverse("donor_portal", kwargs={"donor_id": donor.id}) + f"?open={grant.id}")

    if request.method == "POST" and request.POST.get("form_type") == "save_items":
        grant = _save_items_from_post(request)
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"items": _items_payload(grant), "itemsLimit": _items_limit(grant)})
        return redirect(reverse("donor_portal", kwargs={"donor_id": donor.id}) + f"?open={grant.id}&items=1&saved=items")

    if request.method == "POST" and request.POST.get("form_type") == "save_counts":
        grant = _save_counts_from_post(request)
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"beneficiaries": _counts_payload(grant)})
        return redirect(reverse("donor_portal", kwargs={"donor_id": donor.id}) + f"?open={grant.id}&saved=counts")

    current_year = timezone.now().year
    grants_qs = Grant.objects.filter(donor=donor).select_related("beneficiary").order_by("-grant_date")
    year_total = grants_qs.filter(grant_date__year=current_year).aggregate(total=Sum("amount"))["total"] or 0
    total_beneficiaries = BeneficiaryCount.objects.filter(grant__donor=donor).aggregate(total=Sum("count"))["total"] or 0

    category_history = []
    for y in range(current_year, current_year - 5, -1):
        y_total = grants_qs.filter(grant_date__year=y).aggregate(total=Sum("amount"))["total"] or 0
        y_category = get_donor_category(y_total)
        if y_category:
            category_history.append({"year": y, "category": y_category})

    grants_data = [_grant_full_payload(g) for g in grants_qs]

    context = {
        "donor_info": {
            "id": donor.id,
            "name": donor.name_ar,
            "logoUrl": donor.logo.url if donor.logo else None,
            "category": get_donor_category(year_total),
            "contacts": [
                {"name": c.name, "title": c.position, "email": c.email, "phone": c.phone}
                for c in donor.contacts.all()
            ],
        },
        "category_styles": CATEGORY_STYLES,
        "category_history": category_history,
        "grants_data": grants_data,
        "total_beneficiaries": total_beneficiaries,
        "beneficiaries_list": list(BeneficiaryModel.objects.all().order_by("name_ar").values("id", "name_ar")),
        "beneficiary_categories": BeneficiaryCount.CATEGORY_CHOICES,
        "open_grant_id": request.GET.get("open"),
        "open_report_grant_id": request.GET.get("report"),
        "open_items": request.GET.get("items"),
    }
    return render(request, "admin_panel/donor_portal.html", context)


@manager_required
def beneficiary_management(request):
    """صفحة إدارة الجهات المستفيدة (بحث + ترتيب + قائمة الجهات) — بيانات حقيقية من قاعدة البيانات."""
    beneficiaries_qs = BeneficiaryModel.objects.all().order_by("name_ar")
    beneficiaries_data = []
    for b in beneficiaries_qs:
        grants_qs = Grant.objects.filter(beneficiary=b)
        total_amount = grants_qs.aggregate(total=Sum("amount"))["total"] or 0
        total_beneficiaries = BeneficiaryCount.objects.filter(grant__beneficiary=b).aggregate(total=Sum("count"))["total"] or 0
        last_grant = grants_qs.aggregate(last=Max("grant_date"))["last"]
        beneficiaries_data.append({
            "id": b.id,
            "name": b.name_ar,
            "grantsCount": grants_qs.count(),
            "totalAmount": float(total_amount),
            "totalBeneficiaries": total_beneficiaries,
            "lastGrantDate": last_grant.isoformat() if last_grant else None,
        })
    context = {"beneficiaries_data": beneficiaries_data}
    return render(request, "admin_panel/beneficiary_management.html", context)


# ── بيانات ثابتة (نفس بيانات BeneficiaryPortal.tsx في نسخة React) ──────────

ITEMS_FOR_CS = [
    {"name": "جهاز حاسب آلي", "condition": "جيد", "building": "مبنى أ", "floor": "الدور الثاني", "room": "معمل 201", "model": "Dell OptiPlex 7090", "serial": "SN-00142", "attachment": {"name": "صورة_الجهاز.pdf", "url": "#"}},
    {"name": "جهاز حاسب آلي", "condition": "جيد", "building": "مبنى أ", "floor": "الدور الثاني", "room": "معمل 201", "model": "Dell OptiPlex 7090", "serial": "SN-00143", "attachment": None},
    {"name": "جهاز حاسب آلي", "condition": "تالف", "building": "مبنى ب", "floor": "الدور الأول", "room": "غرفة 105", "model": "Dell OptiPlex 7090", "serial": "SN-00144", "attachment": None},
    {"name": "شاشة عرض", "condition": "جيد", "building": "مبنى أ", "floor": "الدور الثاني", "room": "معمل 201", "model": 'Samsung 24"', "serial": "SN-00201", "attachment": None},
    {"name": "شاشة عرض", "condition": "جيد", "building": "مبنى أ", "floor": "الدور الثاني", "room": "معمل 202", "model": 'Samsung 24"', "serial": "SN-00202", "attachment": None},
]


@manager_required
def beneficiary_portal(request, beneficiary_id):
    """صفحة تفاصيل جهة مستفيدة واحدة (بيانات الجهة + منحها) — بيانات حقيقية من قاعدة البيانات."""
    beneficiary = get_object_or_404(BeneficiaryModel, id=beneficiary_id)

    if request.method == "POST" and request.POST.get("form_type") == "save_beneficiary":
        name = (request.POST.get("name") or "").strip()
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
        if name:
            beneficiary.name_ar = name
            beneficiary.save()
            if is_ajax:
                return JsonResponse({"success": True, "name": beneficiary.name_ar})
            return redirect("beneficiary_portal", beneficiary_id=beneficiary.id)
        if is_ajax:
            return JsonResponse({"success": False, "error": "الاسم مطلوب"})
        return redirect("beneficiary_portal", beneficiary_id=beneficiary.id)

    if request.method == "POST" and request.POST.get("form_type") == "save_grant":
        grant = _save_grant_from_post(request)
        return redirect(reverse("beneficiary_portal", kwargs={"beneficiary_id": beneficiary.id}) + f"?open={grant.id}")

    if request.method == "POST" and request.POST.get("form_type") == "save_items":
        grant = _save_items_from_post(request)
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"items": _items_payload(grant), "itemsLimit": _items_limit(grant)})
        return redirect(reverse("beneficiary_portal", kwargs={"beneficiary_id": beneficiary.id}) + f"?open={grant.id}&items=1&saved=items")

    if request.method == "POST" and request.POST.get("form_type") == "save_counts":
        grant = _save_counts_from_post(request)
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"beneficiaries": _counts_payload(grant)})
        return redirect(reverse("beneficiary_portal", kwargs={"beneficiary_id": beneficiary.id}) + f"?open={grant.id}&saved=counts")

    grants_qs = Grant.objects.filter(beneficiary=beneficiary).select_related("donor").order_by("-grant_date")
    total_beneficiaries = BeneficiaryCount.objects.filter(grant__beneficiary=beneficiary).aggregate(total=Sum("count"))["total"] or 0

    grants_data = [_grant_full_payload(g) for g in grants_qs]

    context = {
        "beneficiary_info": {"id": beneficiary.id, "name": beneficiary.name_ar},
        "grants_data": grants_data,
        "total_beneficiaries": total_beneficiaries,
        "beneficiaries_list": list(BeneficiaryModel.objects.all().order_by("name_ar").values("id", "name_ar")),
        "beneficiary_categories": BeneficiaryCount.CATEGORY_CHOICES,
        "open_grant_id": request.GET.get("open"),
        "open_report_grant_id": request.GET.get("report"),
        "open_items": request.GET.get("items"),
    }
    return render(request, "admin_panel/beneficiary_portal.html", context)


# ── بيانات ثابتة (نفس بيانات GrantManagement.tsx في نسخة React) ────────────

GRANT_FORM_DONORS = [
    "شركة جرير للتسويق",
    "مؤسسة أرامكو السعودية",
    "وزارة التعليم",
    "شركة سابك",
    "البنك الأهلي السعودي",
    "شركة STC",
    "البنك الراجحي",
    "مجموعة MBC",
]

GRANT_FORM_BENEFICIARIES = [
    "كلية الحاسبات وتقنية المعلومات",
    "كلية الاقتصاد والإدارة",
    "المستشفى الجامعي",
    "كلية الاتصال والإعلام",
    "كلية الهندسة",
    "كلية العلوم الإنسانية والاجتماعية",
    "عمادة شؤون الطلاب",
    "عمادة القبول والتسجيل",
]


@manager_required
def grant_management(request):
    """صفحة إضافة منحة جديدة (بيانات المنحة، المستفيدين، الزيارات، الأخبار، الإعلانات) — حفظ فعلي في قاعدة البيانات."""
    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        donor_id = request.POST.get("donor_id")
        donor_other = (request.POST.get("donor_other") or "").strip()
        beneficiary_id = request.POST.get("beneficiary_id")

        if not title or not beneficiary_id or not donor_id or (donor_id == "__other__" and not donor_other):
            messages.error(request, "بيانات المنحة الأساسية ناقصة")
            return redirect("grant_management")

        if donor_id == "__other__":
            donor = DonorModel.objects.create(name_ar=donor_other)
        else:
            donor = get_object_or_404(DonorModel, id=donor_id)
        beneficiary = get_object_or_404(BeneficiaryModel, id=beneficiary_id)

        amount_raw = request.POST.get("amount", "")
        cleaned_amount = re.sub(r"[^\d.]", "", amount_raw)
        try:
            amount = Decimal(cleaned_amount) if cleaned_amount else Decimal("0")
        except InvalidOperation:
            amount = Decimal("0")

        qty_count_raw = (request.POST.get("decisionQuantityCount") or "").strip()
        try:
            qty_count = int(qty_count_raw) if qty_count_raw else None
        except ValueError:
            qty_count = None

        grant = Grant.objects.create(
            title_ar=title,
            donor=donor,
            beneficiary=beneficiary,
            type="in_kind" if request.POST.get("type") == "عيني" else "financial",
            amount=amount,
            grant_date=request.POST.get("date") or timezone.now().date(),
            status="ongoing" if request.POST.get("status") == "جارية" else "ended",
            decision_number=(request.POST.get("decisionNumber") or "").strip(),
            decision_date=request.POST.get("decisionDate") or None,
            decision_quantity_count=qty_count,
            decision_quantity_type=(request.POST.get("decisionQuantityType") or "").strip(),
        )

        try:
            counts_data = json.loads(request.POST.get("counts_json", "[]"))
        except ValueError:
            counts_data = []
        seen_categories = set()
        for c in counts_data:
            category = c.get("category")
            if not category or category in seen_categories:
                continue
            seen_categories.add(category)
            try:
                count_value = int(c.get("count") or 0)
            except (TypeError, ValueError):
                count_value = 0
            if count_value > 0:
                other_label = (c.get("other_label") or "").strip()
                BeneficiaryCount.objects.create(
                    grant=grant, category=category, count=count_value,
                    other_label=other_label if category == "other" else "",
                )

        try:
            visits_data = json.loads(request.POST.get("visits_json", "[]"))
        except ValueError:
            visits_data = []
        for v in visits_data:
            if v.get("date"):
                Visit.objects.create(grant=grant, visit_date=v["date"], description=(v.get("purpose") or "").strip())

        try:
            news_data = json.loads(request.POST.get("news_json", "[]"))
        except ValueError:
            news_data = []
        try:
            ann_data = json.loads(request.POST.get("announcements_json", "[]"))
        except ValueError:
            ann_data = []
        for n in news_data:
            title_n = (n.get("title") or "").strip()
            url_n = (n.get("url") or "").strip()
            if title_n and url_n:
                GrantUpdate.objects.create(grant=grant, type="news", title_ar=title_n, link=url_n)
        for a in ann_data:
            text_a = (a.get("text") or "").strip() if isinstance(a, dict) else ""
            url_a = (a.get("url") or "").strip() if isinstance(a, dict) else ""
            if text_a and url_a:
                GrantUpdate.objects.create(grant=grant, type="announcement", title_ar=text_a, link=url_a)

        return redirect(reverse("dashboard") + f"?open={grant.id}")

    context = {
        "donors_list": list(DonorModel.objects.all().order_by("name_ar").values("id", "name_ar")),
        "beneficiaries_list": list(BeneficiaryModel.objects.all().order_by("name_ar").values("id", "name_ar")),
        "beneficiary_categories": BeneficiaryCount.CATEGORY_CHOICES,
    }
    return render(request, "admin_panel/grant_management.html", context)
