/**
 * Copyright (c) 2026-present Maciej Szymczak and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { Link, useParams } from "react-router";
import useSWR from "swr";
import { StickyService } from "@/services/sticky.service";
import { wikiService } from "@/plane-web/services/wiki.service";

function stickyText(value: string | undefined) {
  if (!value) return "";
  return value
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

const stickies = new StickyService();

export function WikiHome() {
  const { workspaceSlug } = useParams();
  const slug = workspaceSlug?.toString() ?? "";
  const { data: sidebar } = useSWR(slug ? `WIKI_SIDEBAR_${slug}` : null, () => wikiService.sidebar(slug));
  const { data: notes } = useSWR(slug ? `WIKI_STICKIES_${slug}` : null, () =>
    stickies.getStickies(slug, "1:0:0", undefined, 8)
  );

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-8 px-8 py-10">
      <header>
        <p className="text-13 text-tertiary">Workspace knowledge</p>
        <h1 className="text-xl font-semibold text-primary">Wiki</h1>
        <p className="mt-1 text-13 text-secondary">
          Policies, onboarding, and decisions that belong to the whole workspace.
        </p>
      </header>
      <section className="flex flex-col gap-2">
        <h2 className="text-13 font-medium text-secondary">Recents</h2>
        {(sidebar?.recents ?? []).length === 0 ? (
          <p className="text-13 text-tertiary">Pages you open will show up here.</p>
        ) : (
          <ul className="flex flex-col divide-y divide-subtle rounded-md border border-subtle">
            {sidebar?.recents.map((page) => (
              <li key={page.id}>
                <Link
                  to={`/${slug}/wiki/${page.id}`}
                  className="flex items-center justify-between px-3 py-2 hover:bg-layer-transparent-hover"
                >
                  <span className="text-13 text-primary">{page.name || "Untitled"}</span>
                  <span className="text-11 text-tertiary">{page.owned_by?.display_name}</span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
      <section className="flex flex-col gap-2">
        <h2 className="text-13 font-medium text-secondary">Stickies</h2>
        <div className="grid grid-cols-2 gap-3">
          {(notes?.results ?? []).map((note) => (
            <article
              key={note.id}
              className="rounded-md border border-subtle p-3 text-13 text-primary"
              style={{ background: note.background_color || "transparent" }}
            >
              <p className="font-medium">{note.name || "Note"}</p>
              <p className="mt-1 text-secondary">{stickyText(note.description_html)}</p>
            </article>
          ))}
          {(notes?.results ?? []).length === 0 ? (
            <p className="text-13 text-tertiary">Your personal notes stay on this home. Add one from the sticky pad.</p>
          ) : null}
        </div>
      </section>
    </div>
  );
}
