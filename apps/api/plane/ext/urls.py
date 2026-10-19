# Copyright (c) 2026-present Maciej Szymczak and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

# Fork API endpoints, mounted under /api/ alongside plane.app.urls.

from django.urls import include, path

from plane.ext.views.project_workshops import ProjectWorkshopsEndpoint
from plane.ext.views.epic import (
    EpicActivityEndpoint,
    EpicArchiveEndpoint,
    EpicAttachmentV2Endpoint,
    EpicCommentViewSet,
    EpicDescriptionVersionEndpoint,
    EpicDetailViewSet,
    EpicIssuesEndpoint,
    EpicListEndpoint,
    EpicLinkViewSet,
    EpicPaginatedViewSet,
    EpicSettingsEndpoint,
    EpicReactionViewSet,
    EpicSubscriberViewSet,
    EpicUserPropertyEndpoint,
    EpicViewSet,
)
from plane.ext.views.issue_type import (
    EnableIssueTypesEndpoint,
    IssuePropertiesEndpoint,
    IssuePropertyDetailEndpoint,
    IssuePropertyOptionDetailEndpoint,
    IssuePropertyOptionsEndpoint,
    IssuePropertyValuesEndpoint,
    IssueTypeDetailEndpoint,
    IssueTypesEndpoint,
)
from plane.ext.views.import_job import (
    ImportJobCancelEndpoint,
    ImportJobDetailEndpoint,
    ImportJobListEndpoint,
    ImportJobReportEndpoint,
    TodoistImportEndpoint,
    TodoistImportPreviewEndpoint,
)
from plane.ext.views.instance_maintenance import InstanceMaintenanceNoticeEndpoint
from plane.ext.views.project_copy import (
    ProjectCopyRetryEndpoint,
    ProjectCopyStatusEndpoint,
    ProjectDuplicateEndpoint,
)
from plane.ext.views.workspace_defaults import (
    WorkspaceHomeDefaultsEndpoint,
    WorkspaceSharedLinkDetailEndpoint,
    WorkspaceSharedLinkHideEndpoint,
    WorkspaceSharedLinksEndpoint,
)
from plane.ext.views.worklog import (
    IssueWorkLogDetailEndpoint,
    IssueWorkLogsEndpoint,
)
from plane.ext.views.capacity import (
    GoogleCalendarStartEndpoint,
    GoogleCalendarsEndpoint,
    TrainerListEndpoint,
    TrainerScheduleEndpoint,
    TrainerSelfEndpoint,
    WorkspaceCapacityEndpoint,
    WorkshopCalendarResyncEndpoint,
    WorkshopScheduleEndpoint,
    WorkshopPlanDraftDetailEndpoint,
    WorkshopPlanDraftListEndpoint,
    WorkshopPlanHoldEndpoint,
    WorkshopPlanScheduleEndpoint,
    WorkshopSearchEndpoint,
)

from plane.ext.views.capacity_import import TrainingImportEndpoint
from plane.ext.views.capacity_report import TrainingReportEndpoint
from plane.ext.views.capacity_training import GoogleTrainingRulesEndpoint, GoogleTrainingLinkEndpoint
from plane.ext.views.wiki import (
    WikiAnalyticsEndpoint,
    WikiCollectionDetailEndpoint,
    WikiCollectionListCreateEndpoint,
    WikiCollectionMemberDetailEndpoint,
    WikiCollectionMemberEndpoint,
    WikiCollectionPagesEndpoint,
    WikiLabelDetailEndpoint,
    WikiLabelEndpoint,
    WikiLinkBlockDetailEndpoint,
    WikiLinkBlockEndpoint,
    WikiMemberEndpoint,
    WikiPageArchiveEndpoint,
    WikiPageCommentEndpoint,
    WikiPageDetailEndpoint,
    WikiPageFavoriteEndpoint,
    WikiPageListCreateEndpoint,
    WikiPageLockEndpoint,
    WikiPageMoveEndpoint,
    WikiPageShareDetailEndpoint,
    WikiPageShareEndpoint,
    WikiPublishEndpoint,
    WikiPublishedPageEndpoint,
    WikiSettingsEndpoint,
    WikiSidebarEndpoint,
    WikiTemplateEndpoint,
    WikiV2ArchiveEndpoint,
    WikiV2CollectionListCreateEndpoint,
    WikiV2CollectionPagesEndpoint,
    WikiV2PageDetailEndpoint,
    WikiV2PageListCreateEndpoint,
    WikiV2StickyDetailEndpoint,
    WikiV2StickyEndpoint,
    WikiV2UnarchiveEndpoint,
)
from plane.ext.views.workshop_template import (
    WorkshopApplyChecklistEndpoint,
    WorkshopChecklistTemplateDetailEndpoint,
    WorkshopChecklistTemplateListEndpoint,
    WorkshopRoleDetailEndpoint,
    WorkshopRoleListEndpoint,
)

