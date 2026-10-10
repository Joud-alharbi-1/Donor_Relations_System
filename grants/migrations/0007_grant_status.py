# Generated manually to add "حالة المنحة" (grant status) field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grants', '0006_alter_grantitem_condition'),
    ]

    operations = [
        migrations.AddField(
            model_name='grant',
            name='status',
            field=models.CharField(choices=[('ongoing', 'جارية'), ('ended', 'منتهية')], default='ongoing', max_length=20, verbose_name='حالة المنحة'),
        ),
    ]
