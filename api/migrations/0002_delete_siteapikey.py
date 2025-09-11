from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_site_api_key'),
    ]

    operations = [
        migrations.DeleteModel(
            name='SiteAPIKey',
        ),
    ]