PROJECT_BASE = "workspaces/<str:slug>/projects/<uuid:project_id>"

EPIC_BASE = "workspaces/<str:slug>/projects/<uuid:project_id>/epics"

urlpatterns = [
    path(
        "workspaces/<str:slug>/capacity/training-imports/",
        TrainingImportEndpoint.as_view(),
        name="capacity-training-imports",
    ),
    path(
        "workspaces/<str:slug>/capacity/training-report/",
        TrainingReportEndpoint.as_view(),
        name="capacity-training-report",
    ),
    path("workspaces/<str:slug>/capacity/google/training-rules/", GoogleTrainingRulesEndpoint.as_view()),
    path("workspaces/<str:slug>/capacity/google/training-rules/<uuid:rule_id>/", GoogleTrainingRulesEndpoint.as_view()),
    path("workspaces/<str:slug>/capacity/google/training-links/", GoogleTrainingLinkEndpoint.as_view()),
    path("workspaces/<str:slug>/capacity/google/training-links/<str:event_key>/", GoogleTrainingLinkEndpoint.as_view()),
    path("workspaces/<str:slug>/capacity/trainers/me/", TrainerSelfEndpoint.as_view(), name="capacity-trainer-self"),
    path("workspaces/<str:slug>/capacity/trainers/", TrainerListEndpoint.as_view(), name="capacity-trainers"),
    path(
        "workspaces/<str:slug>/capacity/trainers/<uuid:user_id>/schedule/",
        TrainerScheduleEndpoint.as_view(),
        name="capacity-trainer-schedule",
    ),
    path(
        "workspaces/<str:slug>/capacity/google/start/",
        GoogleCalendarStartEndpoint.as_view(),
        name="capacity-google-start",
    ),
    path(
        "workspaces/<str:slug>/capacity/google/calendars/",
        GoogleCalendarsEndpoint.as_view(),
        name="capacity-google-calendars",
    ),
    path("workspaces/<str:slug>/capacity/", WorkspaceCapacityEndpoint.as_view(), name="workspace-capacity"),
    path(
        "workspaces/<str:slug>/capacity/workshops/",
        WorkshopSearchEndpoint.as_view(),
        name="capacity-workshop-search",
    ),
    path(
        "workspaces/<str:slug>/capacity/plans/",
        WorkshopPlanDraftListEndpoint.as_view(),
        name="workshop-plan-drafts",
    ),
    path(
        "workspaces/<str:slug>/capacity/plans/<uuid:draft_id>/",
        WorkshopPlanDraftDetailEndpoint.as_view(),
        name="workshop-plan-draft",
    ),
    path(
        "workspaces/<str:slug>/capacity/plans/<uuid:draft_id>/hold/",
        WorkshopPlanHoldEndpoint.as_view(),
        name="workshop-plan-hold",
    ),
    path(
        "workspaces/<str:slug>/capacity/plans/<uuid:draft_id>/schedule/",
        WorkshopPlanScheduleEndpoint.as_view(),
        name="workshop-plan-schedule",
    ),
    path(
        f"{PROJECT_BASE}/work-items/<uuid:issue_id>/workshop-schedule/",
        WorkshopScheduleEndpoint.as_view(),
        name="workshop-schedule",
    ),
    path(
        f"{PROJECT_BASE}/capacity/workshops/",
        ProjectWorkshopsEndpoint.as_view(),
        name="project-workshops",
    ),
    path(
        f"{PROJECT_BASE}/work-items/<uuid:issue_id>/workshop-schedule/resync/",
        WorkshopCalendarResyncEndpoint.as_view(),
        name="workshop-schedule-resync",
    ),
    path(
        "workspaces/<str:slug>/capacity/workshop-roles/",
        WorkshopRoleListEndpoint.as_view(),
        name="workshop-roles",
    ),
    path(
        "workspaces/<str:slug>/capacity/workshop-roles/<uuid:role_id>/",
        WorkshopRoleDetailEndpoint.as_view(),
        name="workshop-role",
    ),
    path(
        "workspaces/<str:slug>/capacity/checklist-templates/",
        WorkshopChecklistTemplateListEndpoint.as_view(),
        name="workshop-checklist-templates",
    ),
    path(
        "workspaces/<str:slug>/capacity/checklist-templates/<uuid:template_id>/",
        WorkshopChecklistTemplateDetailEndpoint.as_view(),
        name="workshop-checklist-template",
    ),
    path(
        f"{PROJECT_BASE}/work-items/<uuid:issue_id>/apply-checklist/",
        WorkshopApplyChecklistEndpoint.as_view(),
        name="workshop-apply-checklist",
    ),
    # Read-only, anonymous, and deliberately NOT under /api/instances/: the
    # session middleware switches to the admin cookie on any path containing
    # "instances", which would leave every signed-in reader looking anonymous.
    path(
        "maintenance/",
        InstanceMaintenanceNoticeEndpoint.as_view(),
        name="instance-maintenance-notice",
    ),
    path(
        "workspaces/<str:slug>/runner/",
        include("plane.ext.runner.urls"),
    ),
    path(
        "workspaces/<str:slug>/home-defaults/",
        WorkspaceHomeDefaultsEndpoint.as_view(),
        name="workspace-home-defaults",
    ),
    path(
        "workspaces/<str:slug>/shared-links/",
        WorkspaceSharedLinksEndpoint.as_view(),
        name="workspace-shared-links",
    ),
    path(
        "workspaces/<str:slug>/shared-links/<uuid:link_id>/",
        WorkspaceSharedLinkDetailEndpoint.as_view(),
        name="workspace-shared-link",
    ),
    path(
        "workspaces/<str:slug>/shared-links/<uuid:link_id>/hide/",
        WorkspaceSharedLinkHideEndpoint.as_view(),
        name="workspace-shared-link-hide",
    ),
    path(
        "workspaces/<str:slug>/imports/todoist/preview/",
        TodoistImportPreviewEndpoint.as_view(),
        name="todoist-import-preview",
    ),
    path(
        "workspaces/<str:slug>/imports/todoist/",
        TodoistImportEndpoint.as_view(),
        name="todoist-import",
    ),
    path(
        "workspaces/<str:slug>/imports/",
        ImportJobListEndpoint.as_view(),
        name="import-jobs",
    ),
    path(
        "workspaces/<str:slug>/imports/<uuid:job_id>/",
        ImportJobDetailEndpoint.as_view(),
        name="import-job-detail",
    ),
    path(
        "workspaces/<str:slug>/imports/<uuid:job_id>/report/",
        ImportJobReportEndpoint.as_view(),
        name="import-job-report",
    ),
    path(
        "workspaces/<str:slug>/imports/<uuid:job_id>/cancel/",
        ImportJobCancelEndpoint.as_view(),
        name="import-job-cancel",
    ),
    path(
        "workspaces/<str:slug>/projects/<uuid:project_id>/epic-settings/",
        EpicSettingsEndpoint.as_view(),
        name="epic-settings",
    ),
    path(
        f"{PROJECT_BASE}/duplicate/",
        ProjectDuplicateEndpoint.as_view(),
        # A distinct name on purpose: `name="project"` is declared three times in
        # plane.app.urls.project, which is why its tests build URLs by hand.
        name="project-duplicate",
    ),
    path(
        f"{PROJECT_BASE}/copy-status/",
        ProjectCopyStatusEndpoint.as_view(),
        name="project-copy-status",
    ),
    path(
        f"{PROJECT_BASE}/copy-status/retry/",
        ProjectCopyRetryEndpoint.as_view(),
        name="project-copy-retry",
    ),
    path(
        f"{PROJECT_BASE}/issue-types/",
        IssueTypesEndpoint.as_view(),
        name="issue-types",
    ),
    path(
        f"{PROJECT_BASE}/issue-types/enable/",
        EnableIssueTypesEndpoint.as_view(),
        name="enable-issue-types",
    ),
    path(
        f"{PROJECT_BASE}/issue-types/<uuid:type_id>/",
        IssueTypeDetailEndpoint.as_view(),
        name="issue-type-detail",
    ),
    path(
        f"{PROJECT_BASE}/issue-types/<uuid:type_id>/properties/",
        IssuePropertiesEndpoint.as_view(),
        name="issue-type-properties",
    ),
    path(
        f"{PROJECT_BASE}/properties/<uuid:property_id>/",
        IssuePropertyDetailEndpoint.as_view(),
        name="issue-property-detail",
    ),
    path(
        f"{PROJECT_BASE}/properties/<uuid:property_id>/options/",
        IssuePropertyOptionsEndpoint.as_view(),
        name="issue-property-options",
    ),
    path(
        f"{PROJECT_BASE}/properties/<uuid:property_id>/options/<uuid:option_id>/",
        IssuePropertyOptionDetailEndpoint.as_view(),
        name="issue-property-option-detail",
    ),
    path(
        f"{PROJECT_BASE}/issues/<uuid:issue_id>/property-values/",
        IssuePropertyValuesEndpoint.as_view(),
        name="issue-property-values",
    ),
    path(
        f"{PROJECT_BASE}/issues/<uuid:issue_id>/worklogs/",
        IssueWorkLogsEndpoint.as_view(),
        name="issue-worklogs",
    ),
    path(
        f"{PROJECT_BASE}/issues/<uuid:issue_id>/worklogs/<uuid:pk>/",
        IssueWorkLogDetailEndpoint.as_view(),
        name="issue-worklog-detail",
    ),
    path(
        "workspaces/<str:slug>/projects/<uuid:project_id>/epics-user-properties/",
        EpicUserPropertyEndpoint.as_view(),
        name="epic-user-properties",
    ),
    path(
        "workspaces/<str:slug>/projects/<uuid:project_id>/epics/",
        EpicViewSet.as_view({"get": "list", "post": "create"}),
        name="epics",
    ),
    path(f"{EPIC_BASE}/list/", EpicListEndpoint.as_view(), name="epics-list"),
    path(f"{EPIC_BASE}/<uuid:pk>/archive/", EpicArchiveEndpoint.as_view(), name="epic-archive"),
    path(
        "workspaces/<str:slug>/projects/<uuid:project_id>/epics/<uuid:pk>/",
        EpicDetailViewSet.as_view(),
        name="epic-detail",
    ),
    path(
        "workspaces/<str:slug>/projects/<uuid:project_id>/epics/<uuid:pk>/issues/",
        EpicIssuesEndpoint.as_view(),
        name="epic-issues",
    ),
    path(
        "workspaces/<str:slug>/projects/<uuid:project_id>/v2/epics/",
        EpicPaginatedViewSet.as_view({"get": "list"}),
        name="epics-paginated",
    ),
    # Epic sub-resources — the web issue services parameterize their URLs by
    # service type ("epics"), so these alias the existing work-item views,
    # none of which resolve the parent through the epic-excluding
    # issue_objects manager.
    path(f"{EPIC_BASE}/<uuid:issue_id>/history/", EpicActivityEndpoint.as_view(), name="epic-history"),
    path(
        f"{EPIC_BASE}/<uuid:issue_id>/comments/",
        EpicCommentViewSet.as_view({"get": "list", "post": "create"}),
        name="epic-comments",
    ),
    path(
        f"{EPIC_BASE}/<uuid:issue_id>/comments/<uuid:pk>/",
        EpicCommentViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"}),
        name="epic-comments",
    ),
    path(
        f"{EPIC_BASE}/<uuid:issue_id>/reactions/",
        EpicReactionViewSet.as_view({"get": "list", "post": "create"}),
        name="epic-reactions",
    ),
    path(
        f"{EPIC_BASE}/<uuid:issue_id>/reactions/<str:reaction_code>/",
        EpicReactionViewSet.as_view({"delete": "destroy"}),
        name="epic-reactions",
    ),
    path(
        f"{EPIC_BASE}/<uuid:issue_id>/subscribe/",
        EpicSubscriberViewSet.as_view({"get": "subscription_status", "post": "subscribe", "delete": "unsubscribe"}),
        name="epic-subscribe",
    ),
    path(
        f"{EPIC_BASE}/<uuid:issue_id>/links/",
        EpicLinkViewSet.as_view({"get": "list", "post": "create"}),
        name="epic-links",
    ),
    path(
        f"{EPIC_BASE}/<uuid:issue_id>/links/<uuid:pk>/",
        EpicLinkViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"}),
        name="epic-links",
    ),
    path(
        f"{EPIC_BASE}/<uuid:work_item_id>/description-versions/",
        EpicDescriptionVersionEndpoint.as_view(),
        name="epic-description-versions",
    ),
    path(
        f"{EPIC_BASE}/<uuid:work_item_id>/description-versions/<uuid:pk>/",
        EpicDescriptionVersionEndpoint.as_view(),
        name="epic-description-versions",
    ),
    path(
        f"assets/v2/{EPIC_BASE}/<uuid:issue_id>/attachments/",
        EpicAttachmentV2Endpoint.as_view(),
        name="epic-attachments",
    ),
    path(
        f"assets/v2/{EPIC_BASE}/<uuid:issue_id>/attachments/<uuid:pk>/",
        EpicAttachmentV2Endpoint.as_view(),
        name="epic-attachments",
    ),
    # Deferred epic routes (upstream views inline the epic-excluding
    # issue_objects manager and need dedicated ext variants):
    # epics-detail/, epics/list/, issue-relation/, archive/.
    path("workspaces/<str:slug>/wiki/settings/", WikiSettingsEndpoint.as_view(), name="wiki-settings"),
    path("workspaces/<str:slug>/wiki/sidebar/", WikiSidebarEndpoint.as_view(), name="wiki-sidebar"),
    path("workspaces/<str:slug>/wiki/members/", WikiMemberEndpoint.as_view(), name="wiki-members"),
    path("workspaces/<str:slug>/wiki/pages/", WikiPageListCreateEndpoint.as_view(), name="wiki-pages"),
    path("workspaces/<str:slug>/wiki/pages/<uuid:page_id>/", WikiPageDetailEndpoint.as_view(), name="wiki-page"),
    path(
        "workspaces/<str:slug>/wiki/pages/<uuid:page_id>/archive/",
        WikiPageArchiveEndpoint.as_view(),
        name="wiki-page-archive",
    ),
    path(
        "workspaces/<str:slug>/wiki/pages/<uuid:page_id>/lock/", WikiPageLockEndpoint.as_view(), name="wiki-page-lock"
    ),
    path(
        "workspaces/<str:slug>/wiki/pages/<uuid:page_id>/favorite/",
        WikiPageFavoriteEndpoint.as_view(),
        name="wiki-page-favorite",
    ),
    path(
        "workspaces/<str:slug>/wiki/pages/<uuid:page_id>/move/", WikiPageMoveEndpoint.as_view(), name="wiki-page-move"
    ),
    path(
        "workspaces/<str:slug>/wiki/pages/<uuid:page_id>/shares/",
        WikiPageShareEndpoint.as_view(),
        name="wiki-page-shares",
    ),
    path(
        "workspaces/<str:slug>/wiki/pages/<uuid:page_id>/shares/<uuid:member_id>/",
        WikiPageShareDetailEndpoint.as_view(),
        name="wiki-page-share",
    ),
    path(
        "workspaces/<str:slug>/wiki/pages/<uuid:page_id>/comments/",
        WikiPageCommentEndpoint.as_view(),
        name="wiki-page-comments",
    ),
    path(
        "workspaces/<str:slug>/wiki/pages/<uuid:page_id>/analytics/",
        WikiAnalyticsEndpoint.as_view(),
        name="wiki-page-analytics",
    ),
    path(
        "workspaces/<str:slug>/wiki/pages/<uuid:page_id>/publish/",
        WikiPublishEndpoint.as_view(),
        name="wiki-page-publish",
    ),
    path(
        "workspaces/<str:slug>/wiki/pages/<uuid:page_id>/link-blocks/",
        WikiLinkBlockEndpoint.as_view(),
        name="wiki-link-blocks",
    ),
    path(
        "workspaces/<str:slug>/wiki/pages/<uuid:page_id>/link-blocks/<uuid:block_id>/",
        WikiLinkBlockDetailEndpoint.as_view(),
        name="wiki-link-block",
    ),
    path(
        "workspaces/<str:slug>/wiki/collections/", WikiCollectionListCreateEndpoint.as_view(), name="wiki-collections"
    ),
    path(
        "workspaces/<str:slug>/wiki/collections/<uuid:collection_id>/",
        WikiCollectionDetailEndpoint.as_view(),
        name="wiki-collection",
    ),
    path(
        "workspaces/<str:slug>/wiki/collections/<uuid:collection_id>/members/",
        WikiCollectionMemberEndpoint.as_view(),
        name="wiki-collection-members",
    ),
    path(
        "workspaces/<str:slug>/wiki/collections/<uuid:collection_id>/members/<uuid:member_id>/",
        WikiCollectionMemberDetailEndpoint.as_view(),
        name="wiki-collection-member",
    ),
    path(
        "workspaces/<str:slug>/wiki/collections/<uuid:collection_id>/pages/",
        WikiCollectionPagesEndpoint.as_view(),
        name="wiki-collection-pages",
    ),
    path("workspaces/<str:slug>/wiki/labels/", WikiLabelEndpoint.as_view(), name="wiki-labels"),
    path("workspaces/<str:slug>/wiki/labels/<uuid:label_id>/", WikiLabelDetailEndpoint.as_view(), name="wiki-label"),
    path("workspaces/<str:slug>/wiki/templates/", WikiTemplateEndpoint.as_view(), name="wiki-templates"),
    path(
        "workspaces/<str:slug>/wiki/published/<str:anchor>/",
        WikiPublishedPageEndpoint.as_view(),
        name="wiki-published",
    ),
    path("v2/workspaces/<str:slug>/pages/", WikiV2PageListCreateEndpoint.as_view(), name="v2-wiki-pages"),
    path("v2/workspaces/<str:slug>/pages/<uuid:pk>/", WikiV2PageDetailEndpoint.as_view(), name="v2-wiki-page"),
    path("v2/workspaces/<str:slug>/pages/<uuid:pk>/archive/", WikiV2ArchiveEndpoint.as_view(), name="v2-wiki-archive"),
    path(
        "v2/workspaces/<str:slug>/pages/<uuid:pk>/unarchive/",
        WikiV2UnarchiveEndpoint.as_view(),
        name="v2-wiki-unarchive",
    ),
    path(
        "v2/workspaces/<str:slug>/collections/",
        WikiV2CollectionListCreateEndpoint.as_view(),
        name="v2-wiki-collections",
    ),
    path(
        "v2/workspaces/<str:slug>/collections/<uuid:pk>/pages/",
        WikiV2CollectionPagesEndpoint.as_view(),
        name="v2-wiki-collection-pages",
    ),
    path("v2/workspaces/<str:slug>/stickies/", WikiV2StickyEndpoint.as_view(), name="v2-stickies"),
    path("v2/workspaces/<str:slug>/stickies/<uuid:pk>/", WikiV2StickyDetailEndpoint.as_view(), name="v2-sticky"),
]
