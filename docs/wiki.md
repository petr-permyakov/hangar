# Workspace wiki

The wiki is the workspace knowledge base: pages that are not attached to a
project. It is on for every workspace until an admin turns it off under
Workspace settings, Wiki. While it is off, the wiki routes stay closed and the
v2 page and collection endpoints answer `402`. Existing pages stay stored.
Personal stickies stay available either way.

Workspace guests cannot open the wiki. A private page or a private collection
is visible to its owner and to the people added to it. A workspace admin does
not see those unless they own them or were added. Only an admin can create a
private collection.

## Pages and collections

A new public page lands in **General**, the default collection. General cannot
be deleted. A private page stays outside every collection until someone moves
it. Nested pages follow their top-level page: they share its collection, its
visibility, and its shares.

Moving a page between two public collections keeps its readers. A move that
changes who can see the page returns `409` until the request sends `confirm`.
Moving a private page into a public collection makes it public and drops its
shares.

Archive a page before deleting it. Archiving or deleting a page does the same
to its nested pages. Restoring a nested page whose parent is still archived
detaches it.

## Sharing, labels, and published pages

Only the owner of a top-level private page can share it, with view, comment,
or edit. A comment share can comment and cannot rewrite the page.

Page labels belong to the workspace and are separate from work-item labels.
Admins manage them from Wiki settings.

Publishing a page creates an unguessable anchor. The public read is
`GET /api/workspaces/<slug>/wiki/published/<anchor>/`. Archiving the page
removes the publication. An instance that forces private visibility refuses
new public pages and new publications.

## Notes

Stickies remain the personal notes product. The wiki home lists the caller's
own stickies. The v2 sticky endpoints wrap the same rows and never return
another person's notes.

## Where it lives

Workspace routes are under `/<slug>/wiki`. The app API is
`/api/workspaces/<slug>/wiki/`. The v2 shapes are
`/api/v2/workspaces/<slug>/pages`, `.../collections`, and `.../stickies`.
Command search returns project pages with their project ids and wiki pages
with an empty project list, so a wiki hit opens on the wiki route.
