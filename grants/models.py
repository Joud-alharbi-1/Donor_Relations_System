from django.db import models
from django.conf import settings
from entities.models import Donor, Beneficiary


# Create your models here.
class Grant(models.Model):


    TYPE_CHOICES = [
        ('financial', 'مالي'),
        ('in_kind', 'عيني'),
    ]
    STATUS_CHOICES = [
        ('ongoing', 'جارية'),
        ('ended', 'منتهية'),
    ]
    title_ar = models.CharField("عنوان المنحة", max_length=200)
    donor = models.ForeignKey(Donor, on_delete=models.PROTECT, related_name='grants', verbose_name="الجهة المانحة")
    beneficiary = models.ForeignKey(Beneficiary, on_delete=models.PROTECT, related_name='grants', verbose_name="الجهة المستفيدة")
    type = models.CharField("نوع المنحة", max_length=20, choices=TYPE_CHOICES)
    amount = models.DecimalField("المبلغ / القيمة", max_digits=14, decimal_places=2)
    status = models.CharField("حالة المنحة", max_length=20, choices=STATUS_CHOICES, default='ongoing')
    grant_date = models.DateField("تاريخ المنحة")
    decision_number = models.CharField("رقم القرار", max_length=100, blank=True)
    decision_date = models.DateField("تاريخ القرار", blank=True, null=True)
    decision_quantity_count = models.PositiveIntegerField("العدد (رقم صرف — للمنح العينية)", blank=True, null=True)
    decision_quantity_type = models.CharField("نوع الصنف (للمنح العينية)", max_length=50, blank=True)
    created_at = models.DateTimeField("تاريخ الإنشاء", auto_now_add=True)
    updated_at = models.DateTimeField("تاريخ التعديل", auto_now=True)

    def __str__(self):
        return self.title_ar

    def decision_quantity_display(self):
        """يدمج رقم العدد ونوع الصنف (لو موجودين) في نص واحد للعرض — مثال: '50 جهاز' أو '50' أو 'جهاز'."""
        parts = []
        if self.decision_quantity_count is not None:
            parts.append(str(self.decision_quantity_count))
        if self.decision_quantity_type:
            parts.append(self.decision_quantity_type)
        return " ".join(parts)

    def decision_display(self):
        """يدمج رقم القرار وتاريخه (والعدد لو منحة عينية) في نص واحد لعرضه للمانح والمستفيد والإداري."""
        parts = []
        if self.decision_number:
            parts.append(f"رقم {self.decision_number}")
        if self.decision_date:
            parts.append(f"{self.decision_date.day}/{self.decision_date.month}/{self.decision_date.year}")
        if self.type == 'in_kind' and self.decision_quantity_display():
            parts.append(f"العدد {self.decision_quantity_display()}")
        return "، ".join(parts) if parts else "—"

    class Meta:
        verbose_name = "منحة"
        verbose_name_plural = "المنح"




class GrantItem(models.Model):
    CONDITION_CHOICES = [
        ('new', 'جيد'),
        ('damaged', 'تالف'),
    ]
    grant = models.ForeignKey(Grant, on_delete=models.CASCADE, related_name='items', verbose_name="المنحة")
    item_type = models.CharField("نوع الصنف", max_length=100)
    building = models.CharField("المبنى", max_length=50, blank=True)
    floor = models.CharField("الدور", max_length=30, blank=True)
    room = models.CharField("الغرفة", max_length=50, blank=True)
    model = models.CharField("الموديل", max_length=100, blank=True)
    serial_number = models.CharField("الرقم التسلسلي", max_length=100, unique=True)
    condition = models.CharField("الحالة", max_length=20, choices=CONDITION_CHOICES)
    attachment = models.FileField("مرفق", upload_to='item_attachments/', blank=True, null=True)

    def __str__(self):
        return f"{self.item_type} - {self.serial_number}"

    class Meta:
        verbose_name = "صنف منحة"
        verbose_name_plural = "أصناف المنح"


class BeneficiaryCount(models.Model):
    CATEGORY_CHOICES = [
        ('staff', 'موظف إداري'),
        ('faculty', 'عضو هيئة تدريس'),
        ('student_male', 'طالب'),
        ('student_female', 'طالبة'),
        ('researcher', 'باحث'),
        ('patient', 'مريض'),
        ('other', 'أخرى'),
    ]

    grant = models.ForeignKey(Grant, on_delete=models.CASCADE, related_name='counts', verbose_name="المنحة")
    category = models.CharField("الفئة", max_length=20, choices=CATEGORY_CHOICES)
    other_label = models.CharField("اسم الفئة (عند اختيار أخرى)", max_length=100, blank=True)
    count = models.PositiveIntegerField("العدد", default=0)

    def display_category(self):
        """اسم الفئة للعرض — يرجع الاسم المخصص لو الفئة 'أخرى' ومكتوب لها اسم، وإلا الاسم القياسي."""
        if self.category == "other" and self.other_label:
            return self.other_label
        return self.get_category_display()

    def __str__(self):
        return f"{self.display_category()}: {self.count}"
    

    class Meta:
        verbose_name = "عدد مستفيدين"
        verbose_name_plural = "أعداد المستفيدين"
        unique_together = ('grant', 'category')


class Visit(models.Model):
    grant = models.ForeignKey(Grant, on_delete=models.CASCADE, related_name='visits', verbose_name="المنحة")
    visit_date = models.DateField("تاريخ الزيارة")
    description = models.TextField("الوصف", blank=True)

    def __str__(self):
        return f"زيارة {self.visit_date}"

    class Meta:
        verbose_name = "زيارة"
        verbose_name_plural = "الزيارات"


class ImpactReport(models.Model):
    STAGE_CHOICES = [
        ('preliminary', 'أولي'),
        ('official', 'رسمي'),
    ]
    grant = models.ForeignKey(Grant, on_delete=models.CASCADE, related_name='reports', verbose_name="المنحة")
    stage = models.CharField("المرحلة", max_length=20, choices=STAGE_CHOICES)
    report_date = models.DateField("تاريخ التقرير", blank=True, null=True)
    file = models.FileField("ملف التقرير", upload_to='impact_reports/')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="رفعه")
    created_at = models.DateTimeField("تاريخ الرفع", auto_now_add=True)

    def __str__(self):
        return f"{self.get_stage_display()} - {self.grant.title_ar}"

    class Meta:
        verbose_name = "تقرير أثر"
        verbose_name_plural = "تقارير الأثر"


class GrantUpdate(models.Model):
    TYPE_CHOICES = [
        ('news', 'خبر'),
        ('announcement', 'إعلان'),
    ]
    grant = models.ForeignKey(Grant, on_delete=models.CASCADE, related_name='updates', verbose_name="المنحة")
    type = models.CharField("النوع", max_length=20, choices=TYPE_CHOICES)
    title_ar = models.CharField("العنوان", max_length=255)
    link = models.URLField("الرابط", blank=True)
    created_at = models.DateTimeField("تاريخ النشر", auto_now_add=True)

    def __str__(self):
        return self.title_ar

    class Meta:
        verbose_name = "تحديث منحة"
        verbose_name_plural = "أخبار وإعلانات المنح"