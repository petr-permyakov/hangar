# Copyright (c) 2026-present Maciej Szymczak and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from django.db import models
from django.db.models import Q

from plane.db.models.base import BaseModel

NAME_MAX_LENGTH = 255
EXTERNAL_ID_MAX_LENGTH = 255
REVENUE_MAX_LENGTH = 64
STAGE_MAX_LENGTH = 64
CONTRACT_STATUS_MAX_LENGTH = 64


class WorkspaceFeature(BaseModel):
    """Workspace-level feature switches that have no home on the upstream Workspace row."""

    workspace = models.OneToOneField(
        "db.Workspace",
        on_delete=models.CASCADE,
        related_name="ext_features",
    )
    is_customers_enabled = models.BooleanField(default=False)
    customers_enabled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Workspace Feature"
        verbose_name_plural = "Workspace Features"
        db_table = "ext_workspace_features"

    def __str__(self):
        return f"{self.workspace_id} customers={self.is_customers_enabled}"


class Customer(BaseModel):
    """Workspace CRM record. Field names match Plane API v2."""

    workspace = models.ForeignKey("db.Workspace", on_delete=models.CASCADE, related_name="ext_customers")
    name = models.CharField(max_length=NAME_MAX_LENGTH)
    description = models.TextField(blank=True, default="")
    description_html = models.TextField(blank=True, default="")
    description_stripped = models.TextField(blank=True, default="")
    email = models.EmailField(blank=True, default="")
    website_url = models.URLField(max_length=1024, blank=True, default="")
    # Shown as Industry. The website belongs in website_url.
    domain = models.CharField(max_length=255, blank=True, default="")
    employees = models.PositiveIntegerField(null=True, blank=True)
    stage = models.CharField(max_length=STAGE_MAX_LENGTH, blank=True, default="")
    contract_status = models.CharField(max_length=CONTRACT_STATUS_MAX_LENGTH, blank=True, default="")
    revenue = models.CharField(max_length=REVENUE_MAX_LENGTH, blank=True, default="")
    revenue_amount = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    logo_asset = models.ForeignKey(
        "db.FileAsset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ext_customer_logos",
    )
    logo_props = models.JSONField(default=dict, blank=True)
    external_source = models.CharField(max_length=EXTERNAL_ID_MAX_LENGTH, blank=True, null=True)
    external_id = models.CharField(max_length=EXTERNAL_ID_MAX_LENGTH, blank=True, null=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customers"
        db_table = "ext_customers"
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "name"],
                condition=Q(deleted_at__isnull=True),
                name="ext_customer_unique_name_per_workspace",
            ),
            models.UniqueConstraint(
                fields=["workspace", "external_source", "external_id"],
                condition=Q(deleted_at__isnull=True)
                & Q(external_source__isnull=False)
                & ~Q(external_source="")
                & Q(external_id__isnull=False)
                & ~Q(external_id=""),
                name="ext_customer_unique_external_id_per_workspace",
            ),
        ]
        indexes = [
            models.Index(fields=["workspace", "name"]),
            models.Index(fields=["workspace", "archived_at"]),
        ]

    def __str__(self):
        return self.name


class CustomerRequest(BaseModel):
    """What a customer asked for. The `link` is a single source URL."""

    workspace = models.ForeignKey("db.Workspace", on_delete=models.CASCADE, related_name="ext_customer_requests")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="requests")
    name = models.CharField(max_length=NAME_MAX_LENGTH)
    description = models.TextField(blank=True, default="")
    description_html = models.TextField(blank=True, default="")
    description_stripped = models.TextField(blank=True, default="")
    link = models.URLField(max_length=2048, blank=True, default="")
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Customer Request"
        verbose_name_plural = "Customer Requests"
        db_table = "ext_customer_requests"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["customer", "created_at"]),
            models.Index(fields=["workspace", "archived_at"]),
        ]

    def __str__(self):
        return self.name


class CustomerWorkItemLink(BaseModel):
    """Direct (customer_request is null) or request-mediated link to a work item."""

    workspace = models.ForeignKey("db.Workspace", on_delete=models.CASCADE, related_name="ext_customer_work_items")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="work_item_links")
    issue = models.ForeignKey("db.Issue", on_delete=models.CASCADE, related_name="ext_customer_links")
    customer_request = models.ForeignKey(
        CustomerRequest,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="work_item_links",
    )

    class Meta:
        verbose_name = "Customer Work Item Link"
        verbose_name_plural = "Customer Work Item Links"
        db_table = "ext_customer_work_items"
        constraints = [
            models.UniqueConstraint(
                fields=["customer", "issue"],
                condition=Q(deleted_at__isnull=True, customer_request__isnull=True),
                name="ext_customer_direct_link_unique",
            ),
            models.UniqueConstraint(
                fields=["customer", "issue", "customer_request"],
                condition=Q(deleted_at__isnull=True, customer_request__isnull=False),
                name="ext_customer_request_link_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["issue"]),
            models.Index(fields=["customer"]),
            models.Index(fields=["customer_request"]),
        ]

    def __str__(self):
        return f"{self.customer_id} -> {self.issue_id}"
