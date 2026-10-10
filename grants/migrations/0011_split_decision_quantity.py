# Generated manually: يفصل حقل العدد النصي الواحد (decision_quantity، مثال "50 جهاز")
# إلى حقلين منفصلين: decision_quantity_count (رقم صرف) و decision_quantity_type (نوع الصنف كنص)،
# عشان يصير حساب الحد الأقصى لعدد الأصناف (اعتمادًا على الرقم) يشتغل دائمًا حتى لو المستخدم
# كتب نوع الصنف مع الرقم. يحاول يفصل أي بيانات موجودة مسبقًا (رقم في البداية + الباقي كنوع).

import re

from django.db import migrations, models


def split_existing_quantities(apps, schema_editor):
    Grant = apps.get_model('grants', 'Grant')
    for grant in Grant.objects.exclude(decision_quantity=''):
        raw = (grant.decision_quantity or '').strip()
        if not raw:
            continue
        m = re.match(r'^(\d+)\s*(.*)$', raw)
        if m:
            grant.decision_quantity_count = int(m.group(1))
            grant.decision_quantity_type = m.group(2).strip()
        else:
            grant.decision_quantity_count = None
            grant.decision_quantity_type = raw
        grant.save(update_fields=['decision_quantity_count', 'decision_quantity_type'])


def merge_back_quantities(apps, schema_editor):
    Grant = apps.get_model('grants', 'Grant')
    for grant in Grant.objects.all():
        parts = []
        if grant.decision_quantity_count is not None:
            parts.append(str(grant.decision_quantity_count))
        if grant.decision_quantity_type:
            parts.append(grant.decision_quantity_type)
        grant.decision_quantity = ' '.join(parts)
        grant.save(update_fields=['decision_quantity'])


class Migration(migrations.Migration):

    dependencies = [
        ('grants', '0010_beneficiarycount_other_label_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='grant',
            name='decision_quantity_count',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='العدد (رقم صرف — للمنح العينية)'),
        ),
        migrations.AddField(
            model_name='grant',
            name='decision_quantity_type',
            field=models.CharField(blank=True, max_length=50, verbose_name='نوع الصنف (للمنح العينية)'),
        ),
        migrations.RunPython(split_existing_quantities, merge_back_quantities),
        migrations.RemoveField(
            model_name='grant',
            name='decision_quantity',
        ),
    ]
