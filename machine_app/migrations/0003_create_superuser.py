from django.db import migrations
import os

def create_superuser(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    if not User.objects.filter(username='Keshav').exists():
        User.objects.create_superuser(
            username='Keshav',
            email='keshavasukhai@gmail.com',
            password='Keshkaranlol02'  # Change this to your desired password
        )

class Migration(migrations.Migration):
    dependencies = [
        # This will be automatically filled - keep whatever is there
    ]

    operations = [
        migrations.RunPython(create_superuser),
    ]