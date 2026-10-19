# Copyright (c) 2026-present Maciej Szymczak and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from uuid import uuid4

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from plane.db.models import User, WorkspaceMember
from plane.ext.models.wiki import WikiCollection, WikiSettings


def pages_url(workspace):
    return f"/api/workspaces/{workspace.slug}/wiki/pages/"


def settings_url(workspace):
    return f"/api/workspaces/{workspace.slug}/wiki/settings/"


def make_role_client(workspace, role):
    uid = uuid4().hex[:8]
    user = User.objects.create(email=f"wiki-{uid}@hangar.test", username=f"wiki_{uid}", display_name=f"Wiki {uid}")
    WorkspaceMember.objects.create(workspace=workspace, member=user, role=role, is_active=True)
    client = APIClient()
    client.force_authenticate(user=user)
    return client, user


@pytest.mark.contract
class TestWiki:
    @pytest.mark.django_db
    def test_guest_cannot_open_the_wiki(self, workspace):
        client, _user = make_role_client(workspace, role=5)
        response = client.get(pages_url(workspace))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_turning_the_wiki_off_hides_pages_and_returns_402_on_v2(self, session_client, workspace):
        created = session_client.post(pages_url(workspace), {"name": "Handbook"}, format="json")
        assert created.status_code == status.HTTP_201_CREATED

        turned_off = session_client.patch(settings_url(workspace), {"is_enabled": False}, format="json")
        assert turned_off.status_code == status.HTTP_200_OK
        assert session_client.get(pages_url(workspace)).status_code == status.HTTP_403_FORBIDDEN

        v2 = session_client.get(f"/api/v2/workspaces/{workspace.slug}/pages/")
        assert v2.status_code == status.HTTP_402_PAYMENT_REQUIRED

        member, _user = make_role_client(workspace, role=15)
        assert member.patch(settings_url(workspace), {"is_enabled": True}, format="json").status_code == (
            status.HTTP_403_FORBIDDEN
        )

    @pytest.mark.django_db
    def test_new_page_lands_in_general_and_is_visible_to_members(self, session_client, workspace):
        created = session_client.post(
            pages_url(workspace), {"name": "Onboarding", "description": "Welcome"}, format="json"
        )
        assert created.status_code == status.HTTP_201_CREATED
        assert created.data["access"] == 0
        assert created.data["is_global"] is True
        assert created.data["project_ids"] == []
        assert created.data["collection_id"]

        general = WikiCollection.objects.get(workspace=workspace, is_default=True)
        assert created.data["collection_id"] == str(general.id)
        assert general.name == "General"

        member, _user = make_role_client(workspace, role=15)
        listing = member.get(pages_url(workspace))
        assert listing.status_code == status.HTTP_200_OK
        assert any(row["name"] == "Onboarding" for row in listing.data)

        sidebar = member.get(f"/api/workspaces/{workspace.slug}/wiki/sidebar/")
        assert sidebar.status_code == status.HTTP_200_OK
        names = [collection["name"] for collection in sidebar.data["collections"]]
        assert "General" in names

    @pytest.mark.django_db
    def test_private_page_is_shared_and_hidden_from_everyone_else(self, session_client, workspace, create_user):
        member, member_user = make_role_client(workspace, role=15)
        outsider, _outsider = make_role_client(workspace, role=15)
        created = session_client.post(pages_url(workspace), {"name": "Salary notes", "access": 1}, format="json")
        assert created.status_code == status.HTTP_201_CREATED
        page_id = created.data["id"]
        assert created.data["collection_id"] is None

        assert outsider.get(f"{pages_url(workspace)}{page_id}/").status_code == status.HTTP_404_NOT_FOUND

        shared = session_client.post(
            f"{pages_url(workspace)}{page_id}/shares/",
            {"member_id": str(member_user.id), "role": "comment"},
            format="json",
        )
        assert shared.status_code == status.HTTP_200_OK
        assert member.get(f"{pages_url(workspace)}{page_id}/").status_code == status.HTTP_200_OK
        assert (
            member.post(
                f"{pages_url(workspace)}{page_id}/comments/",
                {"comment": "Noted"},
                format="json",
            ).status_code
            == status.HTTP_201_CREATED
        )
        assert (
            member.patch(
                f"{pages_url(workspace)}{page_id}/",
                {"description": "rewrite"},
                format="json",
            ).status_code
            == status.HTTP_403_FORBIDDEN
        )

        sidebar = member.get(f"/api/workspaces/{workspace.slug}/wiki/sidebar/")
        assert any(page["id"] == page_id for page in sidebar.data["shared"])
        assert page_id not in {page["id"] for page in sidebar.data["private"]}

        owner_sidebar = session_client.get(f"/api/workspaces/{workspace.slug}/wiki/sidebar/")
        assert any(page["id"] == page_id for page in owner_sidebar.data["private"])
        assert create_user.id

    @pytest.mark.django_db
    def test_private_collection_is_invisible_to_admins_who_were_not_added(self, session_client, workspace):
        admin, _admin = make_role_client(workspace, role=20)
        created = session_client.post(
            f"/api/workspaces/{workspace.slug}/wiki/collections/",
            {"name": "HR", "access": 1},
            format="json",
        )
        assert created.status_code == status.HTTP_201_CREATED
        collection_id = created.data["id"]

        visible = admin.get(f"/api/workspaces/{workspace.slug}/wiki/collections/")
        assert collection_id not in {row["id"] for row in visible.data}

        member, member_user = make_role_client(workspace, role=15)
        assert (
            member.post(
                f"/api/workspaces/{workspace.slug}/wiki/collections/",
                {"name": "Secret", "access": 1},
                format="json",
            ).status_code
            == status.HTTP_403_FORBIDDEN
        )

        added = session_client.post(
            f"/api/workspaces/{workspace.slug}/wiki/collections/{collection_id}/members/",
            {"member_id": str(member_user.id), "role": "view"},
            format="json",
        )
        assert added.status_code == status.HTTP_200_OK
        assert any(
            row["id"] == collection_id for row in member.get(f"/api/workspaces/{workspace.slug}/wiki/collections/").data
        )

    @pytest.mark.django_db
    def test_moving_into_a_public_collection_drops_shares(self, session_client, workspace):
        member, member_user = make_role_client(workspace, role=15)
        created = session_client.post(pages_url(workspace), {"name": "Draft", "access": 1}, format="json")
        page_id = created.data["id"]
        session_client.post(
            f"{pages_url(workspace)}{page_id}/shares/",
            {"member_id": str(member_user.id), "role": "edit"},
            format="json",
        )
        general = WikiCollection.objects.get(workspace=workspace, is_default=True)
        refused = session_client.post(
            f"{pages_url(workspace)}{page_id}/move/",
            {"collection_id": str(general.id)},
            format="json",
        )
        assert refused.status_code == status.HTTP_409_CONFLICT

        moved = session_client.post(
            f"{pages_url(workspace)}{page_id}/move/",
            {"collection_id": str(general.id), "confirm": True},
            format="json",
        )
        assert moved.status_code == status.HTTP_200_OK
        assert moved.data["access"] == 0
        shares = session_client.get(f"{pages_url(workspace)}{page_id}/shares/")
        assert shares.data == []

    @pytest.mark.django_db
    def test_archive_is_required_before_delete_and_nested_pages_follow(self, session_client, workspace):
        parent = session_client.post(pages_url(workspace), {"name": "Handbook"}, format="json").data
        child = session_client.post(
            pages_url(workspace),
            {"name": "Benefits", "parent_id": parent["id"]},
            format="json",
        )
        assert child.status_code == status.HTTP_201_CREATED
        assert child.data["access"] == 0
        assert child.data["collection_id"] == parent["collection_id"]

        blocked = session_client.delete(f"{pages_url(workspace)}{parent['id']}/")
        assert blocked.status_code == status.HTTP_409_CONFLICT

        assert session_client.post(f"{pages_url(workspace)}{parent['id']}/archive/").status_code == (
            status.HTTP_204_NO_CONTENT
        )
        child_after = session_client.get(f"{pages_url(workspace)}{child.data['id']}/")
        assert child_after.data["archived_at"]

        assert session_client.delete(f"{pages_url(workspace)}{parent['id']}/").status_code == status.HTTP_204_NO_CONTENT
        assert session_client.get(f"{pages_url(workspace)}{child.data['id']}/").status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_labels_link_blocks_and_v2_collection_membership(self, session_client, workspace):
        label = session_client.post(
            f"/api/workspaces/{workspace.slug}/wiki/labels/",
            {"name": "Runbook", "color": "#3f76ff"},
            format="json",
        )
        assert label.status_code == status.HTTP_201_CREATED
        page = session_client.post(
            pages_url(workspace),
            {"name": "Deploy", "label_ids": [label.data["id"]]},
            format="json",
        ).data
        assert page["label_ids"] == [label.data["id"]]

        block = session_client.post(
            f"{pages_url(workspace)}{page['id']}/link-blocks/",
            {"source": "parent", "source_page_id": page["id"], "nesting_level": 1},
            format="json",
        )
        assert block.status_code == status.HTTP_201_CREATED

        collection = session_client.post(
            f"/api/workspaces/{workspace.slug}/wiki/collections/",
            {"name": "Engineering", "access": 0},
            format="json",
        ).data
        moved = session_client.post(
            f"/api/v2/workspaces/{workspace.slug}/collections/{collection['id']}/pages/",
            {"add": [page["id"]], "remove": []},
            format="json",
        )
        assert moved.status_code == status.HTTP_200_OK
        assert page["id"] in moved.data["added"]

        listing = session_client.get(f"/api/v2/workspaces/{workspace.slug}/pages/?fields=id,name,collection_id")
        assert listing.status_code == status.HTTP_200_OK
        row = next(item for item in listing.data["data"] if item["id"] == page["id"])
        assert set(row) == {"id", "name", "collection_id"}
        assert row["collection_id"] == collection["id"]

    @pytest.mark.django_db
    def test_general_collection_cannot_be_deleted(self, session_client, workspace):
        session_client.post(pages_url(workspace), {"name": "Keep"}, format="json")
        general = WikiCollection.objects.get(workspace=workspace, is_default=True)
        response = session_client.delete(f"/api/workspaces/{workspace.slug}/wiki/collections/{general.id}/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert WikiSettings.objects.get(workspace=workspace).is_enabled is True

    @pytest.mark.django_db
    def test_v2_stickies_are_private_to_the_caller(self, session_client, workspace):
        created = session_client.post(
            f"/api/v2/workspaces/{workspace.slug}/stickies/",
            {"name": "Remember", "description_html": "<p>Ship the wiki</p>"},
            format="json",
        )
        assert created.status_code == status.HTTP_201_CREATED
        other, _user = make_role_client(workspace, role=15)
        listing = other.get(f"/api/v2/workspaces/{workspace.slug}/stickies/")
        assert listing.status_code == status.HTTP_200_OK
        assert listing.data["data"] == []
