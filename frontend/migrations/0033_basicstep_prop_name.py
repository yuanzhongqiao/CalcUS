# Generated by Django 3.2.19 on 2023-07-09 14:34

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("frontend", "0032_user_advanced_interface"),
    ]

    operations = [
        migrations.AddField(
            model_name="basicstep",
            name="prop_name",
            field=models.CharField(default="", max_length=100),
        ),
    ]
