from django.db import models

# Create your models here.
class Donor(models.Model):
    name_ar = models.CharField("اسم الجهة", max_length=200)
    logo = models.ImageField("الشعار", upload_to='donor_logos/', blank=True, null=True)
    notes = models.TextField("ملاحظات", blank=True)
    created_at = models.DateTimeField("تاريخ الإضافة", auto_now_add=True)

    def __str__(self):
        return self.name_ar

    class Meta:
        verbose_name = "جهة مانحة"
        verbose_name_plural = "الجهات المانحة"

class DonorContact(models.Model):
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE, related_name="contacts", verbose_name="الجهة المانحة")
    position = models.CharField("المنصب", max_length=100)
    name = models.CharField("الاسم", max_length=150)
    phone = models.CharField("رقم الجوال", max_length=20)
    email = models.EmailField("البريد الإلكتروني", blank=True)

    def __str__(self):
        return f"{self.name} — {self.position} ({self.donor.name_ar})"

    class Meta:
        verbose_name = "جهة اتصال بالمانح"
        verbose_name_plural = "جهات اتصال المانحين"
        
class Beneficiary(models.Model):
    TYPE_CHOICES = [
        ('college', 'كلية'),
        ('deanship', 'عمادة'),
        ('hospital', 'مستشفى'),
        ('center', 'مركز'),
    ]
    name_ar = models.CharField("اسم الجهة", max_length=200)
    type = models.CharField("النوع", max_length=20, choices=TYPE_CHOICES)
    created_at = models.DateTimeField("تاريخ الإضافة", auto_now_add=True)

    def __str__(self):
        return self.name_ar

    class Meta:
        verbose_name = "جهة مستفيدة"
        verbose_name_plural = "الجهات المستفيدة"