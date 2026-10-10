# Generated manually to make GrantUpdate.link optional (الإعلانات لا تحتاج رابط)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grants', '0007_grant_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='grantupdate',
            name='link',
            field=models.URLField(blank=True, verbose_name='الرابط'),
        ),
    ]
