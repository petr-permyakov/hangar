/**
 * Copyright (c) 2026-present Maciej Szymczak and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useState } from "react";
import { Link, useParams } from "react-router";
import useSWR from "swr";
import { ChevronRight, FileText, Home, Lock, Plus } from "lucide-react";
import { Button } from "@plane/propel/button";
import { cn } from "@plane/utils";
import type { TWikiPage } from "@/plane-web/services/wiki.service";
import { wikiService } from "@/plane-web/services/wiki.service";

function PageLinks({ slug, pages, depth = 0 }: { slug: string; pages: TWikiPage[]; depth?: number }) {
  return (
    <div className="flex flex-col">
      {pages.map((page) => (
        <div key={page.id}>
          <Link
            to={`/${slug}/wiki/${page.id}`}
            className="flex items-center gap-1.5 rounded-md px-2 py-1 text-13 text-secondary hover:bg-layer-transparent-hover hover:text-primary"
            style={{ paddingLeft: 8 + depth * 12 }}
          >
            {page.access === 1 ? <Lock className="size-3 shrink-0" /> : <FileText className="size-3 shrink-0" />}
            <span className="truncate">{page.name || "Untitled"}</span>
          </Link>
          {page.children && page.children.length > 0 && (
            <PageLinks slug={slug} pages={page.children} depth={depth + 1} />
          )}
        </div>
      ))}
    </div>
  );
}

export function WikiShell({ children }: { children: React.ReactNode }) {
  const { workspaceSlug } = useParams();
  const slug = workspaceSlug?.toString() ?? "";
  const [creating, setCreating] = useState(false);
  const [collectionName, setCollectionName] = useState("");
  const { data: settings } = useSWR(slug ? `WIKI_SETTINGS_${slug}` : null, () => wikiService.settings(slug));
  const {
    data: sidebar,
    mutate,
    error,
  } = useSWR(slug && settings?.is_enabled !== false ? `WIKI_SIDEBAR_${slug}` : null, () => wikiService.sidebar(slug));

  const createPage = async (access: number) => {
    setCreating(true);
    try {
      const page = await wikiService.createPage(slug, { name: "", access });
      window.location.assign(`/${slug}/wiki/${page.id}`);
    } finally {
      setCreating(false);
    }
  };

  const createCollection = async () => {
    if (!collectionName.trim()) return;
    await wikiService.createCollection(slug, collectionName.trim(), 0);
    setCollectionName("");
    await mutate();
  };

  return (
    <div className="flex h-full min-h-0 w-full overflow-hidden bg-surface-1">
      <aside className="flex h-full w-64 shrink-0 flex-col gap-3 overflow-y-auto border-r border-subtle px-3 py-4">
        <div className="flex flex-col gap-2">
          <Button
            variant="primary"
            onClick={() => createPage(0)}
            loading={creating}
            disabled={settings?.is_enabled === false}
          >
            New page
          </Button>
          <button
            type="button"
            className="rounded-md px-2 py-1 text-left text-13 text-secondary hover:bg-layer-transparent-hover"
            onClick={() => createPage(1)}
          >
            <span className="inline-flex items-center gap-1.5">
              <Plus className="size-3" /> Private page
            </span>
          </button>
        </div>
        <Link
          to={`/${slug}/wiki`}
          className="flex items-center gap-2 rounded-md px-2 py-1.5 text-13 font-medium text-primary hover:bg-layer-transparent-hover"
        >
          <Home className="size-4" /> Home
        </Link>
        {sidebar?.favorites?.length ? (
          <section>
            <p className="px-2 pb-1 text-11 font-medium text-tertiary">Favorites</p>
            <PageLinks slug={slug} pages={sidebar.favorites} />
          </section>
        ) : null}
        <section className="flex flex-col gap-1">
          <div className="flex items-center justify-between px-2">
            <p className="text-11 font-medium text-tertiary">Collections</p>
          </div>
          {sidebar?.collections.map((collection) => (
            <div key={collection.id}>
              <Link
                to={`/${slug}/wiki/collections/${collection.id}`}
                className="flex items-center gap-1 rounded-md px-2 py-1 text-13 font-medium text-primary hover:bg-layer-transparent-hover"
              >
                <ChevronRight className="size-3" />
                <span className="truncate">{collection.name}</span>
                {collection.access === 1 ? <Lock className="size-3 text-tertiary" /> : null}
              </Link>
              <PageLinks slug={slug} pages={collection.pages ?? []} />
            </div>
          ))}
          <div className="flex gap-1 px-2 pt-1">
            <input
              value={collectionName}
              onChange={(event) => setCollectionName(event.target.value)}
              placeholder="New collection"
              className="w-full rounded-md border border-subtle bg-surface-1 px-2 py-1 text-11 text-primary outline-none"
            />
            <button type="button" className="text-11 text-secondary" onClick={createCollection}>
              Add
            </button>
          </div>
        </section>
        <section>
          <p className="px-2 pb-1 text-11 font-medium text-tertiary">Shared</p>
          <PageLinks slug={slug} pages={sidebar?.shared ?? []} />
        </section>
        <section>
          <p className="px-2 pb-1 text-11 font-medium text-tertiary">Private</p>
          <PageLinks slug={slug} pages={sidebar?.private ?? []} />
        </section>
        <section>
          <p className="px-2 pb-1 text-11 font-medium text-tertiary">Archived</p>
          <PageLinks slug={slug} pages={sidebar?.archived ?? []} />
        </section>
      </aside>
      <main className={cn("min-w-0 flex-1 overflow-y-auto")}>
        {error ? (
          <div className="mx-auto max-w-xl px-8 py-16">
            <h1 className="text-20 font-semibold text-primary">Permission denied</h1>
            <p className="mt-2 text-13 text-secondary">Workspace guests can't open the wiki.</p>
          </div>
        ) : settings?.is_enabled === false ? (
          <div className="mx-auto max-w-xl px-8 py-16">
            <h1 className="text-20 font-semibold text-primary">Wiki is turned off</h1>
            <p className="mt-2 text-13 text-secondary">
              A workspace admin can turn it back on in Workspace settings, Wiki. Existing pages stay stored.
            </p>
            <Link to={`/${slug}/settings/wiki`} className="mt-4 inline-block text-13 text-accent-primary">
              Wiki settings
            </Link>
          </div>
        ) : (
          children
        )}
      </main>
    </div>
  );
}
