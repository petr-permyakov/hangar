/**
 * Copyright (c) 2026-present Maciej Szymczak and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { Link, useParams } from "react-router";
import useSWR from "swr";
import { Button } from "@plane/propel/button";
import { wikiService } from "@/plane-web/services/wiki.service";

export function WikiCollectionView() {
  const { workspaceSlug, collectionId } = useParams();
  const slug = workspaceSlug?.toString() ?? "";
  const { data: sidebar, mutate } = useSWR(slug ? `WIKI_SIDEBAR_${slug}` : null, () => wikiService.sidebar(slug));
  const collection = sidebar?.collections.find((item) => item.id === collectionId);

  const addPage = async () => {
    const page = await wikiService.createPage(slug, {
      name: "Untitled",
      collection_id: collectionId,
      access: collection?.access ?? 0,
    });
    window.location.assign(`/${slug}/wiki/${page.id}`);
  };

  const removeCollection = async () => {
    if (!collection || collection.is_default) return;
    const mode = collection.access === 1 ? "archive" : "keep";
    await wikiService.deleteCollection(slug, collection.id, mode);
    await mutate();
    window.location.assign(`/${slug}/wiki`);
  };

  if (!collection) {
    return <p className="px-8 py-10 text-13 text-secondary">This collection isn't available to you.</p>;
  }

  const rows = collection.pages ?? [];

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-4 px-8 py-10">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-11 text-tertiary">
            {collection.access === 1 ? "Private collection" : "Public collection"}
          </p>
          <h1 className="text-xl font-semibold text-primary">{collection.name}</h1>
        </div>
        <div className="flex gap-2">
          <Button variant="primary" onClick={addPage}>
            Add page
          </Button>
          {!collection.is_default ? (
            <Button variant="secondary" onClick={removeCollection}>
              Delete collection
            </Button>
          ) : null}
        </div>
      </div>
      <table className="w-full border-collapse text-left text-13">
        <thead className="text-11 text-tertiary">
          <tr className="border-b border-subtle">
            <th className="py-2 font-medium">Page name</th>
            <th className="py-2 font-medium">Owner</th>
            <th className="py-2 font-medium">Nested pages</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((page) => (
            <tr key={page.id} className="border-b border-subtle">
              <td className="py-2">
                <Link to={`/${slug}/wiki/${page.id}`} className="text-primary">
                  {page.name || "Untitled"}
                </Link>
              </td>
              <td className="py-2 text-secondary">{page.owned_by?.display_name}</td>
              <td className="py-2 text-secondary">{page.child_count}</td>
            </tr>
          ))}
          {rows.length === 0 ? (
            <tr>
              <td colSpan={3} className="py-6 text-tertiary">
                This collection doesn't have any pages right now.
              </td>
            </tr>
          ) : null}
        </tbody>
      </table>
    </div>
  );
}
