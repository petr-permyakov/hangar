# Copyright (c) 2026-present Maciej Szymczak and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from django.utils.html import strip_tags
from rest_framework import serializers

from plane.ext.models.customer import (
    CONTRACT_STATUS_MAX_LENGTH,
    NAME_MAX_LENGTH,
    REVENUE_MAX_LENGTH,
    STAGE_MAX_LENGTH,
    Customer,
    CustomerRequest,
    CustomerWorkItemLink,
)
from plane.utils.content_validator import validate_html_content
from plane.utils.url import contains_url


def _clean_html(value):
    if not value:
        return ""
    is_valid, error, clean = validate_html_content(value)
    if not is_valid:
        raise serializers.ValidationError(error or "Invalid HTML")
    return clean or ""


def _stripped(html, plain):
    text = strip_tags(html or "").strip()
    return text or (plain or "")


class CustomerSerializer(serializers.ModelSerializer):
    customer_request_count = serializers.IntegerField(read_only=True, default=0)
    logo_url = serializers.SerializerMethodField()
    created_by_id = serializers.UUIDField(read_only=True)
    updated_by_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Customer
        fields = [
            "id",
            "name",
            "description",
            "description_html",
            "email",
            "website_url",
            "domain",
            "employees",
            "stage",
            "contract_status",
            "revenue",
            "revenue_amount",
            "logo_props",
            "logo_url",
            "external_source",
            "external_id",
            "archived_at",
            "customer_request_count",
            "created_at",
            "updated_at",
            "created_by_id",
            "updated_by_id",
        ]
        read_only_fields = [
            "id",
            "archived_at",
            "customer_request_count",
            "created_at",
            "updated_at",
            "created_by_id",
            "updated_by_id",
            "logo_url",
        ]

    def get_logo_url(self, obj):
        asset = getattr(obj, "logo_asset", None)
        if asset is None:
            return None
        return getattr(asset, "asset_url", None) or getattr(asset, "asset", None)

    def validate_name(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Name is required.")
        if len(value) > NAME_MAX_LENGTH:
            raise serializers.ValidationError(f"Name must be at most {NAME_MAX_LENGTH} characters.")
        if contains_url(value):
            raise serializers.ValidationError("Name must not contain URLs.")
        return value

    def validate_stage(self, value):
        return (value or "")[:STAGE_MAX_LENGTH]

    def validate_contract_status(self, value):
        return (value or "")[:CONTRACT_STATUS_MAX_LENGTH]

    def validate_revenue(self, value):
        return (value or "")[:REVENUE_MAX_LENGTH]

    def validate_description_html(self, value):
        return _clean_html(value)

    def validate(self, attrs):
        html = attrs.get("description_html", getattr(self.instance, "description_html", ""))
        if "description_html" in attrs and "description" not in attrs:
            attrs["description"] = _stripped(html, "")
        elif "description" in attrs and "description_html" not in attrs:
            attrs.setdefault("description_html", f"<p>{attrs['description']}</p>" if attrs["description"] else "")
        attrs["description_stripped"] = _stripped(
            attrs.get("description_html", html), attrs.get("description", getattr(self.instance, "description", ""))
        )
        return attrs


class CustomerRequestSerializer(serializers.ModelSerializer):
    work_item_ids = serializers.ListField(
        child=serializers.UUIDField(), write_only=True, required=False, allow_empty=True
    )
    created_by_id = serializers.UUIDField(read_only=True)
    updated_by_id = serializers.UUIDField(read_only=True)
    customer_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = CustomerRequest
        fields = [
            "id",
            "customer_id",
            "name",
            "description",
            "description_html",
            "link",
            "work_item_ids",
            "archived_at",
            "created_at",
            "updated_at",
            "created_by_id",
            "updated_by_id",
        ]
        read_only_fields = [
            "id",
            "customer_id",
            "archived_at",
            "created_at",
            "updated_at",
            "created_by_id",
            "updated_by_id",
        ]

    def validate_name(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Name is required.")
        if len(value) > NAME_MAX_LENGTH:
            raise serializers.ValidationError(f"Name must be at most {NAME_MAX_LENGTH} characters.")
        return value

    def validate_description_html(self, value):
        return _clean_html(value)

    def validate_link(self, value):
        value = (value or "").strip()
        if not value:
            return ""
        if not (value.startswith("http://") or value.startswith("https://")):
            raise serializers.ValidationError("Source link must be an http or https URL.")
        return value

    def validate(self, attrs):
        html = attrs.get("description_html", getattr(self.instance, "description_html", ""))
        if "description_html" in attrs and "description" not in attrs:
            attrs["description"] = _stripped(html, "")
        attrs["description_stripped"] = _stripped(
            attrs.get("description_html", html), attrs.get("description", getattr(self.instance, "description", ""))
        )
        return attrs


class CustomerWorkItemLinkActionSerializer(serializers.Serializer):
    add = serializers.ListField(child=serializers.UUIDField(), required=False, allow_empty=True)
    remove = serializers.ListField(child=serializers.UUIDField(), required=False, allow_empty=True)
    customer_request_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, attrs):
        if not attrs.get("add") and not attrs.get("remove"):
            raise serializers.ValidationError("Pass at least one of add or remove.")
        return attrs


class IssueCustomerSerializer(serializers.ModelSerializer):
    customer_id = serializers.UUIDField(source="customer.id", read_only=True)
    name = serializers.CharField(source="customer.name", read_only=True)
    website_url = serializers.CharField(source="customer.website_url", read_only=True)
    stage = serializers.CharField(source="customer.stage", read_only=True)
    contract_status = serializers.CharField(source="customer.contract_status", read_only=True)
    revenue = serializers.CharField(source="customer.revenue", read_only=True)
    customer_request_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomerWorkItemLink
        fields = [
            "id",
            "customer_id",
            "name",
            "website_url",
            "stage",
            "contract_status",
            "revenue",
            "customer_request_id",
            "customer_request_name",
        ]
        read_only_fields = fields

    def get_customer_request_name(self, obj):
        request = obj.customer_request
        return request.name if request else None
