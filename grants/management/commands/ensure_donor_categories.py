"""
ensure_donor_categories — يتأكد أن كل جهة مانحة لديها فئة (حسب مجموع منحها للسنة الحالية).
لأي جهة مانحة بدون فئة، يضيف لها منحة مالية جديدة واحدة بمبلغ عشوائي ضمن إحدى الفئات
(موزّعة على جهة مستفيدة عشوائية من الجهات الموجودة) — عشان تظهر لها فئة في كل الواجهات.

طريقة التشغيل (من مجلد المشروع):
    python manage.py ensure_donor_categories

يمكن تجربته أولاً بدون أي تعديل فعلي على قاعدة البيانات:
    python manage.py ensure_donor_categories --dry-run
"""
import random
from datetime import date

from django.core.management.base import BaseCommand
from django.utils import timezone

from entities.models import Donor, Beneficiary
from grants.models import Grant
from portal.constants import get_donor_category


# نطاقات مبالغ واقعية لكل فئة (نتجنب "الدرجة الثالثة" لأن مبالغها صغيرة جداً وغير واقعية لعرض تقديمي)
TIER_RANGES = [
    (10_000_000, 15_000_000, "البلاتينية"),
    (5_000_000, 9_999_999, "الألماسية"),
    (2_000_000, 4_999_999, "الذهبية"),
    (1_000_000, 1_999_999, "الفضية"),
    (100_000, 999_999, "البرونزية"),
    (50_000, 99_999, "الدرجة الأولى"),
    (25_000, 49_999, "الدرجة الثانية"),
]


class Command(BaseCommand):
    help = "يضيف منحة جديدة بمبلغ يضمن فئة لكل جهة مانحة ليس لديها فئة في السنة الحالية"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="يعرض فقط الجهات التي ستتأثر دون إنشاء أي منحة فعلياً",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        current_year = timezone.now().year

        beneficiaries = list(Beneficiary.objects.all())
        if not beneficiaries:
            self.stdout.write(self.style.ERROR(
                "لا توجد أي جهة مستفيدة في قاعدة البيانات — أضيفي جهة مستفيدة واحدة على الأقل أولاً ثم أعيدي المحاولة."
            ))
            return

        donors_without_category = []
        for donor in Donor.objects.all():
            year_total = sum(
                (g.amount for g in Grant.objects.filter(donor=donor, grant_date__year=current_year)),
                start=0,
            )
            if not get_donor_category(year_total):
                donors_without_category.append(donor)

        if not donors_without_category:
            self.stdout.write(self.style.SUCCESS("كل الجهات المانحة لديها فئة بالفعل — لا حاجة لإضافة شيء."))
            return

        self.stdout.write(f"عدد الجهات المانحة بدون فئة: {len(donors_without_category)}")

        created = []
        for donor in donors_without_category:
            min_amt, max_amt, tier_name = random.choice(TIER_RANGES)
            amount = random.randint(min_amt, max_amt)
            beneficiary = random.choice(beneficiaries)
            grant_date = date(current_year, random.randint(1, min(8, timezone.now().month)), random.randint(1, 28))

            if not dry_run:
                Grant.objects.create(
                    title_ar=f"دعم مالي لـ{beneficiary.name_ar}",
                    donor=donor,
                    beneficiary=beneficiary,
                    type="financial",
                    amount=amount,
                    grant_date=grant_date,
                    status="ongoing",
                )
            created.append((donor.name_ar, amount, tier_name, beneficiary.name_ar))

        verb = "سيتم إنشاء" if dry_run else "تم إنشاء"
        self.stdout.write(self.style.SUCCESS(f"{verb} {len(created)} منحة جديدة:"))
        for name, amount, tier, ben in created:
            self.stdout.write(f"  - {name}: {amount:,} ﷼ ({tier}) → المستفيد: {ben}")

        if dry_run:
            self.stdout.write(self.style.WARNING("هذا كان عرض تجريبي فقط (--dry-run) — لم يتم حفظ أي شيء في قاعدة البيانات."))
