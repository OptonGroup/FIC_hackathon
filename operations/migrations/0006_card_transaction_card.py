# Generated by Django 5.1.3 on 2024-12-01 08:42

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0005_alter_regularpayment_options_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Card",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(max_length=100, verbose_name="Название карты"),
                ),
                (
                    "card_number",
                    models.CharField(max_length=19, verbose_name="Номер карты"),
                ),
                ("bank", models.CharField(max_length=100, verbose_name="Банк")),
                (
                    "card_type",
                    models.CharField(
                        choices=[("debit", "Дебетовая"), ("credit", "Кредитная")],
                        max_length=10,
                        verbose_name="Тип карты",
                    ),
                ),
                (
                    "design",
                    models.CharField(
                        choices=[
                            ("classic_black", "Классическая черная"),
                            ("classic_white", "Классическая белая"),
                            ("gold", "Золотая"),
                            ("platinum", "Платиновая"),
                            ("metal", "Металлическая"),
                        ],
                        default="classic_black",
                        max_length=20,
                        verbose_name="Дизайн карты",
                    ),
                ),
                (
                    "balance",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=10,
                        verbose_name="Баланс",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Дата создания"
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Пользователь",
                    ),
                ),
            ],
            options={
                "verbose_name": "Карта",
                "verbose_name_plural": "Карты",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddField(
            model_name="transaction",
            name="card",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="operations.card",
                verbose_name="Карта",
            ),
        ),
    ]
