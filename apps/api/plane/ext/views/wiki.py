# Copyright (c) 2026-present Maciej Szymczak and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""Workspace wiki HTTP API, plus the v2 shapes Plane documents for pages, collections, and stickies."""

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from plane.app.permissions import ROLE, allow_permission
from plane.app.views.base import BaseAPIView

from plane.ext.services import wiki as wiki_service
from plane.ext.services.wiki import WikiError


def _call(fn):
    try:
        return fn()
    except WikiError as exc:
        return Response({"error": exc.message}, status=exc.status)


class WikiSettingsEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def get(self, request, slug):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            row = wiki_service.settings_for(workspace)
            return Response(
                {"is_enabled": row.is_enabled, "forced_private": wiki_service.force_private_visibility()},
                status=status.HTTP_200_OK,
            )

        return _call(run)

    @allow_permission([ROLE.ADMIN], level="WORKSPACE")
    def patch(self, request, slug):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            if "is_enabled" not in request.data:
                raise WikiError("Send is_enabled.", 400)
            row = wiki_service.settings_for(workspace)
            row.is_enabled = bool(request.data.get("is_enabled"))
            row.save(update_fields=["is_enabled", "updated_at"])
            if row.is_enabled:
                wiki_service.ensure_general(workspace, request.user)
            return Response({"is_enabled": row.is_enabled}, status=status.HTTP_200_OK)

        return _call(run)


class WikiSidebarEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def get(self, request, slug):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            return Response(wiki_service.sidebar(request.user, workspace), status=status.HTTP_200_OK)

        return _call(run)


class WikiPageListCreateEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def get(self, request, slug):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            return Response(
                wiki_service.list_pages(request.user, workspace, request.query_params),
                status=status.HTTP_200_OK,
            )

        return _call(run)

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def post(self, request, slug):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            return Response(
                wiki_service.create_page(request.user, workspace, request.data), status=status.HTTP_201_CREATED
            )

        return _call(run)


class WikiPageDetailEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def get(self, request, slug, page_id):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            wiki_service.require_enabled(workspace)
            page = wiki_service._require_readable(request.user, wiki_service._require_page(workspace, page_id))
            wiki_service.remember_visit(request.user, page)
            return Response(wiki_service.page_payload(page, request.user), status=status.HTTP_200_OK)

        return _call(run)

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def patch(self, request, slug, page_id):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            wiki_service.require_enabled(workspace)
            return Response(
                wiki_service.update_page(request.user, workspace, page_id, request.data),
                status=status.HTTP_200_OK,
            )

        return _call(run)

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def delete(self, request, slug, page_id):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            wiki_service.require_enabled(workspace)
            wiki_service.delete_page(request.user, workspace, page_id)
            return Response(status=status.HTTP_204_NO_CONTENT)

        return _call(run)


class WikiPageArchiveEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def post(self, request, slug, page_id):
        return self._set(request, slug, page_id, True)

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def delete(self, request, slug, page_id):
        return self._set(request, slug, page_id, False)

    def _set(self, request, slug, page_id, archived):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            wiki_service.require_enabled(workspace)
            wiki_service.archive_page(request.user, workspace, page_id, archived)
            return Response(status=status.HTTP_204_NO_CONTENT)

        return _call(run)


class WikiPageLockEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def post(self, request, slug, page_id):
        return self._set(request, slug, page_id, True)

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def delete(self, request, slug, page_id):
        return self._set(request, slug, page_id, False)

    def _set(self, request, slug, page_id, locked):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            wiki_service.require_enabled(workspace)
            page = wiki_service._require_readable(request.user, wiki_service._require_page(workspace, page_id))
            wiki_service.set_locked(request.user, page, locked)
            return Response(status=status.HTTP_204_NO_CONTENT)

        return _call(run)


class WikiPageFavoriteEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def post(self, request, slug, page_id):
        return self._set(request, slug, page_id, True)

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def delete(self, request, slug, page_id):
        return self._set(request, slug, page_id, False)

    def _set(self, request, slug, page_id, on):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            wiki_service.require_enabled(workspace)
            page = wiki_service._require_page(workspace, page_id)
            wiki_service.toggle_favorite(request.user, page, on)
            return Response(status=status.HTTP_204_NO_CONTENT)

        return _call(run)


class WikiPageMoveEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def post(self, request, slug, page_id):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            wiki_service.require_enabled(workspace)
            return Response(
                wiki_service.move_page(
                    request.user,
                    workspace,
                    page_id,
                    request.data.get("collection_id"),
                    bool(request.data.get("confirm")),
                ),
                status=status.HTTP_200_OK,
            )

        return _call(run)


class WikiPageShareEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def get(self, request, slug, page_id):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            page = wiki_service._require_page(workspace, page_id)
            return Response(wiki_service.list_shares(request.user, page), status=status.HTTP_200_OK)

        return _call(run)

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def post(self, request, slug, page_id):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            wiki_service.require_enabled(workspace)
            return Response(
                wiki_service.share_page(
                    request.user, workspace, page_id, request.data.get("member_id"), request.data.get("role")
                ),
                status=status.HTTP_200_OK,
            )

        return _call(run)


class WikiPageShareDetailEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def delete(self, request, slug, page_id, member_id):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            wiki_service.unshare_page(request.user, workspace, page_id, member_id)
            return Response(status=status.HTTP_204_NO_CONTENT)

        return _call(run)


class WikiPageCommentEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def get(self, request, slug, page_id):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            page = wiki_service._require_readable(request.user, wiki_service._require_page(workspace, page_id))
            return Response(wiki_service.list_comments(request.user, page), status=status.HTTP_200_OK)

        return _call(run)

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def post(self, request, slug, page_id):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            wiki_service.require_enabled(workspace)
            return Response(
                wiki_service.add_comment(request.user, workspace, page_id, request.data),
                status=status.HTTP_201_CREATED,
            )

        return _call(run)


class WikiCollectionListCreateEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def get(self, request, slug):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            wiki_service.require_member(request.user, workspace)
            wiki_service.require_enabled(workspace)
            wiki_service.ensure_general(workspace, request.user)
            rows = [
                wiki_service.collection_payload(collection, request.user)
                for collection in wiki_service.visible_collections(request.user, workspace)
            ]
            return Response(rows, status=status.HTTP_200_OK)

        return _call(run)

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def post(self, request, slug):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            return Response(
                wiki_service.create_collection(request.user, workspace, request.data),
                status=status.HTTP_201_CREATED,
            )

        return _call(run)


class WikiCollectionDetailEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def get(self, request, slug, collection_id):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            wiki_service.require_enabled(workspace)
            collection = next(
                (
                    row
                    for row in wiki_service.visible_collections(request.user, workspace)
                    if str(row.id) == str(collection_id)
                ),
                None,
            )
            if collection is None:
                raise WikiError("Collection not found.", 404)
            return Response(wiki_service.collection_payload(collection, request.user), status=status.HTTP_200_OK)

        return _call(run)

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def patch(self, request, slug, collection_id):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            wiki_service.require_enabled(workspace)
            return Response(
                wiki_service.update_collection(request.user, workspace, collection_id, request.data),
                status=status.HTTP_200_OK,
            )

        return _call(run)

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def delete(self, request, slug, collection_id):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            wiki_service.require_enabled(workspace)
            wiki_service.delete_collection(request.user, workspace, collection_id, request.data.get("mode") or "keep")
            return Response(status=status.HTTP_204_NO_CONTENT)

        return _call(run)


class WikiCollectionMemberEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def post(self, request, slug, collection_id):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            return Response(
                wiki_service.set_collection_member(
                    request.user,
                    workspace,
                    collection_id,
                    request.data.get("member_id"),
                    request.data.get("role"),
                ),
                status=status.HTTP_200_OK,
            )

        return _call(run)


class WikiCollectionMemberDetailEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def delete(self, request, slug, collection_id, member_id):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            wiki_service.remove_collection_member(request.user, workspace, collection_id, member_id)
            return Response(status=status.HTTP_204_NO_CONTENT)

        return _call(run)


class WikiCollectionPagesEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def post(self, request, slug, collection_id):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            wiki_service.require_enabled(workspace)
            return Response(
                wiki_service.change_collection_pages(
                    request.user,
                    workspace,
                    collection_id,
                    request.data.get("add") or [],
                    request.data.get("remove") or [],
                    bool(request.data.get("confirm")),
                ),
                status=status.HTTP_200_OK,
            )

        return _call(run)


class WikiLabelEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def get(self, request, slug):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            wiki_service.require_member(request.user, workspace)
            return Response(wiki_service.list_labels(workspace), status=status.HTTP_200_OK)

        return _call(run)

    @allow_permission([ROLE.ADMIN], level="WORKSPACE")
    def post(self, request, slug):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            return Response(
                wiki_service.upsert_label(request.user, workspace, request.data),
                status=status.HTTP_201_CREATED,
            )

        return _call(run)


class WikiLabelDetailEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN], level="WORKSPACE")
    def patch(self, request, slug, label_id):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            return Response(
                wiki_service.upsert_label(request.user, workspace, request.data, label_id),
                status=status.HTTP_200_OK,
            )

        return _call(run)

    @allow_permission([ROLE.ADMIN], level="WORKSPACE")
    def delete(self, request, slug, label_id):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            wiki_service.delete_label(request.user, workspace, label_id)
            return Response(status=status.HTTP_204_NO_CONTENT)

        return _call(run)


class WikiTemplateEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def get(self, request, slug):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            wiki_service.require_member(request.user, workspace)
            return Response(wiki_service.list_templates(workspace), status=status.HTTP_200_OK)

        return _call(run)

    @allow_permission([ROLE.ADMIN], level="WORKSPACE")
    def post(self, request, slug):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            return Response(
                wiki_service.create_template(request.user, workspace, request.data),
                status=status.HTTP_201_CREATED,
            )

        return _call(run)


class WikiPublishEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def post(self, request, slug, page_id):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            wiki_service.require_enabled(workspace)
            return Response(wiki_service.publish_page(request.user, workspace, page_id), status=status.HTTP_200_OK)

        return _call(run)

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def delete(self, request, slug, page_id):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            wiki_service.unpublish_page(request.user, workspace, page_id)
            return Response(status=status.HTTP_204_NO_CONTENT)

        return _call(run)


class WikiPublishedPageEndpoint(BaseAPIView):
    permission_classes = [AllowAny]

    def get(self, request, slug, anchor):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            return Response(wiki_service.published_page(workspace, anchor), status=status.HTTP_200_OK)

        return _call(run)


class WikiAnalyticsEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def get(self, request, slug, page_id):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            page = wiki_service._require_page(workspace, page_id)
            return Response(wiki_service.analytics(request.user, page), status=status.HTTP_200_OK)

        return _call(run)


class WikiLinkBlockEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def get(self, request, slug, page_id):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            page = wiki_service._require_readable(request.user, wiki_service._require_page(workspace, page_id))
            return Response(wiki_service.list_link_blocks(request.user, page), status=status.HTTP_200_OK)

        return _call(run)

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def post(self, request, slug, page_id):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            return Response(
                wiki_service.create_link_block(request.user, workspace, page_id, request.data),
                status=status.HTTP_201_CREATED,
            )

        return _call(run)


class WikiLinkBlockDetailEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def delete(self, request, slug, page_id, block_id):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            wiki_service.delete_link_block(request.user, workspace, page_id, block_id)
            return Response(status=status.HTTP_204_NO_CONTENT)

        return _call(run)


class WikiMemberEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def get(self, request, slug):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            wiki_service.require_member(request.user, workspace)
            return Response(wiki_service.workspace_members(workspace), status=status.HTTP_200_OK)

        return _call(run)


def _v2_page(payload, fields):
    shaped = {
        "access": payload["access"],
        "archived_at": payload["archived_at"],
        "collection_id": payload["collection_id"],
        "color": "",
        "created_at": payload["created_at"],
        "updated_at": payload["updated_at"],
        "created_by_id": payload["owned_by_id"],
        "updated_by_id": None,
        "description_html": payload.get("description_html"),
        "description_stripped": payload.get("description_stripped"),
        "external_id": None,
        "external_source": None,
        "id": payload["id"],
        "is_global": True,
        "is_locked": payload["is_locked"],
        "logo_props": payload["logo_props"],
        "name": payload["name"],
        "owned_by_id": payload["owned_by_id"],
        "parent_id": payload["parent_id"],
        "project_ids": [],
        "sort_order": payload["sort_order"],
        "view_props": None,
    }
    if not fields:
        return shaped
    wanted = [item.strip() for item in fields.split(",") if item.strip()]
    unknown = [item for item in wanted if item not in shaped and item != "all"]
    if unknown:
        raise WikiError(f"Unknown fields: {', '.join(unknown)}.", 400)
    if "all" in wanted:
        return shaped
    return {key: shaped[key] for key in ["id", *wanted] if key in shaped}


