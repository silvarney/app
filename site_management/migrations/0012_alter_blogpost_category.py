from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    """Corrige FK de BlogPost.category para apontar para SiteCategory (antes apontava para app errado)."""

    dependencies = [
        ('site_management', '0011_mark_existing_blog_categories'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blogpost',
            name='category',
            field=models.ForeignKey(
                to='site_management.sitecategory',
                on_delete=django.db.models.deletion.SET_NULL,
                null=True,
                blank=True,
                verbose_name='Categoria'
            ),
        ),
    ]
