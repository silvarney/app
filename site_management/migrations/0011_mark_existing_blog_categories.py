from django.db import migrations


def mark_blog_categories(apps, schema_editor):
    SiteCategory = apps.get_model('site_management', 'SiteCategory')
    BlogPost = apps.get_model('site_management', 'BlogPost')
    cat_ids = BlogPost.objects.exclude(category__isnull=True).values_list('category_id', flat=True).distinct()
    if cat_ids:
        SiteCategory.objects.filter(id__in=cat_ids).update(is_blog=True)


class Migration(migrations.Migration):
    dependencies = [
        ('site_management', '0010_sitecategory_is_blog'),
    ]

    operations = [
        migrations.RunPython(mark_blog_categories, migrations.RunPython.noop)
    ]
