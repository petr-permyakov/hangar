/**
 * Copyright (c) 2026-present Maciej Szymczak and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useState } from "react";
import { observer } from "mobx-react";
import { Link, useParams } from "react-router";
import useSWR from "swr";
import { Copy, MoreHorizontal, Pencil, Plus, Trash2 } from "lucide-react";
import { Button } from "@plane/propel/button";
import { TOAST_TYPE, setToast } from "@plane/propel/toast";
import { PageHead } from "@/components/core/page-title";
import { ExistingIssuesListModal } from "@/components/core/modals/existing-issues-list-modal";
import { useProject } from "@/hooks/store/use-project";
import { customerService } from "@/plane-web/services/customer.service";
import type { TCustomerRequestWrite, TCustomerWrite } from "@/plane-web/types/customer";
import { CustomerFormModal } from "../customer-form-modal";
import { CustomerRequestModal } from "../request-form-modal";

const Property = ({ label, value }: { label: string; value?: string | number | null }) => (
  <div className="flex flex-col gap-0.5 border-b border-subtle py-2">
    <span className="text-11 text-placeholder">{label}</span>
    <span className="text-body-xs-regular">{value || "—"}</span>
  </div>
);

const CustomerDetailPage = observer(function CustomerDetailPage() {
  const { workspaceSlug, customerId } = useParams();
  const slug = workspaceSlug?.toString() ?? "";
  const id = customerId?.toString() ?? "";
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isRequestOpen, setIsRequestOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [linkForRequestId, setLinkForRequestId] = useState<string | null>(null);
  const { workspaceProjectIds } = useProject();
  const projectId = workspaceProjectIds?.[0];

  const { data: customer, mutate: mutateCustomer } = useSWR(
    slug && id ? ["customer", slug, id] : null,
    () => customerService.retrieve(slug, id),
    { revalidateOnFocus: false }
  );
  const { data: requests, mutate: mutateRequests } = useSWR(
    slug && id ? ["customer-requests", slug, id] : null,
    () => customerService.listRequests(slug, id),
    { revalidateOnFocus: false }
  );

  if (!customer) {
    return <div className="p-6 text-body-sm-regular text-secondary">Loading customer…</div>;
  }

  const update = async (payload: TCustomerWrite) => {
    await customerService.update(slug, id, payload);
    setToast({ type: TOAST_TYPE.SUCCESS, title: "Customer updated" });
    setIsEditOpen(false);
    await mutateCustomer();
  };

  const createRequest = async (payload: TCustomerRequestWrite) => {
    await customerService.createRequest(slug, id, payload);
    setToast({ type: TOAST_TYPE.SUCCESS, title: "Request created" });
    setIsRequestOpen(false);
    await mutateRequests();
    await mutateCustomer();
  };

  const copyLink = async () => {
    await navigator.clipboard.writeText(window.location.href);
    setToast({ type: TOAST_TYPE.SUCCESS, title: "Link copied" });
    setMenuOpen(false);
  };

  const destroy = async () => {
    if (!window.confirm("Delete this customer? Requests and links are removed. Work items are kept.")) return;
    await customerService.destroy(slug, id);
    setToast({ type: TOAST_TYPE.SUCCESS, title: "Customer deleted" });
    window.location.href = `/${slug}/customers`;
  };

  return (
    <div className="flex h-full min-h-0">
      <PageHead title={`${customer.name} · Customers`} />
      <div className="flex min-w-0 flex-1 flex-col border-r border-subtle">
        <div className="flex items-center justify-between gap-3 border-b border-subtle px-6 py-3">
          <div>
            <Link to={`/${slug}/customers`} className="text-11 text-secondary hover:text-primary">
              Customers
            </Link>
            <h3 className="text-lg font-semibold">{customer.name}</h3>
          </div>
          <div className="relative">
            <Button variant="secondary" size="sm" onClick={() => setMenuOpen((open) => !open)}>
              <MoreHorizontal className="size-4" />
            </Button>
            {menuOpen && (
              <div className="absolute right-0 z-20 mt-1 w-48 rounded-md border border-subtle bg-surface-1 py-1 shadow-sm">
                <button
                  type="button"
                  className="flex w-full items-center gap-2 px-3 py-1.5 text-left text-body-xs-regular hover:bg-layer-transparent-hover"
                  onClick={() => {
                    setIsEditOpen(true);
                    setMenuOpen(false);
                  }}
                >
                  <Pencil className="size-3.5" /> Edit
                </button>
                <button
                  type="button"
                  className="flex w-full items-center gap-2 px-3 py-1.5 text-left text-body-xs-regular hover:bg-layer-transparent-hover"
                  onClick={copyLink}
                >
                  <Copy className="size-3.5" /> Copy link to customer
                </button>
                <button
                  type="button"
                  className="flex w-full items-center gap-2 px-3 py-1.5 text-left text-body-xs-regular text-danger hover:bg-layer-transparent-hover"
                  onClick={destroy}
                >
                  <Trash2 className="size-3.5" /> Delete
                </button>
              </div>
            )}
          </div>
        </div>
        <div className="flex items-center justify-between px-6 py-3">
          <h4 className="text-body-sm-medium">Requests</h4>
          <Button variant="primary" size="sm" onClick={() => setIsRequestOpen(true)}>
            <Plus className="size-3.5" /> Add request
          </Button>
        </div>
        <ul className="flex-1 overflow-y-auto px-6 pb-6">
          {(requests ?? []).length === 0 ? (
            <li className="rounded-md border border-dashed border-subtle p-6 text-body-xs-regular text-secondary">
              No requests yet. Capture an ask from a call, ticket, or Slack thread.
            </li>
          ) : (
            (requests ?? []).map((request) => (
              <li key={request.id} className="mb-3 rounded-md border border-subtle bg-surface-1 p-4">
                <p className="text-body-sm-medium">{request.name}</p>
                {request.description ? (
                  <p className="mt-1 text-body-xs-regular text-secondary">{request.description}</p>
                ) : null}
                {request.link ? (
                  <a
                    href={request.link}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-2 inline-block text-11 text-accent-primary"
                  >
                    {request.link}
                  </a>
                ) : null}
                <div className="mt-3">
                  <Button variant="secondary" size="sm" onClick={() => setLinkForRequestId(request.id)}>
                    Link work items
                  </Button>
                </div>
              </li>
            ))
          )}
        </ul>
      </div>
      <aside className="w-80 shrink-0 overflow-y-auto px-5 py-4">
        <h4 className="mb-2 text-body-sm-medium">Properties</h4>
        <Property label="Email" value={customer.email} />
        <Property label="Website" value={customer.website_url} />
        <Property label="Industry" value={customer.domain} />
        <Property label="Employees" value={customer.employees} />
        <Property label="Stage" value={customer.stage} />
        <Property label="Contract status" value={customer.contract_status} />
        <Property label="Revenue" value={customer.revenue} />
        <Property label="Description" value={customer.description} />
      </aside>
      <CustomerFormModal isOpen={isEditOpen} onClose={() => setIsEditOpen(false)} onSubmit={update} initial={customer} />
      <CustomerRequestModal isOpen={isRequestOpen} onClose={() => setIsRequestOpen(false)} onSubmit={createRequest} />
      <ExistingIssuesListModal
        workspaceSlug={slug}
        projectId={projectId}
        isOpen={linkForRequestId !== null}
        handleClose={() => setLinkForRequestId(null)}
        workspaceLevelToggle
        searchParams={{}}
        handleOnSubmit={async (selected) => {
          if (!linkForRequestId) return;
          await customerService.manageWorkItems(slug, id, {
            add: selected.map((item) => item.id),
            customer_request_id: linkForRequestId,
          });
          setToast({ type: TOAST_TYPE.SUCCESS, title: "Work items linked" });
          setLinkForRequestId(null);
        }}
      />
    </div>
  );
});

export default CustomerDetailPage;
