/**
 * Copyright (c) 2026-present Maciej Szymczak and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useMemo, useState } from "react";
import { observer } from "mobx-react";
import { Link, useParams } from "react-router";
import useSWR from "swr";
import { Building2, Plus, Search } from "lucide-react";
import { Button } from "@plane/propel/button";
import { TOAST_TYPE, setToast } from "@plane/propel/toast";
import { PageHead } from "@/components/core/page-title";
import { NotAuthorizedView } from "@/components/auth-screens/not-authorized-view";
import { customerService } from "@/plane-web/services/customer.service";
import { useCustomerFeatures } from "@/plane-web/hooks/use-customer-features";
import type { TCustomerWrite } from "@/plane-web/types/customer";
import { CustomerFormModal } from "./customer-form-modal";

const CustomersPage = observer(function CustomersPage() {
  const { workspaceSlug } = useParams();
  const slug = workspaceSlug?.toString() ?? "";
  const { isCustomersEnabled, isLoading: featureLoading } = useCustomerFeatures(slug);
  const [search, setSearch] = useState("");
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  const { data: customers, mutate, isLoading } = useSWR(
    slug && isCustomersEnabled ? ["customers", slug, search] : null,
    () => customerService.list(slug, search || undefined),
    { revalidateOnFocus: false }
  );

  const rows = useMemo(() => customers ?? [], [customers]);

  if (!featureLoading && !isCustomersEnabled) {
    return (
      <NotAuthorizedView
        actionButton={
          <Link to={`/${slug}/settings/customers`}>
            <Button variant="primary">Enable Customers</Button>
          </Link>
        }
      />
    );
  }

  const create = async (payload: TCustomerWrite) => {
    try {
      await customerService.create(slug, payload);
      setToast({ type: TOAST_TYPE.SUCCESS, title: "Customer created" });
      setIsCreateOpen(false);
      await mutate();
    } catch {
      setToast({ type: TOAST_TYPE.ERROR, title: "Could not create the customer." });
    }
  };

  return (
    <div className="flex h-full w-full flex-col">
      <PageHead title="Customers" />
      <div className="flex items-center justify-between gap-3 border-b border-subtle px-6 py-3">
        <div>
          <h3 className="text-lg font-semibold">Customers</h3>
          <p className="text-body-xs-regular text-secondary">Who you build for, and the requests they have made.</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 rounded-md border border-subtle px-2">
            <Search className="size-3.5 text-placeholder" />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search customers"
              className="h-8 w-48 bg-transparent text-body-xs-regular outline-none"
            />
          </div>
          <Button variant="primary" size="sm" onClick={() => setIsCreateOpen(true)}>
            <Plus className="size-3.5" />
            Create customer record
          </Button>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-6">
        {isLoading ? (
          <p className="text-body-sm-regular text-secondary">Loading customers…</p>
        ) : rows.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-3 py-24 text-center">
            <Building2 className="size-10 text-placeholder" />
            <p className="text-body-sm-medium">No customer records yet</p>
            <p className="max-w-md text-body-xs-regular text-secondary">
              Create a customer to capture requests and link them to work items.
            </p>
            <Button variant="primary" size="sm" onClick={() => setIsCreateOpen(true)}>
              Create customer record
            </Button>
          </div>
        ) : (
          <ul className="divide-y divide-subtle rounded-lg border border-subtle bg-surface-1">
            {rows.map((customer) => (
              <li key={customer.id}>
                <Link
                  to={`/${slug}/customers/${customer.id}`}
                  className="flex items-center justify-between gap-4 px-4 py-3 hover:bg-layer-transparent-hover"
                >
                  <div className="flex min-w-0 items-center gap-3">
                    <div className="flex size-9 shrink-0 items-center justify-center rounded-md bg-layer-2 text-body-sm-medium">
                      {customer.name.slice(0, 1).toUpperCase()}
                    </div>
                    <div className="min-w-0">
                      <p className="truncate text-body-sm-medium">{customer.name}</p>
                      <p className="truncate text-11 text-secondary">
                        {customer.website_url || customer.email || customer.domain || "—"}
                      </p>
                    </div>
                  </div>
                  <div className="flex shrink-0 items-center gap-6 text-11 text-secondary">
                    <span>{customer.stage || "No stage"}</span>
                    <span>{customer.contract_status || "No contract"}</span>
                    <span>{customer.revenue || "—"}</span>
                    <span>
                      {customer.customer_request_count} request{customer.customer_request_count === 1 ? "" : "s"}
                    </span>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
      <CustomerFormModal isOpen={isCreateOpen} onClose={() => setIsCreateOpen(false)} onSubmit={create} />
    </div>
  );
});

export default CustomersPage;
