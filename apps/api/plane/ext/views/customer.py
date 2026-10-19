# Copyright (c) 2026-present Maciej Szymczak and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from plane.app.permissions import ROLE, allow_permission
from plane.app.views.base import BaseAPIView
from plane.db.models import Issue, ProjectMember, Workspace, WorkspaceMember
from plane.ext.models.customer import Customer, CustomerRequest, CustomerWorkItemLink, WorkspaceFeature
from plane.ext.serializers.customer import (
    CustomerRequestSerializer,
    CustomerSerializer,
    CustomerWorkItemLinkActionSerializer,
    IssueCustomerSerializer,
)


def _workspace(slug):
    return Workspace.objects.filter(slug=slug).first()


def _features(workspace):
    feature, _ = WorkspaceFeature.objects.get_or_create(workspace=workspace)
    return feature


def _customers_enabled(workspace):
    return WorkspaceFeature.objects.filter(workspace=workspace, is_customers_enabled=True).exists()


def _feature_disabled():
    return Response({"error": "Customers is not enabled for this workspace."}, status=status.HTTP_403_FORBIDDEN)


def _customer_queryset(workspace):
    return (
        Customer.objects.filter(workspace=workspace)
        .select_related("logo_asset")
        .annotate(customer_request_count=Count("requests", filter=Q(requests__deleted_at__isnull=True)))
    )


def _visible_issues(user, workspace, issue_ids):
    if not issue_ids:
        return Issue.objects.none()
    if WorkspaceMember.objects.filter(workspace=workspace, member=user, role=ROLE.ADMIN.value, is_active=True).exists():
        return Issue.objects.filter(workspace=workspace, id__in=issue_ids, archived_at__isnull=True)
    project_ids = ProjectMember.objects.filter(
        workspace=workspace, member=user, is_active=True
    ).values_list("project_id", flat=True)
    return Issue.objects.filter(
        workspace=workspace,
        id__in=issue_ids,
        project_id__in=project_ids,
        archived_at__isnull=True,
        project__archived_at__isnull=True,
    )


class CustomerFeatureEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def get(self, request, slug):
        workspace = _workspace(slug)
        if workspace is None:
            return Response({"error": "Workspace not found."}, status=status.HTTP_404_NOT_FOUND)
        feature = _features(workspace)
        return Response(
            {
                "is_customers_enabled": feature.is_customers_enabled,
                "customers_enabled_at": feature.customers_enabled_at,
            },
            status=status.HTTP_200_OK,
        )

    @allow_permission([ROLE.ADMIN], level="WORKSPACE")
    def patch(self, request, slug):
        workspace = _workspace(slug)
        if workspace is None:
            return Response({"error": "Workspace not found."}, status=status.HTTP_404_NOT_FOUND)
        enabled = request.data.get("is_customers_enabled")
        if not isinstance(enabled, bool):
            return Response({"error": "Send is_customers_enabled as a boolean."}, status=status.HTTP_400_BAD_REQUEST)
        feature = _features(workspace)
        feature.is_customers_enabled = enabled
        if enabled and feature.customers_enabled_at is None:
            feature.customers_enabled_at = timezone.now()
        if not enabled:
            feature.customers_enabled_at = None
        feature.save()
        return Response(
            {
                "is_customers_enabled": feature.is_customers_enabled,
                "customers_enabled_at": feature.customers_enabled_at,
            },
            status=status.HTTP_200_OK,
        )


class CustomerListCreateEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def get(self, request, slug):
        workspace = _workspace(slug)
        if workspace is None:
            return Response({"error": "Workspace not found."}, status=status.HTTP_404_NOT_FOUND)
        if not _customers_enabled(workspace):
            return _feature_disabled()
        queryset = _customer_queryset(workspace)
        search = (request.GET.get("search") or "").strip()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(email__icontains=search) | Q(domain__icontains=search)
            )
        if request.GET.get("archived") == "true":
            queryset = queryset.filter(archived_at__isnull=False)
        else:
            queryset = queryset.filter(archived_at__isnull=True)
        return Response(CustomerSerializer(queryset, many=True).data, status=status.HTTP_200_OK)

    @allow_permission([ROLE.ADMIN], level="WORKSPACE")
    def post(self, request, slug):
        workspace = _workspace(slug)
        if workspace is None:
            return Response({"error": "Workspace not found."}, status=status.HTTP_404_NOT_FOUND)
        if not _customers_enabled(workspace):
            return _feature_disabled()
        serializer = CustomerSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            customer = serializer.save(workspace=workspace)
        except IntegrityError:
            return Response({"error": "A customer with this name already exists."}, status=status.HTTP_409_CONFLICT)
        customer = _customer_queryset(workspace).get(pk=customer.pk)
        return Response(CustomerSerializer(customer).data, status=status.HTTP_201_CREATED)


class CustomerUpsertEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN], level="WORKSPACE")
    def post(self, request, slug):
        workspace = _workspace(slug)
        if workspace is None:
            return Response({"error": "Workspace not found."}, status=status.HTTP_404_NOT_FOUND)
        if not _customers_enabled(workspace):
            return _feature_disabled()
        serializer = CustomerSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        external_source = (data.get("external_source") or "").strip() or None
        external_id = (data.get("external_id") or "").strip() or None
        existing = None
        if external_source and external_id:
            existing = Customer.objects.filter(
                workspace=workspace, external_source=external_source, external_id=external_id
            ).first()
        if existing is None:
            existing = Customer.objects.filter(workspace=workspace, name=data["name"]).first()
        if existing is None:
            customer = serializer.save(workspace=workspace, external_source=external_source, external_id=external_id)
            created = True
        else:
            serializer = CustomerSerializer(existing, data=request.data, partial=True)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            customer = serializer.save()
            created = False
        customer = _customer_queryset(workspace).get(pk=customer.pk)
        return Response(
            CustomerSerializer(customer).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class CustomerDetailEndpoint(BaseAPIView):
    def _get(self, slug, pk):
        workspace = _workspace(slug)
        if workspace is None:
            return None, Response({"error": "Workspace not found."}, status=status.HTTP_404_NOT_FOUND)
        if not _customers_enabled(workspace):
            return None, _feature_disabled()
        customer = _customer_queryset(workspace).filter(pk=pk).first()
        if customer is None:
            return None, Response({"error": "Customer not found."}, status=status.HTTP_404_NOT_FOUND)
        return customer, None

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def get(self, request, slug, pk):
        customer, error = self._get(slug, pk)
        if error is not None:
            return error
        return Response(CustomerSerializer(customer).data, status=status.HTTP_200_OK)

    @allow_permission([ROLE.ADMIN], level="WORKSPACE")
    def patch(self, request, slug, pk):
        customer, error = self._get(slug, pk)
        if error is not None:
            return error
        serializer = CustomerSerializer(customer, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            serializer.save()
        except IntegrityError:
            return Response({"error": "A customer with this name already exists."}, status=status.HTTP_409_CONFLICT)
        customer = _customer_queryset(customer.workspace).get(pk=customer.pk)
        return Response(CustomerSerializer(customer).data, status=status.HTTP_200_OK)

    @allow_permission([ROLE.ADMIN], level="WORKSPACE")
    def delete(self, request, slug, pk):
        customer, error = self._get(slug, pk)
        if error is not None:
            return error
        customer.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomerRequestListCreateEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def get(self, request, slug, customer_id):
        workspace = _workspace(slug)
        if workspace is None:
            return Response({"error": "Workspace not found."}, status=status.HTTP_404_NOT_FOUND)
        if not _customers_enabled(workspace):
            return _feature_disabled()
        customer = get_object_or_404(Customer, workspace=workspace, pk=customer_id)
        requests = CustomerRequest.objects.filter(customer=customer, archived_at__isnull=True)
        return Response(CustomerRequestSerializer(requests, many=True).data, status=status.HTTP_200_OK)

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def post(self, request, slug, customer_id):
        workspace = _workspace(slug)
        if workspace is None:
            return Response({"error": "Workspace not found."}, status=status.HTTP_404_NOT_FOUND)
        if not _customers_enabled(workspace):
            return _feature_disabled()
        customer = get_object_or_404(Customer, workspace=workspace, pk=customer_id)
        serializer = CustomerRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        work_item_ids = serializer.validated_data.pop("work_item_ids", [])
        with transaction.atomic():
            customer_request = serializer.save(workspace=workspace, customer=customer)
            _link_work_items(
                request.user, workspace, customer, customer_request, add=work_item_ids, remove=[]
            )
        return Response(CustomerRequestSerializer(customer_request).data, status=status.HTTP_201_CREATED)


class CustomerRequestDetailEndpoint(BaseAPIView):
    def _get(self, slug, customer_id, pk):
        workspace = _workspace(slug)
        if workspace is None:
            return None, None, Response({"error": "Workspace not found."}, status=status.HTTP_404_NOT_FOUND)
        if not _customers_enabled(workspace):
            return None, None, _feature_disabled()
        customer = Customer.objects.filter(workspace=workspace, pk=customer_id).first()
        if customer is None:
            return None, None, Response({"error": "Customer not found."}, status=status.HTTP_404_NOT_FOUND)
        customer_request = CustomerRequest.objects.filter(customer=customer, pk=pk).first()
        if customer_request is None:
            return None, None, Response({"error": "Customer request not found."}, status=status.HTTP_404_NOT_FOUND)
        return customer, customer_request, None

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def get(self, request, slug, customer_id, pk):
        _, customer_request, error = self._get(slug, customer_id, pk)
        if error is not None:
            return error
        return Response(CustomerRequestSerializer(customer_request).data, status=status.HTTP_200_OK)

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def patch(self, request, slug, customer_id, pk):
        _, customer_request, error = self._get(slug, customer_id, pk)
        if error is not None:
            return error
        serializer = CustomerRequestSerializer(customer_request, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        work_item_ids = serializer.validated_data.pop("work_item_ids", None)
        serializer.save()
        if work_item_ids is not None:
            existing = list(
                CustomerWorkItemLink.objects.filter(customer_request=customer_request).values_list(
                    "issue_id", flat=True
                )
            )
            _link_work_items(
                request.user,
                customer_request.workspace,
                customer_request.customer,
                customer_request,
                add=work_item_ids,
                remove=existing,
            )
        return Response(CustomerRequestSerializer(customer_request).data, status=status.HTTP_200_OK)

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def delete(self, request, slug, customer_id, pk):
        _, customer_request, error = self._get(slug, customer_id, pk)
        if error is not None:
            return error
        customer_request.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def _link_work_items(user, workspace, customer, customer_request, add, remove):
    added, removed = [], []
    visible_add = set(_visible_issues(user, workspace, add).values_list("id", flat=True)) if add else set()
    for issue_id in visible_add:
        _, created = CustomerWorkItemLink.objects.get_or_create(
            workspace=workspace,
            customer=customer,
            issue_id=issue_id,
            customer_request=customer_request,
        )
        if created:
            added.append(issue_id)
    if remove:
        deleted = CustomerWorkItemLink.objects.filter(
            customer=customer,
            issue_id__in=remove,
            customer_request=customer_request,
        ).delete()
        if deleted:
            removed = list(remove)
    return added, removed


class CustomerWorkItemsEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def get(self, request, slug, pk):
        workspace = _workspace(slug)
        if workspace is None:
            return Response({"error": "Workspace not found."}, status=status.HTTP_404_NOT_FOUND)
        if not _customers_enabled(workspace):
            return _feature_disabled()
        customer = get_object_or_404(Customer, workspace=workspace, pk=pk)
        links = CustomerWorkItemLink.objects.filter(customer=customer).select_related("issue")
        request_id = request.GET.get("customer_request_id")
        if request_id:
            links = links.filter(customer_request_id=request_id)
        issue_ids = list(links.values_list("issue_id", flat=True))
        issues = _visible_issues(request.user, workspace, issue_ids).order_by("-created_at", "id")
        payload = [
            {
                "id": str(issue.id),
                "name": issue.name,
                "sequence_id": issue.sequence_id,
                "project_id": str(issue.project_id),
                "priority": issue.priority,
                "created_at": issue.created_at,
            }
            for issue in issues
        ]
        return Response(payload, status=status.HTTP_200_OK)

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def post(self, request, slug, pk):
        workspace = _workspace(slug)
        if workspace is None:
            return Response({"error": "Workspace not found."}, status=status.HTTP_404_NOT_FOUND)
        if not _customers_enabled(workspace):
            return _feature_disabled()
        customer = get_object_or_404(Customer, workspace=workspace, pk=pk)
        serializer = CustomerWorkItemLinkActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        customer_request = None
        request_id = serializer.validated_data.get("customer_request_id")
        if request_id:
            customer_request = get_object_or_404(CustomerRequest, customer=customer, pk=request_id)
        added, removed = _link_work_items(
            request.user,
            workspace,
            customer,
            customer_request,
            add=serializer.validated_data.get("add") or [],
            remove=serializer.validated_data.get("remove") or [],
        )
        return Response(
            {"added": [str(i) for i in added], "removed": [str(i) for i in removed]},
            status=status.HTTP_200_OK,
        )


class IssueCustomersEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def get(self, request, slug, project_id, issue_id):
        workspace = _workspace(slug)
        if workspace is None:
            return Response({"error": "Workspace not found."}, status=status.HTTP_404_NOT_FOUND)
        if not _customers_enabled(workspace):
            return Response([], status=status.HTTP_200_OK)
        issue = get_object_or_404(Issue, workspace=workspace, project_id=project_id, pk=issue_id)
        links = (
            CustomerWorkItemLink.objects.filter(issue=issue)
            .select_related("customer", "customer_request")
            .order_by("customer__name")
        )
        return Response(IssueCustomerSerializer(links, many=True).data, status=status.HTTP_200_OK)

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def post(self, request, slug, project_id, issue_id):
        workspace = _workspace(slug)
        if workspace is None:
            return Response({"error": "Workspace not found."}, status=status.HTTP_404_NOT_FOUND)
        if not _customers_enabled(workspace):
            return _feature_disabled()
        issue = get_object_or_404(Issue, workspace=workspace, project_id=project_id, pk=issue_id)
        serializer = CustomerWorkItemLinkActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        added, removed = [], []
        for customer_id in serializer.validated_data.get("add") or []:
            customer = Customer.objects.filter(workspace=workspace, pk=customer_id).first()
            if customer is None:
                continue
            _, created = CustomerWorkItemLink.objects.get_or_create(
                workspace=workspace, customer=customer, issue=issue, customer_request=None
            )
            if created:
                added.append(customer_id)
        remove_ids = serializer.validated_data.get("remove") or []
        if remove_ids:
            CustomerWorkItemLink.objects.filter(issue=issue, customer_id__in=remove_ids).delete()
            removed = list(remove_ids)
        return Response(
            {"added": [str(i) for i in added], "removed": [str(i) for i in removed]},
            status=status.HTTP_200_OK,
        )
