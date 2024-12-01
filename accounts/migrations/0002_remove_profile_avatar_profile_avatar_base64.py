# Generated by Django 5.1.3 on 2024-12-01 11:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="profile",
            name="avatar",
        ),
        migrations.AddField(
            model_name="profile",
            name="avatar_base64",
            field=models.TextField(blank=True, default=""),
        ),
    ]
