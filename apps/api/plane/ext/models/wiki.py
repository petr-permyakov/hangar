# Copyright (c) 2026-present Maciej Szymczak and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""Workspace wiki: collections, shares, labels, and the blocks only the wiki has.

Pages themselves stay on the upstream ``Page`` row (``is_global=True``). Everything
that makes a page a wiki page — which collection it sits in, who it is shared
with, its labels — lives here so an upstream sync does not have to rebase a
``Page`` migration.
"""

from django.conf import settings
from django.db import models
from django.db.models import Q

from plane.db.models.base import BaseModel

PUBLIC = 0
PRIVATE = 1
ACCESS_CHOICES = ((PUBLIC, "Public"), (PRIVATE, "Private"))

ROLE_VIEW = "view"
ROLE_COMMENT = "comment"
ROLE_EDIT = "edit"
ROLE_CHOICES = (
    (ROLE_VIEW, "Can view"),
    (ROLE_COMMENT, "Can comment"),
    (ROLE_EDIT, "Can edit"),
)

LINK_PARENT = "parent"
LINK_CREATED_BY = "created_by"
LINK_SOURCE_CHOICES = (
    (LINK_PARENT, "Parent pages"),
    (LINK_CREATED_BY, "Created by"),
)


class WikiSettings(BaseModel):
    """Whether this workspace shows the wiki. On until an admin turns it off."""

    workspace = models.OneToOneField("db.Workspace", on_delete=models.CASCADE, related_name="wiki_settings")
    is_enabled = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Wiki settings"
        db_table = "ext_wiki_settings"

    def __str__(self):
        return f"{self.workspace_id} wiki={self.is_enabled}"


class WikiCollection(BaseModel):
    workspace = models.ForeignKey("db.Workspace", on_delete=models.CASCADE, related_name="wiki_collections")
    name = models.CharField(max_length=255)
    access = models.PositiveSmallIntegerField(choices=ACCESS_CHOICES, default=PUBLIC)
    is_default = models.BooleanField(default=False)
    logo_props = models.JSONField(default=dict, blank=True)
    sort_order = models.FloatField(default=65535)
    owned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wiki_collections")

    class Meta:
        verbose_name = "Wiki collection"
        db_table = "ext_wiki_collections"
        ordering = ("sort_order", "name")
        constraints = [
            models.UniqueConstraint(
                fields=["workspace"],
                condition=Q(is_default=True, deleted_at__isnull=True),
                name="ext_wiki_one_default_collection",
            ),
        ]

    def __str__(self):
        return self.name


class WikiCollectionMember(BaseModel):
    collection = models.ForeignKey(WikiCollection, on_delete=models.CASCADE, related_name="members")
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wiki_collection_memberships"
    )
    workspace = models.ForeignKey("db.Workspace", on_delete=models.CASCADE, related_name="wiki_collection_members")
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default=ROLE_VIEW)

    class Meta:
        verbose_name = "Wiki collection member"
        db_table = "ext_wiki_collection_members"
        constraints = [
            models.UniqueConstraint(
                fields=["collection", "member"],
                condition=Q(deleted_at__isnull=True),
                name="ext_wiki_collection_member_unique",
            ),
        ]


class WikiPageLink(BaseModel):
    """The one collection a top-level wiki page belongs to. Nested pages follow their parent."""

    page = models.OneToOneField("db.Page", on_delete=models.CASCADE, related_name="wiki_link")
    collection = models.ForeignKey(WikiCollection, on_delete=models.CASCADE, related_name="page_links")
    workspace = models.ForeignKey("db.Workspace", on_delete=models.CASCADE, related_name="wiki_page_links")

    class Meta:
        verbose_name = "Wiki page link"
        db_table = "ext_wiki_page_links"


class WikiPageShare(BaseModel):
    page = models.ForeignKey("db.Page", on_delete=models.CASCADE, related_name="wiki_shares")
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wiki_page_shares")
    workspace = models.ForeignKey("db.Workspace", on_delete=models.CASCADE, related_name="wiki_page_shares")
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default=ROLE_VIEW)

    class Meta:
        verbose_name = "Wiki page share"
        db_table = "ext_wiki_page_shares"
        constraints = [
            models.UniqueConstraint(
                fields=["page", "member"],
                condition=Q(deleted_at__isnull=True),
                name="ext_wiki_page_share_unique",
            ),
        ]


class WikiLabel(BaseModel):
    workspace = models.ForeignKey("db.Workspace", on_delete=models.CASCADE, related_name="wiki_labels")
    name = models.CharField(max_length=255)
    color = models.CharField(max_length=32, blank=True, default="")

    class Meta:
        verbose_name = "Wiki label"
        db_table = "ext_wiki_labels"
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "name"],
                condition=Q(deleted_at__isnull=True),
                name="ext_wiki_label_name_unique",
            ),
        ]


class WikiPageLabel(BaseModel):
    page = models.ForeignKey("db.Page", on_delete=models.CASCADE, related_name="wiki_page_labels")
    label = models.ForeignKey(WikiLabel, on_delete=models.CASCADE, related_name="page_labels")
    workspace = models.ForeignKey("db.Workspace", on_delete=models.CASCADE, related_name="wiki_page_label_links")

    class Meta:
        verbose_name = "Wiki page label"
        db_table = "ext_wiki_page_label_links"
        constraints = [
            models.UniqueConstraint(
                fields=["page", "label"],
                condition=Q(deleted_at__isnull=True),
                name="ext_wiki_page_label_unique",
            ),
        ]


class WikiPageComment(BaseModel):
    page = models.ForeignKey("db.Page", on_delete=models.CASCADE, related_name="wiki_comments")
    workspace = models.ForeignKey("db.Workspace", on_delete=models.CASCADE, related_name="wiki_comments")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wiki_comments")
    comment_html = models.TextField(blank=True, default="")
    comment_stripped = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "Wiki page comment"
        db_table = "ext_wiki_page_comments"
        ordering = ("created_at",)


class WikiPageTemplate(BaseModel):
    workspace = models.ForeignKey("db.Workspace", on_delete=models.CASCADE, related_name="wiki_templates")
    name = models.CharField(max_length=255)
    description_html = models.TextField(blank=True, default="<p></p>")
    owned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wiki_templates")

    class Meta:
        verbose_name = "Wiki page template"
        db_table = "ext_wiki_page_templates"
        ordering = ("name",)


class WikiPublication(BaseModel):
    page = models.OneToOneField("db.Page", on_delete=models.CASCADE, related_name="wiki_publication")
    workspace = models.ForeignKey("db.Workspace", on_delete=models.CASCADE, related_name="wiki_publications")
    anchor = models.CharField(max_length=32, unique=True)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wiki_publications"
    )

    class Meta:
        verbose_name = "Wiki publication"
        db_table = "ext_wiki_publications"


class WikiLinkBlock(BaseModel):
    """A live list of wiki pages embedded in another wiki page."""

    page = models.ForeignKey("db.Page", on_delete=models.CASCADE, related_name="wiki_link_blocks")
    workspace = models.ForeignKey("db.Workspace", on_delete=models.CASCADE, related_name="wiki_link_blocks")
    source = models.CharField(max_length=16, choices=LINK_SOURCE_CHOICES, default=LINK_PARENT)
    source_page = models.ForeignKey(
        "db.Page",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="wiki_link_block_sources",
    )
    member_ids = models.JSONField(default=list, blank=True)
    nesting_level = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = "Wiki link block"
        db_table = "ext_wiki_link_blocks"
