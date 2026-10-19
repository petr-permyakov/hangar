/**
 * Copyright (c) 2026-present Maciej Szymczak and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useEffect, useState } from "react";
import { useParams } from "react-router";
import useSWR from "swr";
import { Button } from "@plane/propel/button";
import { wikiService } from "@/plane-web/services/wiki.service";

function textFromHtml(value: string | undefined) {
  if (!value) return "";
  return value
    .replace(/<br\s*\/?>/gi, "\n")
    .replace(/<\/p>/gi, "\n")
    .replace(/<[^>]+>/g, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

export function WikiDocument() {
  const { workspaceSlug, pageId } = useParams();
  const slug = workspaceSlug?.toString() ?? "";
  const id = pageId?.toString() ?? "";
  const { data: page, mutate } = useSWR(slug && id ? `WIKI_PAGE_${slug}_${id}` : null, () =>
    wikiService.getPage(slug, id)
  );
  const { data: comments, mutate: mutateComments } = useSWR(slug && id ? `WIKI_COMMENTS_${slug}_${id}` : null, () =>
    wikiService.comments(slug, id)
  );
  const { data: blocks } = useSWR(slug && id ? `WIKI_BLOCKS_${slug}_${id}` : null, () =>
    wikiService.linkBlocks(slug, id)
  );
  const { data: stats } = useSWR(slug && id ? `WIKI_STATS_${slug}_${id}` : null, () => wikiService.analytics(slug, id));
  const { data: members } = useSWR(slug ? `WIKI_MEMBERS_${slug}` : null, () => wikiService.members(slug));
  const [title, setTitle] = useState(page?.name ?? "");
  const [body, setBody] = useState(textFromHtml(page?.description_html));
  const [comment, setComment] = useState("");
  const [shareId, setShareId] = useState("");

  useEffect(() => {
    if (!page) return;
    setTitle(page.name);
    setBody(textFromHtml(page.description_html));
  }, [page]);

  if (!page) return <p className="px-8 py-10 text-13 text-secondary">Loading page…</p>;

  const save = async () => {
    await wikiService.updatePage(slug, id, { name: title, description: body });
    await mutate();
  };

  const nest = async () => {
    const child = await wikiService.createPage(slug, { name: "Untitled", parent_id: id });
    window.location.assign(`/${slug}/wiki/${child.id}`);
  };

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6 px-8 py-10">
      <div className="flex flex-wrap items-center gap-2">
        <span className="rounded-md bg-layer-1 px-2 py-1 text-11 text-secondary">
          {page.access === 1 ? "Private" : "Public"}
        </span>
        {page.archived_at ? <span className="text-11 text-tertiary">Archived</span> : null}
        <Button
          variant="secondary"
          onClick={() => wikiService.favorite(slug, id, !page.is_favorite).then(() => mutate())}
        >
          {page.is_favorite ? "Unfavorite" : "Favorite"}
        </Button>
        {page.can_manage ? (
          <Button
            variant="secondary"
            onClick={() =>
              (page.archived_at ? wikiService.restorePage(slug, id) : wikiService.archivePage(slug, id)).then(() =>
                mutate()
              )
            }
          >
            {page.archived_at ? "Restore" : "Archive"}
          </Button>
        ) : null}
        {page.can_edit ? (
          <Button variant="secondary" onClick={nest}>
            Nested page
          </Button>
        ) : null}
        <Button variant="primary" onClick={save} disabled={!page.can_edit}>
          Save
        </Button>
      </div>
      <input
        value={title}
        onChange={(event) => setTitle(event.target.value)}
        placeholder="Untitled"
        disabled={!page.can_edit}
        className="text-xl w-full bg-transparent font-semibold text-primary outline-none placeholder:text-placeholder"
      />
      <textarea
        value={body}
        onChange={(event) => setBody(event.target.value)}
        disabled={!page.can_edit}
        placeholder="Write the page"
        className="min-h-64 w-full resize-y rounded-md border border-subtle bg-surface-1 px-3 py-2 text-13 text-primary outline-none"
      />
      {page.can_share ? (
        <section className="flex flex-col gap-2">
          <h2 className="text-13 font-medium text-secondary">Share</h2>
          <div className="flex gap-2">
            <select
              value={shareId}
              onChange={(event) => setShareId(event.target.value)}
              className="rounded-md border border-subtle bg-surface-1 px-2 py-1 text-13"
            >
              <option value="">Choose a member</option>
              {(members ?? []).map((member) => (
                <option key={member.id} value={member.id}>
                  {member.display_name}
                </option>
              ))}
            </select>
            <Button
              variant="secondary"
              disabled={!shareId}
              onClick={() => wikiService.share(slug, id, shareId, "comment").then(() => setShareId(""))}
            >
              Can comment
            </Button>
          </div>
        </section>
      ) : null}
      <section className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <h2 className="text-13 font-medium text-secondary">Link pages</h2>
          {page.can_edit ? (
            <Button variant="secondary" onClick={() => wikiService.createLinkBlock(slug, id, id)}>
              Insert
            </Button>
          ) : null}
        </div>
        {(blocks ?? []).map((block) => (
          <ul key={block.id} className="rounded-md border border-subtle px-3 py-2 text-13">
            {block.pages.length === 0 ? <li className="text-tertiary">No nested pages yet.</li> : null}
            {block.pages.map((linked) => (
              <li key={linked.id}>{linked.name || "Untitled"}</li>
            ))}
          </ul>
        ))}
      </section>
      <section className="flex flex-col gap-2">
        <h2 className="text-13 font-medium text-secondary">Comments</h2>
        <ul className="flex flex-col gap-2">
          {(comments ?? []).map((item) => (
            <li key={item.id} className="rounded-md border border-subtle px-3 py-2 text-13">
              <span className="text-tertiary">{item.actor?.display_name}</span>
              <p>{item.comment_stripped}</p>
            </li>
          ))}
        </ul>
        {page.can_comment ? (
          <div className="flex gap-2">
            <input
              value={comment}
              onChange={(event) => setComment(event.target.value)}
              placeholder="Comment"
              className="flex-1 rounded-md border border-subtle bg-surface-1 px-3 py-2 text-13 outline-none"
            />
            <Button
              variant="secondary"
              onClick={() =>
                wikiService.addComment(slug, id, comment).then(() => {
                  setComment("");
                  return mutateComments();
                })
              }
            >
              Comment
            </Button>
          </div>
        ) : null}
      </section>
      {stats ? (
        <p className="text-11 text-tertiary">
          {stats.viewers} viewers · {stats.nested_pages} nested pages · {stats.comments} comments
        </p>
      ) : null}
    </div>
  );
}
