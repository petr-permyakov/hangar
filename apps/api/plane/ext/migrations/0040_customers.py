# Copyright (c) 2026-present Maciej Szymczak and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("db", "0133_email_outbox_outer_subject"),
        ("ext", "0039_default_working_hours"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="WorkspaceFeature",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Last Modified At")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="Deleted At")),
                (
                    "id",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                ("is_customers_enabled", models.BooleanField(default=False)),
                ("customers_enabled_at", models.DateTimeField(blank=True, null=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_created_by",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Created By",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_updated_by",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Last Modified By",
                    ),
                ),
                (
                    "workspace",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ext_features",
                        to="db.workspace",
                    ),
                ),
            ],
            options={
                "verbose_name": "Workspace Feature",
                "verbose_name_plural": "Workspace Features",
                "db_table": "ext_workspace_features",
            },
        ),
        migrations.CreateModel(
            name="Customer",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Last Modified At")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="Deleted At")),
                (
                    "id",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True, default="")),
                ("description_html", models.TextField(blank=True, default="")),
                ("description_stripped", models.TextField(blank=True, default="")),
                ("email", models.EmailField(blank=True, default="", max_length=254)),
                ("website_url", models.URLField(blank=True, default="", max_length=1024)),
                ("domain", models.CharField(blank=True, default="", max_length=255)),
                ("employees", models.PositiveIntegerField(blank=True, null=True)),
                ("stage", models.CharField(blank=True, default="", max_length=64)),
                ("contract_status", models.CharField(blank=True, default="", max_length=64)),
                ("revenue", models.CharField(blank=True, default="", max_length=64)),
                ("revenue_amount", models.DecimalField(blank=True, decimal_places=2, max_digits=18, null=True)),
                ("logo_props", models.JSONField(blank=True, default=dict)),
                ("external_source", models.CharField(blank=True, max_length=255, null=True)),
                ("external_id", models.CharField(blank=True, max_length=255, null=True)),
                ("archived_at", models.DateTimeField(blank=True, null=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_created_by",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Created By",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_updated_by",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Last Modified By",
                    ),
                ),
                (
                    "logo_asset",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="ext_customer_logos",
                        to="db.fileasset",
                    ),
                ),
                (
                    "workspace",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ext_customers",
                        to="db.workspace",
                    ),
                ),
            ],
            options={
                "verbose_name": "Customer",
                "verbose_name_plural": "Customers",
                "db_table": "ext_customers",
                "ordering": ("name",),
            },
        ),
        migrations.CreateModel(
            name="CustomerRequest",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Last Modified At")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="Deleted At")),
                (
                    "id",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True, default="")),
                ("description_html", models.TextField(blank=True, default="")),
                ("description_stripped", models.TextField(blank=True, default="")),
                ("link", models.URLField(blank=True, default="", max_length=2048)),
                ("archived_at", models.DateTimeField(blank=True, null=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_created_by",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Created By",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_updated_by",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Last Modified By",
                    ),
                ),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="requests",
                        to="ext.customer",
                    ),
                ),
                (
                    "workspace",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ext_customer_requests",
                        to="db.workspace",
                    ),
                ),
            ],
            options={
                "verbose_name": "Customer Request",
                "verbose_name_plural": "Customer Requests",
                "db_table": "ext_customer_requests",
                "ordering": ("-created_at",),
            },
        ),
        migrations.CreateModel(
            name="CustomerWorkItemLink",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Last Modified At")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="Deleted At")),
                (
                    "id",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_created_by",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Created By",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_updated_by",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Last Modified By",
                    ),
                ),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="work_item_links",
                        to="ext.customer",
                    ),
                ),
                (
                    "customer_request",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="work_item_links",
                        to="ext.customerrequest",
                    ),
                ),
                (
                    "issue",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ext_customer_links",
                        to="db.issue",
                    ),
                ),
                (
                    "workspace",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ext_customer_work_items",
                        to="db.workspace",
                    ),
                ),
            ],
            options={
                "verbose_name": "Customer Work Item Link",
                "verbose_name_plural": "Customer Work Item Links",
                "db_table": "ext_customer_work_items",
            },
        ),
        migrations.AddIndex(
            model_name="customer",
            index=models.Index(fields=["workspace", "name"], name="ext_custome_workspa_5c1a11_idx"),
        ),
        migrations.AddIndex(
            model_name="customer",
            index=models.Index(fields=["workspace", "archived_at"], name="ext_custome_workspa_8b22c0_idx"),
        ),
        migrations.AddConstraint(
            model_name="customer",
            constraint=models.UniqueConstraint(
                condition=models.Q(("deleted_at__isnull", True)),
                fields=("workspace", "name"),
                name="ext_customer_unique_name_per_workspace",
            ),
        ),
        migrations.AddConstraint(
            model_name="customer",
            constraint=models.UniqueConstraint(
                condition=models.Q(
                    ("deleted_at__isnull", True),
                    ("external_source__isnull", False),
                    models.Q(("external_source", ""), _negated=True),
                    ("external_id__isnull", False),
                    models.Q(("external_id", ""), _negated=True),
                ),
                fields=("workspace", "external_source", "external_id"),
                name="ext_customer_unique_external_id_per_workspace",
            ),
        ),
        migrations.AddIndex(
            model_name="customerrequest",
            index=models.Index(fields=["customer", "created_at"], name="ext_custome_custome_4a91e2_idx"),
        ),
        migrations.AddIndex(
            model_name="customerrequest",
            index=models.Index(fields=["workspace", "archived_at"], name="ext_custome_workspa_91aa10_idx"),
        ),
        migrations.AddIndex(
            model_name="customerworkitemlink",
            index=models.Index(fields=["issue"], name="ext_custome_issue_i_11c0a3_idx"),
        ),
        migrations.AddIndex(
            model_name="customerworkitemlink",
            index=models.Index(fields=["customer"], name="ext_custome_custome_22b8d1_idx"),
        ),
        migrations.AddIndex(
            model_name="customerworkitemlink",
            index=models.Index(fields=["customer_request"], name="ext_custome_custome_33c9e4_idx"),
        ),
        migrations.AddConstraint(
            model_name="customerworkitemlink",
            constraint=models.UniqueConstraint(
                condition=models.Q(("deleted_at__isnull", True), ("customer_request__isnull", True)),
                fields=("customer", "issue"),
                name="ext_customer_direct_link_unique",
            ),
        ),
        migrations.AddConstraint(
            model_name="customerworkitemlink",
            constraint=models.UniqueConstraint(
                condition=models.Q(("deleted_at__isnull", True), ("customer_request__isnull", False)),
                fields=("customer", "issue", "customer_request"),
                name="ext_customer_request_link_unique",
            ),
        ),
    ]
