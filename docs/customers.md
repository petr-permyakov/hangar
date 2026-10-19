# Customers and customer requests

Hangar Customers is a workspace CRM: records of the organisations you build
for, the requests they have made, and the work items that satisfy those
requests. It is off until a workspace administrator enables it.

This is not Plane Intake. Intake is the queue of incoming work items in
Triage. A customer request is a named ask attached to a customer record. The
same Customers field appears on intake items so a Triage item can already say
who it is for.

## Enable Customers

1. Open **Workspace settings → Customers**.
2. Choose **Enable Customers**.

Members can then open **Customers** in the workspace sidebar. Guests cannot
read customer records.

## Customer records

Create a record from **Customers → Create customer record**. Name is required.
The rest of the default fields are description, email, website, industry
(`domain` in the API), employees, stage, contract status, and revenue.

Administrators can create, update, and delete records. Members can read them
and file requests. Deleting a customer removes its requests and work-item
links; the work items themselves stay.

## Requests

Open a customer and choose **Add request**. A request has a name, an optional
description, and an optional source URL (http or https). From the request you
can **Link work items** that already exist.

A work item can also be linked to a customer directly from the work-item
sidebar **Customers** field, including on intake items. Linked customers and
request names appear in the work-item detail collapsible.

## Permissions

| Action                                      | Admin | Member | Guest |
| ------------------------------------------- | ----- | ------ | ----- |
| Enable or disable Customers                 | Yes   | No     | No    |
| Create, update, or delete a customer        | Yes   | No     | No    |
| Read customers and requests                 | Yes   | Yes    | No    |
| Create or edit a request                    | Yes   | Yes    | No    |
| Link or unlink work items                   | Yes   | Yes    | No    |

Work-item links only include issues the caller can already see.

## API

All paths sit under `/api/workspaces/<slug>/` and require a workspace session
cookie. The feature switch lives at `customer-features/`. Customer CRUD is
`customers/` with an `upsert/` match on `external_source` + `external_id`,
then name. Requests are `customers/<id>/requests/`. Work-item links are
`customers/<id>/work-items/` and
`/api/workspaces/<slug>/projects/<project_id>/issues/<issue_id>/customers/`.

Work items can be filtered with `?customer=<uuid>[,<uuid>]`.

Field names follow Plane API v2 (`website_url`, `domain` as industry, a
single `link` on a request). `revenue_amount` is Hangar-only and unused in
the first UI.

## Out of scope for this release

Custom properties on customer records, logos, the full Plane Intake product
(forms, email, Slack, AI, extra layouts), and creating a customer request
from an intake item.
