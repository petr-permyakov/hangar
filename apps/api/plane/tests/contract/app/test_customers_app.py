# Copyright (c) 2026-present Maciej Szymczak and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from uuid import uuid4

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from plane.db.models import Issue, Project, ProjectMember, State, User, WorkspaceMember
from plane.ext.models.customer import Customer, CustomerRequest, CustomerWorkItemLink, WorkspaceFeature


@pytest.fixture
def project(db, workspace, create_user):
    project = Project.objects.create(
        name="Customers Project",
        identifier="CUS",
        workspace=workspace,
        created_by=create_user,
    )
    ProjectMember.objects.create(project=project, member=create_user, role=20, is_active=True)
    return project


@pytest.fixture
def state(db, project, workspace):
    return State.objects.create(
        name="Todo", group="unstarted", color="#fff", project=project, workspace=workspace, default=True
    )


@pytest.fixture
def issue(db, project, workspace, state):
    return Issue.objects.create(name="Checkout redesign", project=project, workspace=workspace, state=state)


def features_url(workspace):
    return f"/api/workspaces/{workspace.slug}/customer-features/"


def customers_url(workspace):
    return f"/api/workspaces/{workspace.slug}/customers/"


def enable_customers(workspace):
    return WorkspaceFeature.objects.create(workspace=workspace, is_customers_enabled=True)


def make_role_client(workspace, role):
    uid = uuid4().hex[:8]
    user = User.objects.create(email=f"user-{uid}@hangar.test", username=f"user_{uid}")
    WorkspaceMember.objects.create(workspace=workspace, member=user, role=role, is_active=True)
    client = APIClient()
    client.force_authenticate(user=user)
    return client, user


