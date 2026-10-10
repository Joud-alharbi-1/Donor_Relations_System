import json

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.urls import reverse
from django.db.models import Sum, Count, Q
from django.db import IntegrityError
from django.utils import timezone
from django.contrib import messages

from accounts.decorators import donor_required, beneficiary_required
from grants.models import Grant, BeneficiaryCount, GrantItem, ImpactReport, Visit, GrantUpdate
from entities.models import Beneficiary, Donor
from .constants import get_donor_category, get_category_color


def _items_json(grant):
    """يبني قائمة أصناف منحة عينية (GrantItem) بصيغة JSON لعرضها/تحديثها بكارد الأصناف
    دون الحاجة لإعادة تحميل الصفحة بعد الحفظ."""
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


def _reports_json(reports_qs):
    """يبني قائمة تقارير الأثر بصيغة JSON (لعرضها بكارد التقرير)، مع تحديد ما إذا كان الملف PDF
    (قابل للمعاينة داخل الصفحة) أو لا (Word مثلاً)، لعرض بديل مناسب بدل معاينة فارغة."""
    out = []
    for r in reports_qs:
        d = r.report_date or r.created_at.date()
        file_name = r.file.name.rsplit("/", 1)[-1] if r.file else ""
        out.append({
            "id": r.id,
            "label": f"تقرير {d.day}/{d.month}/{d.year}",
            "fileName": file_name,
            "url": r.file.url if r.file else "",
            "isPdf": file_name.lower().endswith(".pdf"),
        })
    return out


@donor_required
def donor_dashboard(request):
    donor = request.donor
    current_year = timezone.now().year
    grants_qs = Grant.objects.filter(donor=donor).select_related("beneficiary").order_by("-grant_date")
    year_total = grants_qs.filter(grant_date__year=current_year).aggregate(total=Sum("amount"))["total"] or 0
    category = get_donor_category(year_total)
    total_amount = grants_qs.aggregate(total=Sum("amount"))["total"] or 0
    total_beneficiaries = BeneficiaryCount.objects.filter(grant__donor=donor).aggregate(total=Sum("count"))["total"] or 0

    category_history = []
    for y in range(current_year, current_year - 5, -1):
        y_total = grants_qs.filter(grant_date__year=y).aggregate(total=Sum("amount"))["total"] or 0
        y_category = get_donor_category(y_total)
        if not y_category:
            continue
        category_history.append({
            "year": y,
            "category": y_category,
            "color": get_category_color(y_category),
        })

    grants_data = []
    for grant in grants_qs:
        reports_qs = grant.reports.filter(stage="official").order_by("-report_date")
        grants_data.append({
            "grant": grant,
            "counts": grant.counts.filter(count__gt=0),
            "visits": grant.visits.all().order_by("visit_date"),
            "news": grant.updates.filter(type="news").order_by("-created_at"),
            "announcements": grant.updates.filter(type="announcement").order_by("-created_at"),
            "reports": reports_qs,
            "reports_json": _reports_json(reports_qs),
            "reports_script_id": f"reports-data-{grant.id}",
        })

    context = {
        "donor": donor, "grants_data": grants_data, "grants_count": grants_qs.count(),
        "total_beneficiaries": total_beneficiaries, "total_amount": total_amount,
        "category": category, "current_year": current_year,
        "donor_contacts": donor.contacts.all(),
        "category_history": category_history,
    }
    return render(request, "portal/donor_dashboard.html", context)


@donor_required
def donor_beneficiaries(request):
    donor = request.donor
    beneficiaries = (
        Beneficiary.objects.filter(grants__donor=donor).distinct()
        .annotate(donor_grants_count=Count("grants", filter=Q(grants__donor=donor), distinct=True))
    )
    beneficiaries_data = []
    for b in beneficiaries:
        total = BeneficiaryCount.objects.filter(grant__donor=donor, grant__beneficiary=b).aggregate(total=Sum("count"))["total"] or 0
        beneficiaries_data.append({"beneficiary": b, "grants_count": b.donor_grants_count, "total_beneficiaries": total})
    return render(request, "portal/donor_beneficiaries.html", {"donor": donor, "beneficiaries_data": beneficiaries_data})


