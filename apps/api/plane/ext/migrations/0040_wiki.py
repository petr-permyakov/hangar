# Copyright (c) 2026-present Maciej Szymczak and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ext", "0039_default_working_hours"),
        ("db", "0121_alter_estimate_type"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="WikiSettings",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Last Modified At")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="Deleted At")),
                ("id", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ("is_enabled", models.BooleanField(default=True)),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(class)s_created_by", to=settings.AUTH_USER_MODEL, verbose_name="Created By")),
                ("updated_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(class)s_updated_by", to=settings.AUTH_USER_MODEL, verbose_name="Last Modified By")),
                ("workspace", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="wiki_settings", to="db.workspace")),
            ],
            options={"verbose_name": "Wiki settings", "db_table": "ext_wiki_settings"},
        ),
        migrations.CreateModel(
            name="WikiCollection",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Last Modified At")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="Deleted At")),
                ("id", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ("name", models.CharField(max_length=255)),
                ("access", models.PositiveSmallIntegerField(choices=[(0, "Public"), (1, "Private")], default=0)),
                ("is_default", models.BooleanField(default=False)),
                ("logo_props", models.JSONField(blank=True, default=dict)),
                ("sort_order", models.FloatField(default=65535)),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(class)s_created_by", to=settings.AUTH_USER_MODEL, verbose_name="Created By")),
                ("owned_by", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="wiki_collections", to=settings.AUTH_USER_MODEL)),
                ("updated_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(class)s_updated_by", to=settings.AUTH_USER_MODEL, verbose_name="Last Modified By")),
                ("workspace", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="wiki_collections", to="db.workspace")),
            ],
            options={"verbose_name": "Wiki collection", "db_table": "ext_wiki_collections", "ordering": ("sort_order", "name")},
        ),
        migrations.AddConstraint(
            model_name="wikicollection",
            constraint=models.UniqueConstraint(condition=models.Q(("deleted_at__isnull", True), ("is_default", True)), fields=("workspace",), name="ext_wiki_one_default_collection"),
        ),
        migrations.CreateModel(
            name="WikiCollectionMember",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Last Modified At")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="Deleted At")),
                ("id", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ("role", models.CharField(choices=[("view", "Can view"), ("comment", "Can comment"), ("edit", "Can edit")], default="view", max_length=16)),
                ("collection", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="members", to="ext.wikicollection")),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(class)s_created_by", to=settings.AUTH_USER_MODEL, verbose_name="Created By")),
                ("member", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="wiki_collection_memberships", to=settings.AUTH_USER_MODEL)),
                ("updated_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(class)s_updated_by", to=settings.AUTH_USER_MODEL, verbose_name="Last Modified By")),
                ("workspace", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="wiki_collection_members", to="db.workspace")),
            ],
            options={"verbose_name": "Wiki collection member", "db_table": "ext_wiki_collection_members"},
        ),
        migrations.AddConstraint(
            model_name="wikicollectionmember",
            constraint=models.UniqueConstraint(condition=models.Q(("deleted_at__isnull", True)), fields=("collection", "member"), name="ext_wiki_collection_member_unique"),
        ),
        migrations.CreateModel(
            name="WikiPageLink",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Last Modified At")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="Deleted At")),
                ("id", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ("collection", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="page_links", to="ext.wikicollection")),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(class)s_created_by", to=settings.AUTH_USER_MODEL, verbose_name="Created By")),
                ("page", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="wiki_link", to="db.page")),
                ("updated_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(class)s_updated_by", to=settings.AUTH_USER_MODEL, verbose_name="Last Modified By")),
                ("workspace", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="wiki_page_links", to="db.workspace")),
            ],
            options={"verbose_name": "Wiki page link", "db_table": "ext_wiki_page_links"},
        ),
        migrations.CreateModel(
            name="WikiPageShare",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Last Modified At")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="Deleted At")),
                ("id", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ("role", models.CharField(choices=[("view", "Can view"), ("comment", "Can comment"), ("edit", "Can edit")], default="view", max_length=16)),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(class)s_created_by", to=settings.AUTH_USER_MODEL, verbose_name="Created By")),
                ("member", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="wiki_page_shares", to=settings.AUTH_USER_MODEL)),
                ("page", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="wiki_shares", to="db.page")),
                ("updated_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(class)s_updated_by", to=settings.AUTH_USER_MODEL, verbose_name="Last Modified By")),
                ("workspace", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="wiki_page_shares", to="db.workspace")),
            ],
            options={"verbose_name": "Wiki page share", "db_table": "ext_wiki_page_shares"},
        ),
        migrations.AddConstraint(
            model_name="wikipageshare",
            constraint=models.UniqueConstraint(condition=models.Q(("deleted_at__isnull", True)), fields=("page", "member"), name="ext_wiki_page_share_unique"),
        ),
        migrations.CreateModel(
            name="WikiLabel",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Last Modified At")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="Deleted At")),
                ("id", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ("name", models.CharField(max_length=255)),
                ("color", models.CharField(blank=True, default="", max_length=32)),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(class)s_created_by", to=settings.AUTH_USER_MODEL, verbose_name="Created By")),
                ("updated_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(class)s_updated_by", to=settings.AUTH_USER_MODEL, verbose_name="Last Modified By")),
                ("workspace", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="wiki_labels", to="db.workspace")),
            ],
            options={"verbose_name": "Wiki label", "db_table": "ext_wiki_labels"},
        ),
        migrations.AddConstraint(
            model_name="wikilabel",
            constraint=models.UniqueConstraint(condition=models.Q(("deleted_at__isnull", True)), fields=("workspace", "name"), name="ext_wiki_label_name_unique"),
        ),
        migrations.CreateModel(
            name="WikiPageLabel",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Last Modified At")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="Deleted At")),
                ("id", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(class)s_created_by", to=settings.AUTH_USER_MODEL, verbose_name="Created By")),
                ("label", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="page_labels", to="ext.wikilabel")),
                ("page", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="wiki_page_labels", to="db.page")),
                ("updated_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(class)s_updated_by", to=settings.AUTH_USER_MODEL, verbose_name="Last Modified By")),
                ("workspace", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="wiki_page_label_links", to="db.workspace")),
            ],
            options={"verbose_name": "Wiki page label", "db_table": "ext_wiki_page_label_links"},
        ),
        migrations.AddConstraint(
            model_name="wikipagelabel",
            constraint=models.UniqueConstraint(condition=models.Q(("deleted_at__isnull", True)), fields=("page", "label"), name="ext_wiki_page_label_unique"),
        ),
        migrations.CreateModel(
            name="WikiPageComment",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Last Modified At")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="Deleted At")),
                ("id", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ("comment_html", models.TextField(blank=True, default="")),
                ("comment_stripped", models.TextField(blank=True, default="")),
                ("actor", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="wiki_comments", to=settings.AUTH_USER_MODEL)),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(class)s_created_by", to=settings.AUTH_USER_MODEL, verbose_name="Created By")),
                ("page", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="wiki_comments", to="db.page")),
                ("updated_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(class)s_updated_by", to=settings.AUTH_USER_MODEL, verbose_name="Last Modified By")),
                ("workspace", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="wiki_comments", to="db.workspace")),
            ],
            options={"verbose_name": "Wiki page comment", "db_table": "ext_wiki_page_comments", "ordering": ("created_at",)},
        ),
        migrations.CreateModel(
            name="WikiPageTemplate",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Last Modified At")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="Deleted At")),
                ("id", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ("name", models.CharField(max_length=255)),
                ("description_html", models.TextField(blank=True, default="<p></p>")),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(class)s_created_by", to=settings.AUTH_USER_MODEL, verbose_name="Created By")),
                ("owned_by", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="wiki_templates", to=settings.AUTH_USER_MODEL)),
                ("updated_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(class)s_updated_by", to=settings.AUTH_USER_MODEL, verbose_name="Last Modified By")),
                ("workspace", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="wiki_templates", to="db.workspace")),
            ],
            options={"verbose_name": "Wiki page template", "db_table": "ext_wiki_page_templates", "ordering": ("name",)},
        ),
        migrations.CreateModel(
            name="WikiPublication",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Last Modified At")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="Deleted At")),
                ("id", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ("anchor", models.CharField(max_length=32, unique=True)),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(class)s_created_by", to=settings.AUTH_USER_MODEL, verbose_name="Created By")),
                ("page", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="wiki_publication", to="db.page")),
                ("published_by", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="wiki_publications", to=settings.AUTH_USER_MODEL)),
                ("updated_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(class)s_updated_by", to=settings.AUTH_USER_MODEL, verbose_name="Last Modified By")),
                ("workspace", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="wiki_publications", to="db.workspace")),
            ],
            options={"verbose_name": "Wiki publication", "db_table": "ext_wiki_publications"},
        ),
        migrations.CreateModel(
            name="WikiLinkBlock",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created At")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Last Modified At")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="Deleted At")),
                ("id", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ("source", models.CharField(choices=[("parent", "Parent pages"), ("created_by", "Created by")], default="parent", max_length=16)),
                ("member_ids", models.JSONField(blank=True, default=list)),
                ("nesting_level", models.PositiveSmallIntegerField(default=0)),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(class)s_created_by", to=settings.AUTH_USER_MODEL, verbose_name="Created By")),
                ("page", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="wiki_link_blocks", to="db.page")),
                ("source_page", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="wiki_link_block_sources", to="db.page")),
                ("updated_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(class)s_updated_by", to=settings.AUTH_USER_MODEL, verbose_name="Last Modified By")),
                ("workspace", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="wiki_link_blocks", to="db.workspace")),
            ],
            options={"verbose_name": "Wiki link block", "db_table": "ext_wiki_link_blocks"},
        ),
    ]
