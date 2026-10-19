/**
 * Copyright (c) 2026-present Maciej Szymczak and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { API_BASE_URL } from "@plane/constants";
import { APIService } from "@/services/api.service";

export type TWikiPage = {
  id: string;
  name: string;
  access: number;
  is_locked: boolean;
  archived_at: string | null;
  parent_id: string | null;
  owned_by_id: string;
  owned_by: { id: string; display_name: string; email: string } | null;
  collection_id: string | null;
  description_html?: string;
  description_stripped?: string;
  label_ids: string[];
  can_edit: boolean;
  can_comment: boolean;
  can_manage: boolean;
  can_share: boolean;
  is_favorite: boolean;
  child_count: number;
  children?: TWikiPage[];
  visited_at?: string;
};

export type TWikiCollection = {
  id: string;
  name: string;
  access: number;
  is_default: boolean;
  sort_order: number;
  owned_by: { id: string; display_name: string; email: string } | null;
  my_role: string | null;
  pages?: TWikiPage[];
};

export type TWikiSidebar = {
  enabled: boolean;
  forced_private: boolean;
  collections: TWikiCollection[];
  private: TWikiPage[];
  shared: TWikiPage[];
  favorites: TWikiPage[];
  recents: TWikiPage[];
  archived: TWikiPage[];
};

export class WikiService extends APIService {
  constructor() {
    super(API_BASE_URL);
  }

  private async send<T>(request: Promise<{ data: T }>): Promise<T> {
    return request
      .then((response) => response.data)
      .catch((error) => {
        throw error?.response?.data ?? error;
      });
  }

  settings(slug: string) {
    return this.send<{ is_enabled: boolean; forced_private: boolean }>(
      this.get(`/api/workspaces/${slug}/wiki/settings/`)
    );
  }

  updateSettings(slug: string, isEnabled: boolean) {
    return this.send<{ is_enabled: boolean }>(
      this.patch(`/api/workspaces/${slug}/wiki/settings/`, { is_enabled: isEnabled })
    );
  }

  sidebar(slug: string) {
    return this.send<TWikiSidebar>(this.get(`/api/workspaces/${slug}/wiki/sidebar/`));
  }

  listPages(slug: string, params?: Record<string, string>) {
    return this.send<TWikiPage[]>(this.get(`/api/workspaces/${slug}/wiki/pages/`, { params }));
  }

  getPage(slug: string, pageId: string) {
    return this.send<TWikiPage>(this.get(`/api/workspaces/${slug}/wiki/pages/${pageId}/`));
  }

  createPage(slug: string, payload: Record<string, unknown>) {
    return this.send<TWikiPage>(this.post(`/api/workspaces/${slug}/wiki/pages/`, payload));
  }

  updatePage(slug: string, pageId: string, payload: Record<string, unknown>) {
    return this.send<TWikiPage>(this.patch(`/api/workspaces/${slug}/wiki/pages/${pageId}/`, payload));
  }

  archivePage(slug: string, pageId: string) {
    return this.send<void>(this.post(`/api/workspaces/${slug}/wiki/pages/${pageId}/archive/`, {}));
  }

  restorePage(slug: string, pageId: string) {
    return this.send<void>(this.delete(`/api/workspaces/${slug}/wiki/pages/${pageId}/archive/`));
  }

  deletePage(slug: string, pageId: string) {
    return this.send<void>(this.delete(`/api/workspaces/${slug}/wiki/pages/${pageId}/`));
  }

  favorite(slug: string, pageId: string, on: boolean) {
    const url = `/api/workspaces/${slug}/wiki/pages/${pageId}/favorite/`;
    return this.send<void>(on ? this.post(url, {}) : this.delete(url));
  }

  movePage(slug: string, pageId: string, collectionId: string | null, confirm: boolean) {
    return this.send<TWikiPage>(
      this.post(`/api/workspaces/${slug}/wiki/pages/${pageId}/move/`, { collection_id: collectionId, confirm })
    );
  }

  shares(slug: string, pageId: string) {
    return this.send<{ id: string; role: string; member: { id: string; display_name: string } }[]>(
      this.get(`/api/workspaces/${slug}/wiki/pages/${pageId}/shares/`)
    );
  }

  share(slug: string, pageId: string, memberId: string, role: string) {
    return this.send(this.post(`/api/workspaces/${slug}/wiki/pages/${pageId}/shares/`, { member_id: memberId, role }));
  }

  comments(slug: string, pageId: string) {
    return this.send<{ id: string; comment_stripped: string; actor: { display_name: string } | null }[]>(
      this.get(`/api/workspaces/${slug}/wiki/pages/${pageId}/comments/`)
    );
  }

  addComment(slug: string, pageId: string, comment: string) {
    return this.send(this.post(`/api/workspaces/${slug}/wiki/pages/${pageId}/comments/`, { comment }));
  }

  createCollection(slug: string, name: string, access: number) {
    return this.send<TWikiCollection>(this.post(`/api/workspaces/${slug}/wiki/collections/`, { name, access }));
  }

  deleteCollection(slug: string, collectionId: string, mode: "keep" | "archive") {
    return this.send<void>(this.delete(`/api/workspaces/${slug}/wiki/collections/${collectionId}/`, { mode }));
  }

  labels(slug: string) {
    return this.send<{ id: string; name: string; color: string }[]>(this.get(`/api/workspaces/${slug}/wiki/labels/`));
  }

  createLabel(slug: string, name: string, color: string) {
    return this.send(this.post(`/api/workspaces/${slug}/wiki/labels/`, { name, color }));
  }

  deleteLabel(slug: string, labelId: string) {
    return this.send<void>(this.delete(`/api/workspaces/${slug}/wiki/labels/${labelId}/`));
  }

  members(slug: string) {
    return this.send<{ id: string; display_name: string; email: string }[]>(
      this.get(`/api/workspaces/${slug}/wiki/members/`)
    );
  }

  linkBlocks(slug: string, pageId: string) {
    return this.send<{ id: string; source: string; pages: TWikiPage[] }[]>(
      this.get(`/api/workspaces/${slug}/wiki/pages/${pageId}/link-blocks/`)
    );
  }

  createLinkBlock(slug: string, pageId: string, sourcePageId: string) {
    return this.send(
      this.post(`/api/workspaces/${slug}/wiki/pages/${pageId}/link-blocks/`, {
        source: "parent",
        source_page_id: sourcePageId,
        nesting_level: 6,
      })
    );
  }

  analytics(slug: string, pageId: string) {
    return this.send<{ viewers: number; nested_pages: number; comments: number }>(
      this.get(`/api/workspaces/${slug}/wiki/pages/${pageId}/analytics/`)
    );
  }

  templates(slug: string) {
    return this.send<{ id: string; name: string }[]>(this.get(`/api/workspaces/${slug}/wiki/templates/`));
  }

  createTemplate(slug: string, name: string, descriptionHtml: string) {
    return this.send(this.post(`/api/workspaces/${slug}/wiki/templates/`, { name, description_html: descriptionHtml }));
  }
}

export const wikiService = new WikiService();