@beneficiary_required
def beneficiary_dashboard(request):
    beneficiary = request.beneficiary

    if request.method == "POST":
        form_type = request.POST.get("form_type")
        grant_id = request.POST.get("grant_id")
        grant = get_object_or_404(Grant, id=grant_id, beneficiary=beneficiary)
        reopen_items = False
        limit_exceeded = False
        duplicate_serial = False
        items_limit = None

        if form_type == "counts":
            # نحذف كل الفئات القديمة ونعيد إنشاء بس اللي أُرسلت من النموذج
            # (يدعم إضافة/حذف فئات ديناميكياً من الواجهة)
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

        elif form_type == "save_items":
            # نحدد إذا الطلب AJAX من البداية: الأخطاء بهالحالة تترجع ضمن الـ JSON نفسه
            # وتُعرض داخل الكرت مباشرة، فما نحتاج (ولا يصح) نضيفها لرسائل Django العامة
            # اللي تظهر ببانر أعلى الصفحة بمعزل عن سياق الكرت.
            is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
            try:
                items_data = json.loads(request.POST.get("items_json", "[]"))
                deleted_ids = json.loads(request.POST.get("deleted_ids_json", "[]"))
            except ValueError:
                items_data, deleted_ids = [], []

            if deleted_ids:
                GrantItem.objects.filter(grant=grant, id__in=deleted_ids).delete()

            items_limit = grant.decision_quantity_count
            if items_limit is not None and len(items_data) > items_limit:
                items_data = items_data[:items_limit]
                limit_exceeded = True
                if not is_ajax:
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
                reopen_items = True
            except IntegrityError:
                duplicate_serial = True
                if not is_ajax:
                    messages.error(request, "duplicate_serial")
                reopen_items = True

            if is_ajax:
                return JsonResponse({
                    "ok": not duplicate_serial,
                    "items": _items_json(grant),
                    "limitExceeded": limit_exceeded,
                    "duplicateSerial": duplicate_serial,
                    "itemsLimit": items_limit,
                })



        elif form_type == "report":
            # ملاحظة: الواجهة تمنع الإرسال بدون ملف قبل ما توصل هنا (تحقق فوري داخل الكرت)،
            # فما نحتاج رسالة Django عامة هنا — لو وصل طلب بدون ملف (تجاوز للتحقق الأمامي) نتجاهله بصمت
            # بدل ما نعرض بانر خطأ بمعزل عن الكرت.
            uploaded_file = request.FILES.get("file")
            new_report_id = None
            if uploaded_file:
                new_report = ImpactReport.objects.create(
                    grant=grant, stage="preliminary",
                    report_date=timezone.now().date(),
                    file=uploaded_file, uploaded_by=request.user,
                )
                new_report_id = new_report.id

        elif form_type == "delete_report":
            report = get_object_or_404(ImpactReport, id=request.POST.get("report_id"), grant=grant, stage="preliminary")
            report.delete()

        url = reverse("beneficiary_dashboard") + f"?open={grant.id}"
        if reopen_items:
            url += "&items=1"
        if form_type == "report" and new_report_id:
            url += f"&uploaded={new_report_id}"
        if form_type == "delete_report":
            url += "&report=1"
        if form_type == "counts":
            url += "&saved=counts"
        if form_type == "save_items":
            url += "&saved=items"
        return redirect(url)


    

    grants_qs = Grant.objects.filter(beneficiary=beneficiary).select_related("donor").order_by("-grant_date")
    total_amount = grants_qs.aggregate(total=Sum("amount"))["total"] or 0
    total_beneficiaries = BeneficiaryCount.objects.filter(grant__beneficiary=beneficiary).aggregate(total=Sum("count"))["total"] or 0

    grants_data = []
    for grant in grants_qs:
        existing = list(grant.counts.all())
        counts_json = [{"value": c.category, "label": c.display_category(), "count": c.count, "other_label": c.other_label} for c in existing]
        reports = grant.reports.filter(stage="preliminary").order_by("-report_date", "-created_at")
        report_years = sorted({(r.report_date or r.created_at.date()).year for r in reports}, reverse=True)
        items_json = _items_json(grant)
        damaged_count = sum(1 for it in grant.items.all() if it.condition == "damaged")
        items_limit = grant.decision_quantity_count
        grants_data.append({
            "grant": grant,
            "items": grant.items.all(),
            "items_json": items_json,
            "items_script_id": f"items-data-{grant.id}",
            "items_limit": items_limit,
            "damaged_count": damaged_count,
            "counts_json": counts_json,
            "script_id": f"counts-data-{grant.id}",
            "reports": reports,
            "reports_json": _reports_json(reports),
            "reports_script_id": f"reports-data-{grant.id}",
            "report_years": report_years,
            "news": grant.updates.filter(type="news").order_by("-created_at"),
            "announcements": grant.updates.filter(type="announcement").order_by("-created_at"),
        })

    all_categories_json = [{"value": v, "label": l} for v, l in BeneficiaryCount.CATEGORY_CHOICES]

    open_grant_id = request.GET.get("open")
    uploaded_report_id = request.GET.get("uploaded")
    open_report_card = request.GET.get("report")
    show_report_card = bool(open_grant_id) and bool(uploaded_report_id or open_report_card)
    show_grant_card = bool(open_grant_id) and not show_report_card

    context = {
        "beneficiary": beneficiary, "grants_data": grants_data, "grants_count": grants_qs.count(),
        "total_beneficiaries": total_beneficiaries, "total_amount": total_amount,
        "all_categories_json": all_categories_json,
        "open_grant_id": open_grant_id,
        "open_items": request.GET.get("items"),
        "uploaded_report_id": uploaded_report_id,
        "show_report_card": show_report_card,
        "show_grant_card": show_grant_card,
        "saved": request.GET.get("saved"),
    }
    return render(request, "portal/beneficiary_dashboard.html", context)


@beneficiary_required
def beneficiary_donors(request):
    beneficiary = request.beneficiary
    current_year = timezone.now().year
    donors = (
        Donor.objects.filter(grants__beneficiary=beneficiary).distinct()
        .annotate(ben_grants_count=Count("grants", filter=Q(grants__beneficiary=beneficiary), distinct=True))
    )
    donors_data = []
    for d in donors:
        year_total = Grant.objects.filter(
            donor=d, beneficiary=beneficiary, grant_date__year=current_year
        ).aggregate(total=Sum("amount"))["total"] or 0
        category = get_donor_category(year_total)
        donors_data.append({
            "donor": d,
            "grants_count": d.ben_grants_count,
            "category": category,
            "category_color": get_category_color(category) if category else None,
        })
    return render(request, "portal/beneficiary_donors.html", {"beneficiary": beneficiary, "donors_data": donors_data})