@pytest.mark.contract
class TestCustomerFeatureGate:
    @pytest.mark.django_db
    def test_disabled_blocks_list_and_create(self, session_client, workspace):
        listing = session_client.get(customers_url(workspace))
        assert listing.status_code == status.HTTP_403_FORBIDDEN

        created = session_client.post(customers_url(workspace), {"name": "Acme"}, format="json")
        assert created.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_admin_can_enable(self, session_client, workspace):
        response = session_client.patch(features_url(workspace), {"is_customers_enabled": True}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_customers_enabled"] is True
        assert WorkspaceFeature.objects.get(workspace=workspace).is_customers_enabled is True

    @pytest.mark.django_db
    def test_member_cannot_enable(self, workspace):
        client, _ = make_role_client(workspace, role=15)
        response = client.patch(features_url(workspace), {"is_customers_enabled": True}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_guest_cannot_read_features(self, workspace):
        client, _ = make_role_client(workspace, role=5)
        response = client.get(features_url(workspace))
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.contract
class TestCustomerCRUD:
    @pytest.mark.django_db
    def test_create_list_update_delete(self, session_client, workspace):
        enable_customers(workspace)
        created = session_client.post(
            customers_url(workspace),
            {
                "name": "Acme",
                "email": "ana@acme.test",
                "website_url": "https://acme.test",
                "domain": "Manufacturing",
                "stage": "customer",
                "contract_status": "active",
                "revenue": "4.2M",
                "employees": 250,
            },
            format="json",
        )
        assert created.status_code == status.HTTP_201_CREATED
        assert created.data["name"] == "Acme"
        assert created.data["domain"] == "Manufacturing"
        assert created.data["customer_request_count"] == 0
        customer_id = created.data["id"]

        listing = session_client.get(customers_url(workspace))
        assert listing.status_code == status.HTTP_200_OK
        assert len(listing.data) == 1

        updated = session_client.patch(
            f"{customers_url(workspace)}{customer_id}/",
            {"stage": "closed_won"},
            format="json",
        )
        assert updated.status_code == status.HTTP_200_OK
        assert updated.data["stage"] == "closed_won"

        deleted = session_client.delete(f"{customers_url(workspace)}{customer_id}/")
        assert deleted.status_code == status.HTTP_204_NO_CONTENT
        assert session_client.get(customers_url(workspace)).data == []

    @pytest.mark.django_db
    def test_duplicate_name_conflicts(self, session_client, workspace):
        enable_customers(workspace)
        session_client.post(customers_url(workspace), {"name": "Acme"}, format="json")
        duplicate = session_client.post(customers_url(workspace), {"name": "Acme"}, format="json")
        assert duplicate.status_code == status.HTTP_409_CONFLICT

    @pytest.mark.django_db
    def test_member_can_read_but_not_create(self, workspace):
        enable_customers(workspace)
        Customer.objects.create(workspace=workspace, name="Acme")
        client, _ = make_role_client(workspace, role=15)
        assert client.get(customers_url(workspace)).status_code == status.HTTP_200_OK
        created = client.post(customers_url(workspace), {"name": "Beta"}, format="json")
        assert created.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_guest_cannot_list(self, workspace):
        enable_customers(workspace)
        client, _ = make_role_client(workspace, role=5)
        assert client.get(customers_url(workspace)).status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_name_is_required(self, session_client, workspace):
        enable_customers(workspace)
        response = session_client.post(customers_url(workspace), {"email": "a@b.test"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_upsert_matches_external_id_then_name(self, session_client, workspace):
        enable_customers(workspace)
        first = session_client.post(
            f"{customers_url(workspace)}upsert/",
            {"name": "Acme", "external_source": "crm", "external_id": "acme-1", "stage": "lead"},
            format="json",
        )
        assert first.status_code == status.HTTP_201_CREATED
        second = session_client.post(
            f"{customers_url(workspace)}upsert/",
            {"name": "Acme Inc", "external_source": "crm", "external_id": "acme-1", "stage": "customer"},
            format="json",
        )
        assert second.status_code == status.HTTP_200_OK
        assert second.data["id"] == first.data["id"]
        assert second.data["stage"] == "customer"
        assert Customer.objects.filter(workspace=workspace).count() == 1


@pytest.mark.contract
class TestCustomerRequestsAndLinks:
    @pytest.mark.django_db
    def test_create_request_and_link_work_item(self, session_client, workspace, issue):
        enable_customers(workspace)
        customer = Customer.objects.create(workspace=workspace, name="Acme")
        created = session_client.post(
            f"{customers_url(workspace)}{customer.id}/requests/",
            {
                "name": "Faster checkout",
                "link": "https://mail.example/thread/1",
                "work_item_ids": [str(issue.id)],
            },
            format="json",
        )
        assert created.status_code == status.HTTP_201_CREATED
        assert created.data["name"] == "Faster checkout"
        assert created.data["link"] == "https://mail.example/thread/1"

        items = session_client.get(
            f"{customers_url(workspace)}{customer.id}/work-items/?customer_request_id={created.data['id']}"
        )
        assert items.status_code == status.HTTP_200_OK
        assert len(items.data) == 1
        assert items.data[0]["id"] == str(issue.id)

        linked = session_client.get(
            f"/api/workspaces/{workspace.slug}/projects/{issue.project_id}/issues/{issue.id}/customers/"
        )
        assert linked.status_code == status.HTTP_200_OK
        assert linked.data[0]["customer_id"] == str(customer.id)
        assert linked.data[0]["customer_request_name"] == "Faster checkout"

    @pytest.mark.django_db
    def test_direct_link_add_remove(self, session_client, workspace, issue):
        enable_customers(workspace)
        customer = Customer.objects.create(workspace=workspace, name="Acme")
        linked = session_client.post(
            f"{customers_url(workspace)}{customer.id}/work-items/",
            {"add": [str(issue.id)], "remove": []},
            format="json",
        )
        assert linked.status_code == status.HTTP_200_OK
        assert str(issue.id) in linked.data["added"]
        assert CustomerWorkItemLink.objects.filter(
            customer=customer, issue=issue, customer_request__isnull=True
        ).exists()

        unlinked = session_client.post(
            f"{customers_url(workspace)}{customer.id}/work-items/",
            {"add": [], "remove": [str(issue.id)]},
            format="json",
        )
        assert unlinked.status_code == status.HTTP_200_OK
        assert not CustomerWorkItemLink.objects.filter(customer=customer, issue=issue).exists()

    @pytest.mark.django_db
    def test_rejects_non_https_source_link(self, session_client, workspace):
        enable_customers(workspace)
        customer = Customer.objects.create(workspace=workspace, name="Acme")
        created = session_client.post(
            f"{customers_url(workspace)}{customer.id}/requests/",
            {"name": "Ask", "link": "javascript:alert(1)"},
            format="json",
        )
        assert created.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_member_can_create_request(self, workspace, issue):
        enable_customers(workspace)
        customer = Customer.objects.create(workspace=workspace, name="Acme")
        client, user = make_role_client(workspace, role=15)
        ProjectMember.objects.create(project=issue.project, member=user, role=15, is_active=True)
        created = client.post(
            f"{customers_url(workspace)}{customer.id}/requests/",
            {"name": "Ask", "work_item_ids": [str(issue.id)]},
            format="json",
        )
        assert created.status_code == status.HTTP_201_CREATED
        assert CustomerRequest.objects.filter(customer=customer).count() == 1

    @pytest.mark.django_db
    def test_issue_customers_empty_when_disabled(self, session_client, workspace, issue):
        response = session_client.get(
            f"/api/workspaces/{workspace.slug}/projects/{issue.project_id}/issues/{issue.id}/customers/"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    @pytest.mark.django_db
    def test_guest_cannot_create_request(self, workspace):
        enable_customers(workspace)
        customer = Customer.objects.create(workspace=workspace, name="Acme")
        client, _ = make_role_client(workspace, role=5)
        created = client.post(
            f"{customers_url(workspace)}{customer.id}/requests/",
            {"name": "Ask"},
            format="json",
        )
        assert created.status_code == status.HTTP_403_FORBIDDEN