class WikiV2PageListCreateEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def get(self, request, slug):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            wiki_service.require_enabled(workspace, status=402)
            rows = wiki_service.list_pages(request.user, workspace, request.query_params)
            data = [_v2_page(row, request.query_params.get("fields")) for row in rows]
            return Response(
                {
                    "data": data,
                    "total_count": len(data),
                    "next": None,
                    "previous": None,
                    "pagination": {"style": "offset"},
                },
                status=status.HTTP_200_OK,
            )

        return _call(run)

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def post(self, request, slug):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            wiki_service.require_enabled(workspace, status=402)
            payload = wiki_service.create_page(request.user, workspace, request.data)
            return Response(_v2_page(payload, None), status=status.HTTP_201_CREATED)

        return _call(run)


class WikiV2PageDetailEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def get(self, request, slug, pk):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            wiki_service.require_enabled(workspace, status=402)
            page = wiki_service._require_readable(request.user, wiki_service._require_page(workspace, pk))
            return Response(_v2_page(wiki_service.page_payload(page, request.user), request.query_params.get("fields")))

        return _call(run)

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def patch(self, request, slug, pk):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            wiki_service.require_enabled(workspace, status=402)
            return Response(_v2_page(wiki_service.update_page(request.user, workspace, pk, request.data), None))

        return _call(run)

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def delete(self, request, slug, pk):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            wiki_service.require_enabled(workspace, status=402)
            wiki_service.delete_page(request.user, workspace, pk)
            return Response(status=status.HTTP_204_NO_CONTENT)

        return _call(run)


class WikiV2ArchiveEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def post(self, request, slug, pk):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            wiki_service.require_enabled(workspace, status=402)
            wiki_service.archive_page(request.user, workspace, pk, True)
            return Response(status=status.HTTP_204_NO_CONTENT)

        return _call(run)


class WikiV2UnarchiveEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def post(self, request, slug, pk):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            wiki_service.require_enabled(workspace, status=402)
            wiki_service.archive_page(request.user, workspace, pk, False)
            return Response(status=status.HTTP_204_NO_CONTENT)

        return _call(run)


class WikiV2CollectionListCreateEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def get(self, request, slug):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            wiki_service.require_enabled(workspace, status=402)
            wiki_service.ensure_general(workspace, request.user)
            data = [
                wiki_service.collection_payload(collection, request.user)
                for collection in wiki_service.visible_collections(request.user, workspace)
            ]
            return Response({"data": data, "total_count": len(data)}, status=status.HTTP_200_OK)

        return _call(run)

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def post(self, request, slug):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            wiki_service.require_enabled(workspace, status=402)
            return Response(
                wiki_service.create_collection(request.user, workspace, request.data),
                status=status.HTTP_201_CREATED,
            )

        return _call(run)


class WikiV2CollectionPagesEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def post(self, request, slug, pk):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            wiki_service.require_enabled(workspace, status=402)
            return Response(
                wiki_service.change_collection_pages(
                    request.user,
                    workspace,
                    pk,
                    request.data.get("add") or [],
                    request.data.get("remove") or [],
                    bool(request.data.get("confirm", True)),
                )
            )

        return _call(run)


class WikiV2StickyEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER, ROLE.GUEST], level="WORKSPACE")
    def get(self, request, slug):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            rows = wiki_service.list_stickies(request.user, workspace)
            return Response({"data": rows, "total_count": len(rows)}, status=status.HTTP_200_OK)

        return _call(run)

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER, ROLE.GUEST], level="WORKSPACE")
    def post(self, request, slug):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            return Response(
                wiki_service.create_sticky(request.user, workspace, request.data), status=status.HTTP_201_CREATED
            )

        return _call(run)


class WikiV2StickyDetailEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER, ROLE.GUEST], level="WORKSPACE")
    def get(self, request, slug, pk):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            rows = [row for row in wiki_service.list_stickies(request.user, workspace) if row["id"] == str(pk)]
            if not rows:
                raise WikiError("Sticky not found.", 404)
            return Response(rows[0], status=status.HTTP_200_OK)

        return _call(run)

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER, ROLE.GUEST], level="WORKSPACE")
    def patch(self, request, slug, pk):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            return Response(wiki_service.update_sticky(request.user, workspace, pk, request.data))

        return _call(run)

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER, ROLE.GUEST], level="WORKSPACE")
    def delete(self, request, slug, pk):
        def run():
            workspace = wiki_service.workspace_or_404(slug)
            wiki_service.delete_sticky(request.user, workspace, pk)
            return Response(status=status.HTTP_204_NO_CONTENT)

        return _call(run)
