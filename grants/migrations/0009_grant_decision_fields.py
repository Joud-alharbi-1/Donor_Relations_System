# Generated manually: يستبدل قرار الاعتماد النصي الواحد بثلاث خانات منفصلة
# (رقم القرار، تاريخ القرار، العدد) تطابق نموذج الإدخال الأصلي، مع دمجها
# للعرض عبر Grant.decision_display().

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grants', '0008_grantupdate_link_optional'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='grant',
            name='approval_decision',
        ),
        migrations.AddField(
            model_name='grant',
            name='decision_number',
            field=models.CharField(blank=True, max_length=100, verbose_name='رقم القرار'),
        ),
        migrations.AddField(
            model_name='grant',
            name='decision_date',
            field=models.DateField(blank=True, null=True, verbose_name='تاريخ القرار'),
        ),
        migrations.AddField(
            model_name='grant',
            name='decision_quantity',
            field=models.CharField(blank=True, max_length=50, verbose_name='العدد (للمنح العينية)'),
        ),
    ]
