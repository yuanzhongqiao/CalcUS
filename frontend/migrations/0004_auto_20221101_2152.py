# Generated by Django 3.2.15 on 2022-11-02 02:52

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import hashid_field.field


class Migration(migrations.Migration):
    dependencies = [
        ("frontend", "0003_auto_20221031_1735"),
    ]

    operations = [
        migrations.CreateModel(
            name="Flowchart",
            fields=[
                (
                    "id",
                    hashid_field.field.BigHashidAutoField(
                        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890",
                        auto_created=True,
                        min_length=13,
                        prefix="",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("flowchart", models.JSONField(null=True)),
                (
                    "author",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AlterField(
            model_name="calculation",
            name="order",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="frontend.calculationorder",
            ),
        ),
        migrations.CreateModel(
            name="Step",
            fields=[
                (
                    "id",
                    hashid_field.field.BigHashidAutoField(
                        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890",
                        auto_created=True,
                        min_length=13,
                        prefix="",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=50)),
                (
                    "flowchart",
                    models.ForeignKey(
                        default=None,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="frontend.flowchart",
                    ),
                ),
                (
                    "parameters",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="frontend.parameters",
                    ),
                ),
                (
                    "parentId",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to="frontend.step",
                    ),
                ),
                (
                    "step",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="frontend.basicstep",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="FlowchartOrder",
            fields=[
                (
                    "id",
                    hashid_field.field.BigHashidAutoField(
                        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890",
                        auto_created=True,
                        min_length=13,
                        prefix="",
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("last_seen_status", models.PositiveIntegerField(default=0)),
                (
                    "date",
                    models.DateTimeField(blank=True, null=True, verbose_name="date"),
                ),
                (
                    "author",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "ensemble",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="frontend.ensemble",
                    ),
                ),
                (
                    "filter",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="frontend.filter",
                    ),
                ),
                (
                    "flowchart",
                    models.ForeignKey(
                        default=None,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="frontend.flowchart",
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="frontend.project",
                    ),
                ),
                (
                    "structure",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="frontend.structure",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="calculation",
            name="flowchart_order",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="frontend.flowchartorder",
            ),
        ),
        migrations.AddField(
            model_name="calculation",
            name="flowchart_step",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="frontend.step",
            ),
        ),
    ]
