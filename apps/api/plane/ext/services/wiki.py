# Copyright (c) 2026-present Maciej Szymczak and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""Rules for the workspace wiki.

A wiki page is an upstream ``Page`` with ``is_global=True`` and no project.
Visibility is decided here: public collections, private collections, and
shares. Workspace admins do not see a private page or a private collection
unless they own it or were added to it.
"""

import html
import secrets
from django.contrib.postgres.aggregates import ArrayAgg
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from plane.db.models import Page, Sticky, UserFavorite, UserRecentVisit, Workspace, WorkspaceMember
from plane.utils.content_validator import validate_html_content
from plane.utils.html_processor import strip_tags
from plane.utils.visibility_policy import force_private_visibility

from plane.ext.models.wiki import (
    LINK_CREATED_BY,
    LINK_PARENT,
    PRIVATE,
    PUBLIC,
    ROLE_COMMENT,
    ROLE_EDIT,
    ROLE_VIEW,
    WikiCollection,
    WikiCollectionMember,
    WikiLabel,
    WikiLinkBlock,
    WikiPageComment,
    WikiPageLabel,
    WikiPageLink,
    WikiPageShare,
    WikiPageTemplate,
    WikiPublication,
    WikiSettings,
)

FAVORITE_TYPE = "wiki-page"
RECENT_TYPE = "wiki-page"
ROLES = {ROLE_VIEW, ROLE_COMMENT, ROLE_EDIT}
MEMBER = 15
ADMIN = 20
GUEST = 5


class WikiError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


def workspace_or_404(slug):
    workspace = Workspace.objects.filter(slug=slug).first()
    if workspace is None:
        raise WikiError("Workspace not found.", 404)
    return workspace


def role_of(user, workspace):
    membership = WorkspaceMember.objects.filter(workspace=workspace, member=user, is_active=True).first()
    if membership is None:
        return None
    return membership.role


def require_member(user, workspace):
    role = role_of(user, workspace)
    if role is None or role <= GUEST:
        raise WikiError("You don't have permission to open the wiki.", 403)
    return role


def settings_for(workspace):
    row, _created = WikiSettings.objects.get_or_create(workspace=workspace)
    return row


def wiki_is_enabled(workspace):
    return settings_for(workspace).is_enabled


def require_enabled(workspace, *, status=403):
    if not wiki_is_enabled(workspace):
        raise WikiError("Wiki is turned off for this workspace.", status)


def ensure_general(workspace, user):
    existing = WikiCollection.objects.filter(workspace=workspace, is_default=True).first()
    if existing:
        return existing
    return WikiCollection.objects.create(
        workspace=workspace,
        name="General",
        access=PUBLIC,
        is_default=True,
        owned_by=user,
        sort_order=0,
    )


def _sanitize(value):
    if not value:
        return "<p></p>"
    is_valid, error_message, sanitized = validate_html_content(value)
    if not is_valid:
        raise WikiError(error_message or "Page content was rejected.", 400)
    return sanitized if sanitized is not None else value


def plain_to_html(text):
    chunks = [html.escape(line) for line in (text or "").splitlines()] or [""]
    return _sanitize("".join(f"<p>{line or '<br>'}</p>" for line in chunks))


def user_brief(user):
    if user is None:
        return None
    return {
        "id": str(user.id),
        "display_name": user.display_name or user.email,
        "email": user.email,
    }


def root_page(page):
    seen = set()
    current = page
    while current.parent_id and current.id not in seen:
        seen.add(current.id)
        parent = Page.objects.filter(id=current.parent_id, workspace_id=page.workspace_id, is_global=True).first()
        if parent is None:
            break
        current = parent
    return current


def descendants(page):
    found = []
    frontier = [page.id]
    while frontier:
        children = list(
            Page.objects.filter(parent_id__in=frontier, workspace_id=page.workspace_id, is_global=True).values_list(
                "id", flat=True
            )
        )
        found.extend(children)
        frontier = children
    return found


def collection_for(page):
    root = root_page(page)
    link = WikiPageLink.objects.filter(page=root).select_related("collection").first()
    return link.collection if link else None


def collection_role(user, collection):
    if collection.access == PUBLIC:
        role = role_of(user, collection.workspace)
        if role is not None and role > GUEST:
            return ROLE_EDIT
        return None
    if collection.owned_by_id == user.id:
        return ROLE_EDIT
    membership = WikiCollectionMember.objects.filter(collection=collection, member=user).first()
    return membership.role if membership else None


def share_for(user, page):
    root = root_page(page)
    return WikiPageShare.objects.filter(page=root, member=user).first()


def can_read(user, page):
    if not page.is_global:
        return False
    if require_member_silent(user, page.workspace_id) is None:
        return False
    root = root_page(page)
    collection = collection_for(root)
    if root.access == PUBLIC:
        if collection is None or collection.access == PUBLIC:
            return True
        return collection_role(user, collection) is not None
    if root.owned_by_id == user.id:
        return True
    if share_for(user, root) is not None:
        return True
    if collection is not None and collection.access == PRIVATE and collection_role(user, collection) is not None:
        return True
    return False


def require_member_silent(user, workspace_id):
    membership = WorkspaceMember.objects.filter(workspace_id=workspace_id, member=user, is_active=True).first()
    if membership is None or membership.role <= GUEST:
        return None
    return membership.role


def can_edit(user, page):
    if page.is_locked or page.archived_at:
        return False
    if not can_read(user, page):
        return False
    root = root_page(page)
    if root.owned_by_id == user.id:
        return True
    collection = collection_for(root)
    if root.access == PUBLIC and (collection is None or collection.access == PUBLIC):
        return True
    share = share_for(user, root)
    if share is not None and share.role == ROLE_EDIT:
        return True
    if collection is not None and collection_role(user, collection) == ROLE_EDIT:
        return True
    return False


def can_comment(user, page):
    if page.archived_at or not can_read(user, page):
        return False
    if can_edit(user, page) or (page.is_locked and root_page(page).owned_by_id == user.id):
        return True
    root = root_page(page)
    share = share_for(user, root)
    if share is not None and share.role in {ROLE_COMMENT, ROLE_EDIT}:
        return True
    collection = collection_for(root)
    if collection is not None and collection_role(user, collection) in {ROLE_COMMENT, ROLE_EDIT}:
        return True
    if root.access == PUBLIC and (collection is None or collection.access == PUBLIC):
        return True
    return False


def can_manage(user, page):
    """Lock, archive, delete, move, publish. Admins only for pages they can see."""
    if not can_read(user, page):
        return False
    root = root_page(page)
    if root.owned_by_id == user.id:
        return True
    return require_member_silent(user, page.workspace_id) == ADMIN


def can_share(user, page):
    root = root_page(page)
    if page.id != root.id or root.owned_by_id != user.id:
        return False
    if root.access != PRIVATE:
        return False
    collection = collection_for(root)
    if collection is not None and collection.access == PRIVATE:
        role = require_member_silent(user, page.workspace_id)
        return role == ADMIN or collection_role(user, collection) == ROLE_EDIT
    return True


def can_relabel(user, page):
    if page.is_locked or page.archived_at or not can_read(user, page):
        return False
    root = root_page(page)
    if root.owned_by_id == user.id:
        return True
    return require_member_silent(user, page.workspace_id) == ADMIN


def _require_page(workspace, page_id):
    page = Page.objects.filter(id=page_id, workspace=workspace, is_global=True).first()
    if page is None:
        raise WikiError("Page not found.", 404)
    return page


def _require_readable(user, page):
    if not can_read(user, page):
        raise WikiError("Page not found.", 404)
    return page


def label_ids(page):
    return [str(value) for value in WikiPageLabel.objects.filter(page=page).values_list("label_id", flat=True)]


def page_payload(page, user, *, include_body=True):
    root = root_page(page)
    collection = collection_for(page)
    share = share_for(user, root)
    payload = {
        "id": str(page.id),
        "name": page.name,
        "access": page.access,
        "is_locked": page.is_locked,
        "is_global": True,
        "archived_at": page.archived_at.isoformat() if page.archived_at else None,
        "parent_id": str(page.parent_id) if page.parent_id else None,
        "owned_by_id": str(page.owned_by_id),
        "owned_by": user_brief(page.owned_by),
        "collection_id": str(collection.id) if collection else None,
        "sort_order": page.sort_order,
        "logo_props": page.logo_props or {},
        "label_ids": label_ids(page),
        "created_at": page.created_at,
        "updated_at": page.updated_at,
        "project_ids": [],
        "can_edit": can_edit(user, page),
        "can_comment": can_comment(user, page),
        "can_manage": can_manage(user, page),
        "can_share": can_share(user, page),
        "share_role": share.role if share else None,
        "is_favorite": UserFavorite.objects.filter(
            user=user, workspace_id=page.workspace_id, entity_type=FAVORITE_TYPE, entity_identifier=page.id
        ).exists(),
        "child_count": Page.objects.filter(parent=page, is_global=True).count(),
    }
    if include_body:
        payload["description_html"] = page.description_html
        payload["description_stripped"] = page.description_stripped
    return payload


def collection_payload(collection, user):
    return {
        "id": str(collection.id),
        "name": collection.name,
        "access": collection.access,
        "is_default": collection.is_default,
        "is_global": True,
        "logo_props": collection.logo_props or {},
        "sort_order": collection.sort_order,
        "owned_by_id": str(collection.owned_by_id),
        "owned_by": user_brief(collection.owned_by),
        "page_ids": [
            str(value)
            for value in WikiPageLink.objects.filter(collection=collection, page__archived_at__isnull=True).values_list(
                "page_id", flat=True
            )
        ],
        "my_role": collection_role(user, collection),
        "created_at": collection.created_at,
        "updated_at": collection.updated_at,
    }


def visible_collections(user, workspace):
    rows = []
    for collection in WikiCollection.objects.filter(workspace=workspace).select_related("owned_by"):
        if collection_role(user, collection) is not None:
            rows.append(collection)
    return rows


def _set_access(page, access):
    ids = [page.id, *descendants(page)]
    Page.objects.filter(id__in=ids).update(access=access, updated_at=timezone.now())
    page.access = access


def _link(page, collection):
    link = WikiPageLink.objects.filter(page=page).first()
    if link:
        link.collection = collection
        link.workspace = page.workspace
        link.save(update_fields=["collection", "workspace", "updated_at"])
        return link
    return WikiPageLink.objects.create(page=page, collection=collection, workspace=page.workspace)


def _clear_shares(page):
    WikiPageShare.objects.filter(page=root_page(page)).delete()


def create_page(user, workspace, data):
    require_member(user, workspace)
    require_enabled(workspace)
    general = ensure_general(workspace, user)
    parent = None
    parent_id = data.get("parent_id")
    if parent_id:
        parent = _require_readable(user, _require_page(workspace, parent_id))
        if not can_edit(user, parent):
            raise WikiError("You can't add a page here.", 403)
    template = None
    if data.get("template_id"):
        template = WikiPageTemplate.objects.filter(id=data["template_id"], workspace=workspace).first()
        if template is None:
            raise WikiError("Template not found.", 404)
    requested_access = PRIVATE if force_private_visibility() else int(data.get("access", PUBLIC))
    if requested_access not in (PUBLIC, PRIVATE):
        raise WikiError("Access must be public or private.", 400)
    description = data.get("description_html")
    if description is None and data.get("description") is not None:
        description = plain_to_html(data.get("description"))
    elif template and not description:
        description = template.description_html
    description = _sanitize(description or "<p></p>")
    name = (data.get("name") or (template.name if template else "") or "")[:10000]
    with transaction.atomic():
        page = Page.objects.create(
            workspace=workspace,
            name=name,
            owned_by=user,
            access=PRIVATE if parent is None and requested_access == PRIVATE else PUBLIC,
            is_global=True,
            parent=parent,
            description_html=description,
        )
        if parent is not None:
            root = root_page(parent)
            page.access = root.access
            page.save(update_fields=["access"])
            collection = collection_for(root)
            if collection is not None and page.id == root.id:
                _link(page, collection)
        else:
            collection = None
            collection_id = data.get("collection_id")
            if collection_id:
                collection = WikiCollection.objects.filter(id=collection_id, workspace=workspace).first()
                if collection is None or collection_role(user, collection) is None:
                    raise WikiError("Collection not found.", 404)
                if collection.access == PRIVATE and collection_role(user, collection) != ROLE_EDIT:
                    raise WikiError("You need edit access to add a page to this collection.", 403)
            if requested_access == PRIVATE and collection is None:
                page.access = PRIVATE
                page.save(update_fields=["access"])
            elif collection is not None and collection.access == PRIVATE:
                page.access = PRIVATE
                page.save(update_fields=["access"])
                _link(page, collection)
            else:
                target = collection or general
                if target.access != PUBLIC:
                    raise WikiError("A public page has to live in a public collection.", 400)
                page.access = PUBLIC if not force_private_visibility() else PRIVATE
                page.save(update_fields=["access"])
                if page.access == PUBLIC:
                    _link(page, target)
        if data.get("label_ids"):
            _replace_labels(workspace, page, data["label_ids"])
    page.refresh_from_db()
    return page_payload(page, user)


def update_page(user, workspace, page_id, data):
    page = _require_readable(user, _require_page(workspace, page_id))
    if page.archived_at:
        raise WikiError("Archived pages can't be edited.", 400)
    content_fields = {"name", "description_html", "description", "logo_props", "sort_order"}
    if content_fields.intersection(data) and not can_edit(user, page):
        raise WikiError("You can't edit this page.", 403)
    if "name" in data:
        page.name = data.get("name") or ""
    if "description_html" in data:
        page.description_html = _sanitize(data.get("description_html"))
    elif "description" in data:
        page.description_html = plain_to_html(data.get("description"))
    if "logo_props" in data and isinstance(data["logo_props"], dict):
        page.logo_props = data["logo_props"]
    if "sort_order" in data:
        page.sort_order = data["sort_order"]
    page.save()
    if "label_ids" in data:
        if not can_relabel(user, page):
            raise WikiError("You can't change this page's labels.", 403)
        _replace_labels(workspace, page, data["label_ids"])
    if "access" in data:
        set_access(user, page, int(data["access"]))
    page.refresh_from_db()
    return page_payload(page, user)


def _replace_labels(workspace, page, raw_ids):
    if not isinstance(raw_ids, list):
        raise WikiError("label_ids must be a list.", 400)
    labels = list(WikiLabel.objects.filter(workspace=workspace, id__in=raw_ids))
    if len(labels) != len(set(raw_ids)):
        raise WikiError("One of those labels is not in this workspace.", 400)
    WikiPageLabel.objects.filter(page=page).delete()
    WikiPageLabel.objects.bulk_create([WikiPageLabel(page=page, label=label, workspace=workspace) for label in labels])


def set_access(user, page, access):
    root = root_page(page)
    if root.owned_by_id != user.id or page.id != root.id:
        raise WikiError("Only the page owner can change who can see it.", 403)
    if access not in (PUBLIC, PRIVATE):
        raise WikiError("Access must be public or private.", 400)
    if force_private_visibility() and access == PUBLIC:
        raise WikiError("This instance does not allow public pages.", 403)
    collection = collection_for(root)
    if collection is not None and collection.access == PRIVATE and access == PUBLIC:
        raise WikiError("Remove the page from its private collection before making it public.", 409)
    with transaction.atomic():
        if access == PRIVATE:
            _set_access(root, PRIVATE)
            if collection is not None and collection.access == PUBLIC:
                WikiPageLink.objects.filter(page=root).delete()
        else:
            _set_access(root, PUBLIC)
            _clear_shares(root)
            if collection is None or collection.access != PUBLIC:
                _link(root, ensure_general(root.workspace, user))


def set_locked(user, page, locked):
    if not can_manage(user, page):
        raise WikiError("You can't lock this page.", 403)
    ids = [page.id]
    ids.extend(descendants(page))
    Page.objects.filter(id__in=ids).update(is_locked=locked, updated_at=timezone.now())


def archive_page(user, workspace, page_id, archived):
    page = _require_readable(user, _require_page(workspace, page_id))
    if not can_manage(user, page):
        raise WikiError("You can't archive this page.", 403)
    root = root_page(page)
    if archived:
        when = timezone.now().date()
        ids = [page.id, *descendants(page)]
        Page.objects.filter(id__in=ids).update(archived_at=when)
        WikiPublication.objects.filter(page_id__in=ids).delete()
        UserFavorite.objects.filter(entity_type=FAVORITE_TYPE, entity_identifier__in=ids).delete()
        return
    if page.parent_id:
        parent = Page.objects.filter(id=page.parent_id).first()
        if parent and parent.archived_at:
            page.parent = None
            page.save(update_fields=["parent"])
    Page.objects.filter(id__in=[page.id, *descendants(page)]).update(archived_at=None)
    if root.access == PUBLIC and collection_for(root) is None:
        _link(root, ensure_general(workspace, user))


def delete_page(user, workspace, page_id):
    page = _require_readable(user, _require_page(workspace, page_id))
    if not page.archived_at:
        raise WikiError("Archive a page before deleting it.", 409)
    if not can_manage(user, page):
        raise WikiError("You can't delete this page.", 403)
    ids = [page.id, *descendants(page)]
    for child in Page.objects.filter(id__in=ids):
        WikiPublication.objects.filter(page=child).delete()
        child.delete()


def move_page(user, workspace, page_id, collection_id, confirm):
    page = _require_readable(user, _require_page(workspace, page_id))
    root = root_page(page)
    if root.id != page.id:
        raise WikiError("Move the top-level page. Nested pages follow it.", 400)
    collection = None
    if collection_id:
        collection = WikiCollection.objects.filter(id=collection_id, workspace=workspace).first()
        if collection is None or collection_role(user, collection) is None:
            raise WikiError("Collection not found.", 404)
        if (
            collection.access == PRIVATE
            and collection_role(user, collection) != ROLE_EDIT
            and role_of(user, workspace) != ADMIN
        ):
            raise WikiError("You need edit access on that collection.", 403)
    if not _can_move(user, page, collection):
        raise WikiError("You can't move this page.", 403)
    current = collection_for(root)
    changes_visibility = _visibility_changes(root, current, collection)
    if changes_visibility and not confirm:
        raise WikiError("This move changes who can see the page. Confirm it and try again.", 409)
    with transaction.atomic():
        if collection is None:
            WikiPageLink.objects.filter(page=root).delete()
            _set_access(root, PRIVATE)
        elif collection.access == PUBLIC:
            _set_access(root, PUBLIC)
            _clear_shares(root)
            _link(root, collection)
        else:
            _set_access(root, PRIVATE)
            _link(root, collection)
    root.refresh_from_db()
    return page_payload(root, user)


def _can_move(user, page, target):
    if can_manage(user, page):
        return True
    if not can_edit(user, page):
        return False
    current = collection_for(root_page(page))
    current_public = page.access == PUBLIC and (current is None or current.access == PUBLIC)
    target_public = target is not None and target.access == PUBLIC
    return current_public and target_public


def _visibility_changes(page, current, target):
    current_private = page.access == PRIVATE or (current is not None and current.access == PRIVATE)
    target_private = target is None or target.access == PRIVATE
    if current_private != target_private:
        return True
    if current is not None and target is not None and current.id != target.id and current.access == PRIVATE:
        return True
    return False


def share_page(user, workspace, page_id, member_id, role):
    page = _require_readable(user, _require_page(workspace, page_id))
    if not can_share(user, page):
        raise WikiError("Only the owner of a top-level private page can share it.", 403)
    if role not in ROLES:
        raise WikiError("Role must be view, comment, or edit.", 400)
    member = (
        WorkspaceMember.objects.filter(workspace=workspace, member_id=member_id, is_active=True, role__gt=GUEST)
        .select_related("member")
        .first()
    )
    if member is None:
        raise WikiError("That person is not a member of this workspace.", 400)
    if str(member.member_id) == str(page.owned_by_id):
        raise WikiError("The owner already has access.", 400)
    share, _created = WikiPageShare.objects.get_or_create(
        page=root_page(page),
        member_id=member_id,
        defaults={"workspace": workspace, "role": role},
    )
    if share.role != role:
        share.role = role
        share.save(update_fields=["role", "updated_at"])
    return {"id": str(share.id), "member": user_brief(share.member), "role": share.role}


def unshare_page(user, workspace, page_id, member_id):
    page = _require_readable(user, _require_page(workspace, page_id))
    if not can_share(user, page):
        raise WikiError("Only the owner can change sharing.", 403)
    WikiPageShare.objects.filter(page=root_page(page), member_id=member_id).delete()


def list_shares(user, page):
    if not can_read(user, page):
        raise WikiError("Page not found.", 404)
    root = root_page(page)
    return [
        {"id": str(share.id), "member": user_brief(share.member), "role": share.role}
        for share in WikiPageShare.objects.filter(page=root).select_related("member")
    ]


def create_collection(user, workspace, data):
    role = require_member(user, workspace)
    require_enabled(workspace)
    ensure_general(workspace, user)
    name = (data.get("name") or "").strip()
    if not name:
        raise WikiError("Collection title is required.", 400)
    if len(name) > 255:
        raise WikiError("Collection name must be less than 255 characters.", 400)
    access = int(data.get("access", PUBLIC))
    if access not in (PUBLIC, PRIVATE):
        raise WikiError("Visibility must be public or private.", 400)
    if access == PRIVATE and role != ADMIN:
        raise WikiError("Only workspace admins can create a private collection.", 403)
    last = WikiCollection.objects.filter(workspace=workspace).order_by("-sort_order").first()
    collection = WikiCollection.objects.create(
        workspace=workspace,
        name=name,
        access=access,
        owned_by=user,
        sort_order=(last.sort_order + 10000) if last else 65535,
        logo_props=data.get("logo_props") if isinstance(data.get("logo_props"), dict) else {},
    )
    if access == PRIVATE:
        WikiCollectionMember.objects.create(collection=collection, member=user, workspace=workspace, role=ROLE_EDIT)
    return collection_payload(collection, user)


def update_collection(user, workspace, collection_id, data):
    collection = _editable_collection(user, workspace, collection_id)
    if "access" in data and int(data["access"]) != collection.access:
        raise WikiError("A collection's visibility can't be changed after it's created.", 400)
    if collection.is_default and data.get("name") and data["name"] != collection.name:
        collection.name = data["name"].strip()
    elif "name" in data:
        name = (data.get("name") or "").strip()
        if not name or len(name) > 255:
            raise WikiError("Collection name must be under 255 characters.", 400)
        collection.name = name
    if "logo_props" in data and isinstance(data["logo_props"], dict):
        collection.logo_props = data["logo_props"]
    if "sort_order" in data:
        collection.sort_order = data["sort_order"]
    collection.save()
    return collection_payload(collection, user)


def _editable_collection(user, workspace, collection_id):
    require_member(user, workspace)
    collection = WikiCollection.objects.filter(id=collection_id, workspace=workspace).first()
    if collection is None or collection_role(user, collection) is None:
        raise WikiError("Collection not found.", 404)
    role = role_of(user, workspace)
    if collection.owned_by_id != user.id and role != ADMIN:
        raise WikiError("Only the collection owner or a workspace admin can change it.", 403)
    return collection


def delete_collection(user, workspace, collection_id, mode):
    collection = _editable_collection(user, workspace, collection_id)
    if collection.is_default:
        raise WikiError("The General collection can't be deleted.", 400)
    pages = [link.page for link in WikiPageLink.objects.filter(collection=collection).select_related("page")]
    with transaction.atomic():
        if collection.access == PRIVATE or mode == "archive":
            when = timezone.now().date()
            for page in pages:
                Page.objects.filter(id__in=[page.id, *descendants(page)]).update(archived_at=when)
                WikiPageLink.objects.filter(page=page).delete()
        else:
            general = ensure_general(workspace, user)
            for page in pages:
                _link(page, general)
        collection.delete()


def set_collection_member(user, workspace, collection_id, member_id, role):
    collection = WikiCollection.objects.filter(id=collection_id, workspace=workspace).first()
    if collection is None:
        raise WikiError("Collection not found.", 404)
    actor_role = role_of(user, workspace)
    if collection.owned_by_id != user.id and actor_role != ADMIN:
        raise WikiError("Only the collection owner or a workspace admin can manage members.", 403)
    if collection.access != PRIVATE:
        raise WikiError("Public collections are visible to every member.", 400)
    if role not in ROLES:
        raise WikiError("Role must be view, comment, or edit.", 400)
    membership = WorkspaceMember.objects.filter(
        workspace=workspace, member_id=member_id, is_active=True, role__gt=GUEST
    ).first()
    if membership is None:
        raise WikiError("That person is not a member of this workspace.", 400)
    row, _created = WikiCollectionMember.objects.get_or_create(
        collection=collection,
        member_id=member_id,
        defaults={"workspace": workspace, "role": role},
    )
    if row.role != role:
        row.role = role
        row.save(update_fields=["role", "updated_at"])
    return {"member_id": str(member_id), "role": row.role}


def remove_collection_member(user, workspace, collection_id, member_id):
    collection = WikiCollection.objects.filter(id=collection_id, workspace=workspace).first()
    if collection is None:
        raise WikiError("Collection not found.", 404)
    if collection.owned_by_id != user.id and role_of(user, workspace) != ADMIN:
        raise WikiError("Only the collection owner or a workspace admin can manage members.", 403)
    if str(collection.owned_by_id) == str(member_id):
        raise WikiError("The collection owner can't be removed.", 400)
    WikiCollectionMember.objects.filter(collection=collection, member_id=member_id).delete()


def change_collection_pages(user, workspace, collection_id, add_ids, remove_ids, confirm):
    collection = WikiCollection.objects.filter(id=collection_id, workspace=workspace).select_related("owned_by").first()
    if collection is None or collection_role(user, collection) is None:
        raise WikiError("Collection not found.", 404)
    if (
        collection.access == PRIVATE
        and collection_role(user, collection) != ROLE_EDIT
        and role_of(user, workspace) != ADMIN
    ):
        raise WikiError("You need edit access on that collection.", 403)
    added, removed = [], []
    for page_id in add_ids or []:
        payload = move_page(user, workspace, page_id, collection.id, confirm)
        added.append(payload["id"])
    for page_id in remove_ids or []:
        page = _require_readable(user, _require_page(workspace, page_id))
        root = root_page(page)
        if collection.access == PUBLIC:
            move_page(user, workspace, root.id, ensure_general(workspace, user).id, confirm=True)
        else:
            move_page(user, workspace, root.id, None, confirm)
        removed.append(str(root.id))
    return {"added": added, "removed": removed}


def remember_visit(user, page):
    UserRecentVisit.objects.update_or_create(
        workspace_id=page.workspace_id,
        user=user,
        entity_name=RECENT_TYPE,
        entity_identifier=page.id,
        defaults={"visited_at": timezone.now()},
    )


def toggle_favorite(user, page, on):
    if not can_read(user, page):
        raise WikiError("Page not found.", 404)
    existing = UserFavorite.objects.filter(
        user=user, workspace_id=page.workspace_id, entity_type=FAVORITE_TYPE, entity_identifier=page.id
    ).first()
    if on and existing is None:
        UserFavorite.objects.create(
            user=user,
            workspace_id=page.workspace_id,
            entity_type=FAVORITE_TYPE,
            entity_identifier=page.id,
            name=page.name or "Untitled",
        )
    if not on and existing is not None:
        existing.delete()


def sidebar(user, workspace):
    require_member(user, workspace)
    require_enabled(workspace)
    ensure_general(workspace, user)
    collections = []
    for collection in visible_collections(user, workspace):
        roots = [
            link.page
            for link in WikiPageLink.objects.filter(
                collection=collection, page__parent__isnull=True, page__archived_at__isnull=True
            ).select_related("page", "page__owned_by")
        ]
        collections.append(
            {
                **collection_payload(collection, user),
                "pages": [_tree_node(page, user) for page in roots],
            }
        )
    private_roots = []
    shared_roots = []
    loose = Page.objects.filter(
        workspace=workspace, is_global=True, parent__isnull=True, archived_at__isnull=True, access=PRIVATE
    ).select_related("owned_by")
    for page in loose:
        if not can_read(user, page) or collection_for(page) is not None:
            continue
        if page.owned_by_id == user.id:
            private_roots.append(_tree_node(page, user))
        else:
            shared_roots.append(_tree_node(page, user))
    favorites = []
    for favorite in UserFavorite.objects.filter(user=user, workspace=workspace, entity_type=FAVORITE_TYPE):
        page = Page.objects.filter(id=favorite.entity_identifier, workspace=workspace, is_global=True).first()
        if page and can_read(user, page) and not page.archived_at:
            favorites.append(page_payload(page, user, include_body=False))
    recents = _recents(user, workspace)
    archived = []
    for page in Page.objects.filter(
        workspace=workspace, is_global=True, archived_at__isnull=False, parent__isnull=True
    ).select_related("owned_by"):
        if can_read(user, page):
            archived.append(page_payload(page, user, include_body=False))
    return {
        "enabled": True,
        "forced_private": force_private_visibility(),
        "collections": collections,
        "private": private_roots,
        "shared": shared_roots,
        "favorites": favorites,
        "recents": recents,
        "archived": archived,
    }


def _tree_node(page, user):
    children = Page.objects.filter(parent=page, is_global=True, archived_at__isnull=True).select_related("owned_by")
    node = page_payload(page, user, include_body=False)
    node["children"] = [_tree_node(child, user) for child in children if can_read(user, child)]
    return node


def _recents(user, workspace):
    visits = UserRecentVisit.objects.filter(workspace=workspace, user=user, entity_name=RECENT_TYPE).order_by(
        "-visited_at"
    )[:12]
    rows = []
    for visit in visits:
        page = (
            Page.objects.filter(id=visit.entity_identifier, workspace=workspace, is_global=True)
            .select_related("owned_by")
            .first()
        )
        if page and can_read(user, page) and not page.archived_at:
            payload = page_payload(page, user, include_body=False)
            payload["visited_at"] = visit.visited_at
            rows.append(payload)
    return rows


def list_pages(user, workspace, filters):
    require_member(user, workspace)
    require_enabled(workspace)
    ensure_general(workspace, user)
    query = (filters.get("search") or "").strip()
    rows = []
    pages = Page.objects.filter(workspace=workspace, is_global=True).select_related("owned_by")
    if filters.get("archived") in ("1", "true"):
        pages = pages.filter(archived_at__isnull=False)
    else:
        pages = pages.filter(archived_at__isnull=True)
    if query:
        pages = pages.filter(name__icontains=query)
    for page in pages.order_by("sort_order", "name"):
        if not can_read(user, page):
            continue
        collection = collection_for(page)
        if filters.get("collection_id") and (collection is None or str(collection.id) != filters["collection_id"]):
            continue
        if filters.get("access") not in (None, "") and str(page.access) != str(filters["access"]):
            continue
        rows.append(page_payload(page, user, include_body=False))
    return rows


def add_comment(user, workspace, page_id, data):
    page = _require_readable(user, _require_page(workspace, page_id))
    if not can_comment(user, page):
        raise WikiError("You can't comment on this page.", 403)
    body = _sanitize(data.get("comment_html") or plain_to_html(data.get("comment") or ""))
    comment = WikiPageComment.objects.create(
        page=page,
        workspace=workspace,
        actor=user,
        comment_html=body,
        comment_stripped=strip_tags(body) or "",
    )
    return _comment_payload(comment)


def list_comments(user, page):
    if not can_read(user, page):
        raise WikiError("Page not found.", 404)
    return [_comment_payload(row) for row in WikiPageComment.objects.filter(page=page).select_related("actor")]


def _comment_payload(comment):
    return {
        "id": str(comment.id),
        "comment_html": comment.comment_html,
        "comment_stripped": comment.comment_stripped,
        "actor": user_brief(comment.actor),
        "created_at": comment.created_at,
    }


def upsert_label(user, workspace, data, label_id=None):
    if role_of(user, workspace) != ADMIN:
        raise WikiError("Only workspace admins can manage page labels.", 403)
    name = (data.get("name") or "").strip()
    if not name or len(name) > 255:
        raise WikiError("Label name is required.", 400)
    clash = WikiLabel.objects.filter(workspace=workspace, name__iexact=name)
    if label_id:
        clash = clash.exclude(id=label_id)
    if clash.exists():
        raise WikiError("A page label with that name already exists.", 409)
    if label_id:
        label = WikiLabel.objects.filter(id=label_id, workspace=workspace).first()
        if label is None:
            raise WikiError("Label not found.", 404)
        label.name = name
        if "color" in data:
            label.color = data.get("color") or ""
        label.save()
    else:
        label = WikiLabel.objects.create(workspace=workspace, name=name, color=data.get("color") or "")
    return {"id": str(label.id), "name": label.name, "color": label.color}


def delete_label(user, workspace, label_id):
    if role_of(user, workspace) != ADMIN:
        raise WikiError("Only workspace admins can manage page labels.", 403)
    label = WikiLabel.objects.filter(id=label_id, workspace=workspace).first()
    if label is None:
        raise WikiError("Label not found.", 404)
    label.delete()


def list_labels(workspace):
    return [
        {"id": str(label.id), "name": label.name, "color": label.color}
        for label in WikiLabel.objects.filter(workspace=workspace).order_by("name")
    ]


def create_template(user, workspace, data):
    if role_of(user, workspace) != ADMIN:
        raise WikiError("Only workspace admins can manage templates.", 403)
    name = (data.get("name") or "").strip()
    if not name:
        raise WikiError("Template name is required.", 400)
    template = WikiPageTemplate.objects.create(
        workspace=workspace,
        name=name,
        description_html=_sanitize(data.get("description_html") or "<p></p>"),
        owned_by=user,
    )
    return {"id": str(template.id), "name": template.name, "description_html": template.description_html}


def list_templates(workspace):
    return [
        {"id": str(row.id), "name": row.name, "description_html": row.description_html}
        for row in WikiPageTemplate.objects.filter(workspace=workspace)
    ]


def publish_page(user, workspace, page_id):
    page = _require_readable(user, _require_page(workspace, page_id))
    if not can_manage(user, page):
        raise WikiError("You can't publish this page.", 403)
    if force_private_visibility():
        raise WikiError("This instance does not publish pages.", 403)
    if page.archived_at:
        raise WikiError("Archived pages are not published.", 400)
    ids = [root_page(page).id, *descendants(root_page(page))]
    created = None
    for current_id in ids:
        current = Page.objects.get(id=current_id)
        publication = WikiPublication.objects.filter(page=current).first()
        if publication is None:
            publication = WikiPublication.objects.create(
                page=current,
                workspace=workspace,
                anchor=secrets.token_hex(16),
                published_by=user,
            )
        if current.id == page.id:
            created = publication
    return {"anchor": created.anchor, "path": f"/wiki/published/{created.anchor}"}


def unpublish_page(user, workspace, page_id):
    page = _require_readable(user, _require_page(workspace, page_id))
    if not can_manage(user, page):
        raise WikiError("You can't unpublish this page.", 403)
    WikiPublication.objects.filter(page_id__in=[page.id, *descendants(page)]).delete()


def published_page(workspace, anchor):
    publication = WikiPublication.objects.filter(workspace=workspace, anchor=anchor).select_related("page").first()
    if publication is None or publication.page.archived_at:
        raise WikiError("Published page not found.", 404)
    page = publication.page
    return {
        "id": str(page.id),
        "name": page.name,
        "description_html": page.description_html,
        "description_stripped": page.description_stripped,
        "anchor": publication.anchor,
        "collection_id": None,
        "project_ids": [],
        "is_global": True,
    }


def analytics(user, page):
    if not can_read(user, page):
        raise WikiError("Page not found.", 404)
    viewers = (
        UserRecentVisit.objects.filter(entity_name=RECENT_TYPE, entity_identifier=page.id)
        .values("user_id")
        .distinct()
        .count()
    )
    return {
        "viewers": viewers,
        "nested_pages": len(descendants(page)),
        "comments": WikiPageComment.objects.filter(page=page).count(),
    }


def create_link_block(user, workspace, page_id, data):
    page = _require_readable(user, _require_page(workspace, page_id))
    if not can_edit(user, page):
        raise WikiError("You can't edit this page.", 403)
    source = data.get("source") or LINK_PARENT
    if source not in (LINK_PARENT, LINK_CREATED_BY):
        raise WikiError("Source must be parent or created_by.", 400)
    source_page = None
    if source == LINK_PARENT:
        source_page = _require_readable(user, _require_page(workspace, data.get("source_page_id") or page_id))
    level = int(data.get("nesting_level") or 0)
    if level < 0 or level > 6:
        raise WikiError("Nesting level must be between 0 and 6.", 400)
    block = WikiLinkBlock.objects.create(
        page=page,
        workspace=workspace,
        source=source,
        source_page=source_page,
        member_ids=data.get("member_ids") if isinstance(data.get("member_ids"), list) else [],
        nesting_level=level,
    )
    return resolve_link_block(user, block)


def list_link_blocks(user, page):
    if not can_read(user, page):
        raise WikiError("Page not found.", 404)
    return [resolve_link_block(user, block) for block in WikiLinkBlock.objects.filter(page=page)]


def resolve_link_block(user, block):
    pages = []
    if block.source == LINK_PARENT and block.source_page_id:
        depth = block.nesting_level or None
        frontier = [(block.source_page, 0)]
        while frontier:
            current, level = frontier.pop(0)
            children = Page.objects.filter(parent=current, is_global=True, archived_at__isnull=True)
            for child in children:
                next_level = level + 1
                if depth is not None and next_level > depth:
                    continue
                if can_read(user, child):
                    pages.append(page_payload(child, user, include_body=False))
                frontier.append((child, next_level))
    else:
        wanted = {str(value) for value in (block.member_ids or [])}
        candidates = Page.objects.filter(workspace_id=block.workspace_id, is_global=True, archived_at__isnull=True)
        for page in candidates:
            if str(page.owned_by_id) in wanted and can_read(user, page):
                pages.append(page_payload(page, user, include_body=False))
    return {
        "id": str(block.id),
        "source": block.source,
        "source_page_id": str(block.source_page_id) if block.source_page_id else None,
        "nesting_level": block.nesting_level,
        "member_ids": block.member_ids,
        "pages": pages,
    }


def delete_link_block(user, workspace, page_id, block_id):
    page = _require_readable(user, _require_page(workspace, page_id))
    if not can_edit(user, page):
        raise WikiError("You can't edit this page.", 403)
    WikiLinkBlock.objects.filter(id=block_id, page=page).delete()


def workspace_members(workspace):
    memberships = WorkspaceMember.objects.filter(workspace=workspace, is_active=True, role__gt=GUEST).select_related(
        "member"
    )
    return [user_brief(row.member) for row in memberships]


def command_search_pages(user, slug, query, count):
    """Pages for the command menu: project pages, plus wiki pages the caller can open."""
    limit = count or 10
    name_filter = Q()
    if query:
        name_filter = Q(name__icontains=query)
    project_rows = (
        Page.objects.filter(
            name_filter,
            projects__project_projectmember__member=user,
            projects__project_projectmember__is_active=True,
            workspace__slug=slug,
            is_global=False,
        )
        .filter(Q(access=PUBLIC) | Q(owned_by=user))
        .annotate(
            project_ids=ArrayAgg("projects__id", distinct=True, order_by="projects__id"),
            project__identifiers=ArrayAgg("projects__identifier", distinct=True, order_by="projects__identifier"),
        )
        .order_by("-created_at")
        .distinct()
        .values("name", "id", "workspace__slug", "project_ids", "project__identifiers")[:limit]
    )
    results = []
    for row in project_rows:
        results.append(
            {
                "name": row["name"],
                "id": row["id"],
                "workspace__slug": row["workspace__slug"],
                "project_ids": [str(value) for value in (row["project_ids"] or []) if value],
                "project__identifiers": [value for value in (row["project__identifiers"] or []) if value],
            }
        )
    workspace = Workspace.objects.filter(slug=slug).first()
    if workspace is None or not wiki_is_enabled(workspace):
        return results
    if require_member_silent(user, workspace.id) is None:
        return results
    remaining = max(limit - len(results), 0)
    if remaining == 0:
        return results
    wiki_pages = Page.objects.filter(
        name_filter, workspace=workspace, is_global=True, archived_at__isnull=True
    ).order_by("-updated_at")
    for page in wiki_pages:
        if not can_read(user, page):
            continue
        results.append(
            {
                "name": page.name,
                "id": page.id,
                "workspace__slug": slug,
                "project_ids": [],
                "project__identifiers": [],
            }
        )
        if len(results) >= limit:
            break
    return results


def sticky_payload(sticky):
    return {
        "id": str(sticky.id),
        "name": sticky.name,
        "description_html": sticky.description_html,
        "description_stripped": sticky.description_stripped,
        "color": sticky.color,
        "background_color": sticky.background_color,
        "logo_props": sticky.logo_props,
        "owner_id": str(sticky.owner_id),
        "sort_order": sticky.sort_order,
        "created_at": sticky.created_at,
        "updated_at": sticky.updated_at,
        "created_by_id": str(sticky.created_by_id) if sticky.created_by_id else None,
        "updated_by_id": str(sticky.updated_by_id) if sticky.updated_by_id else None,
    }


def list_stickies(user, workspace):
    require_member_or_guest(user, workspace)
    return [sticky_payload(row) for row in Sticky.objects.filter(workspace=workspace, owner=user)]


def require_member_or_guest(user, workspace):
    if role_of(user, workspace) is None:
        raise WikiError("You don't have permission.", 403)


def create_sticky(user, workspace, data):
    require_member_or_guest(user, workspace)
    description = _sanitize(data.get("description_html") or "<p></p>")
    sticky = Sticky.objects.create(
        workspace=workspace,
        owner=user,
        name=data.get("name") or "",
        description_html=description,
        color=data.get("color") or "",
        background_color=data.get("background_color") or "",
    )
    return sticky_payload(sticky)


def update_sticky(user, workspace, sticky_id, data):
    sticky = Sticky.objects.filter(id=sticky_id, workspace=workspace, owner=user).first()
    if sticky is None:
        raise WikiError("Sticky not found.", 404)
    if "description_html" in data:
        sticky.description_html = _sanitize(data.get("description_html"))
    if "name" in data:
        sticky.name = data.get("name") or ""
    if "color" in data:
        sticky.color = data.get("color") or ""
    if "background_color" in data:
        sticky.background_color = data.get("background_color") or ""
    if "sort_order" in data:
        sticky.sort_order = data["sort_order"]
    sticky.save()
    return sticky_payload(sticky)


def delete_sticky(user, workspace, sticky_id):
    sticky = Sticky.objects.filter(id=sticky_id, workspace=workspace, owner=user).first()
    if sticky is None:
        raise WikiError("Sticky not found.", 404)
    sticky.delete()
