/**
 * Copyright (c) 2026-present Maciej Szymczak and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useMemo, useState } from "react";
import { observer } from "mobx-react";
import { Link } from "react-router";
import useSWR, { mutate } from "swr";
import { Building2 } from "lucide-react";
import { SidebarPropertyListItem } from "@/components/common/layout/sidebar/property-list-item";
import { useCustomerFeatures } from "@/plane-web/hooks/use-customer-features";
import { customerService } from "@/plane-web/services/customer.service";

type Props = {
  workspaceSlug: string;
  projectId: string;
  issueId: string;
  disabled: boolean;
};

export const issueCustomersKey = (workspaceSlug: string, projectId: string, issueId: string) =>
  ["issue-customers", workspaceSlug, projectId, issueId] as const;

export const IssueCustomersProperty = observer(function IssueCustomersProperty(props: Props) {
  const { workspaceSlug, projectId, issueId, disabled } = props;
  const { isCustomersEnabled } = useCustomerFeatures(workspaceSlug);
  const [pickerOpen, setPickerOpen] = useState(false);
  const { data: customers } = useSWR(
    isCustomersEnabled ? ["customers", workspaceSlug] : null,
    () => customerService.list(workspaceSlug),
    { revalidateOnFocus: false }
  );
  const { data: links } = useSWR(
    isCustomersEnabled ? issueCustomersKey(workspaceSlug, projectId, issueId) : null,
    () => customerService.listIssueCustomers(workspaceSlug, projectId, issueId),
    { revalidateOnFocus: false }
  );

  const selectedIds = useMemo(() => new Set((links ?? []).map((row) => row.customer_id)), [links]);

  if (!isCustomersEnabled) return null;

  const toggle = async (customerId: string) => {
    const remove = selectedIds.has(customerId);
    await customerService.manageIssueCustomers(workspaceSlug, projectId, issueId, {
      add: remove ? [] : [customerId],
      remove: remove ? [customerId] : [],
    });
    await mutate(issueCustomersKey(workspaceSlug, projectId, issueId));
  };

  return (
    <>
      <SidebarPropertyListItem icon={Building2} label="Customers">
        <button
          type="button"
          disabled={disabled}
          onClick={() => setPickerOpen((open) => !open)}
          className="flex min-h-7.5 w-full flex-wrap items-center gap-1 rounded px-2 text-left text-body-xs-regular text-secondary hover:bg-layer-1"
        >
          {(links ?? []).length === 0 ? (
            <span className="text-placeholder">{disabled ? "—" : "Add customers"}</span>
          ) : (
            (links ?? []).map((row) => (
              <Link
                key={row.id}
                to={`/${workspaceSlug}/customers/${row.customer_id}`}
                className="rounded bg-layer-2 px-1.5 py-0.5 text-11 text-primary"
                title={row.customer_request_name ? `${row.name} · ${row.customer_request_name}` : row.name}
                onClick={(event) => event.stopPropagation()}
              >
                {row.name}
                {row.customer_request_name ? ` · ${row.customer_request_name}` : ""}
              </Link>
            ))
          )}
        </button>
      </SidebarPropertyListItem>
      {pickerOpen && !disabled ? (
        <div className="mb-2 max-h-48 overflow-y-auto rounded-md border border-subtle bg-surface-1 p-2">
          {(customers ?? []).map((customer) => (
            <label key={customer.id} className="flex items-center gap-2 py-1 text-body-xs-regular">
              <input
                type="checkbox"
                checked={selectedIds.has(customer.id)}
                onChange={() => toggle(customer.id)}
              />
              {customer.name}
            </label>
          ))}
        </div>
      ) : null}
    </>
  );
});
