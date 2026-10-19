/**
 * Copyright (c) 2026-present Maciej Szymczak and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useState } from "react";
import { useParams } from "react-router";
import useSWR from "swr";
import { Button } from "@plane/propel/button";
import { PageHead } from "@/components/core/page-title";
import { SettingsContentWrapper } from "@/components/settings/content-wrapper";
import { wikiService } from "@/plane-web/services/wiki.service";

export default function WikiSettingsPage() {
  const { workspaceSlug } = useParams();
  const slug = workspaceSlug?.toString() ?? "";
  const { data, mutate } = useSWR(slug ? `WIKI_SETTINGS_${slug}` : null, () => wikiService.settings(slug));
  const { data: labels, mutate: mutateLabels } = useSWR(slug ? `WIKI_LABELS_${slug}` : null, () =>
    wikiService.labels(slug)
  );
  const [name, setName] = useState("");
  const [color, setColor] = useState("#3f76ff");

  return (
    <SettingsContentWrapper>
      <PageHead title="Wiki" />
      <div className="flex flex-col gap-8">
        <div>
          <h1 className="text-xl font-semibold text-primary">Wiki</h1>
          <p className="mt-1 text-13 text-secondary">
            The workspace knowledge base. While it's off, the wiki is hidden and its pages can't be opened.
          </p>
        </div>
        <label className="flex items-center justify-between gap-4 rounded-md border border-subtle px-4 py-3">
          <span className="text-13 text-primary">Turn on wiki for this workspace</span>
          <input
            type="checkbox"
            checked={data?.is_enabled !== false}
            onChange={(event) => wikiService.updateSettings(slug, event.target.checked).then(() => mutate())}
          />
        </label>
        {data?.forced_private ? (
          <p className="text-13 text-secondary">
            This instance forces private visibility, so public collections and published pages stay closed.
          </p>
        ) : null}
        <section className="flex flex-col gap-3">
          <h2 className="text-13 font-medium text-secondary">Page labels</h2>
          <ul className="flex flex-col gap-2">
            {(labels ?? []).map((label) => (
              <li key={label.id} className="flex items-center justify-between text-13">
                <span className="inline-flex items-center gap-2">
                  <span className="size-2 rounded-full" style={{ background: label.color || "#3f76ff" }} />
                  {label.name}
                </span>
                <button
                  type="button"
                  className="text-tertiary"
                  onClick={() => wikiService.deleteLabel(slug, label.id).then(() => mutateLabels())}
                >
                  Delete
                </button>
              </li>
            ))}
          </ul>
          <div className="flex gap-2">
            <input
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="Label name"
              className="rounded-md border border-subtle bg-surface-1 px-3 py-2 text-13 outline-none"
            />
            <input
              value={color}
              onChange={(event) => setColor(event.target.value)}
              className="w-28 rounded-md border border-subtle px-2 py-2 text-13"
            />
            <Button
              variant="secondary"
              onClick={() =>
                wikiService.createLabel(slug, name, color).then(() => {
                  setName("");
                  return mutateLabels();
                })
              }
            >
              Add label
            </Button>
          </div>
        </section>
      </div>
    </SettingsContentWrapper>
  );
}
