/**
 * Copyright (c) 2026-present Maciej Szymczak and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useState } from "react";
import { Link } from "react-router";
import useSWR from "swr";
import { Building2, ChevronRight } from "lucide-react";
import { useCustomerFeatures } from "@/plane-web/hooks/use-customer-features";
import { customerService } from "@/plane-web/services/customer.service";
import { issueCustomersKey } from "@/plane-web/components/issues/customers/property/root";

type Props = {
  workspaceSlug: string;
  projectId: string;
  issueId: string;
};

export function CustomerRequestsCollapsible(props: Props) {
  const { workspaceSlug, projectId, issueId } = props;
  const { isCustomersEnabled } = useCustomerFeatures(workspaceSlug);
  const [open, setOpen] = useState(true);
  const { data: links } = useSWR(
    isCustomersEnabled ? issueCustomersKey(workspaceSlug, projectId, issueId) : null,
    () => customerService.listIssueCustomers(workspaceSlug, projectId, issueId),
    { revalidateOnFocus: false }
  );

  if (!isCustomersEnabled || !links?.length) return null;

  return (
    <div className="border-b border-subtle">
      <button
        type="button"
        className="flex w-full items-center gap-2 px-2 py-2 text-left text-body-xs-medium"
        onClick={() => setOpen((value) => !value)}
      >
        <ChevronRight className={`size-3.5 transition-transform ${open ? "rotate-90" : ""}`} />
        <Building2 className="size-3.5" />
        Customer requests
        <span className="text-placeholder">({links.length})</span>
      </button>
      {open ? (
        <ul className="space-y-1 px-8 pb-3">
          {links.map((row) => (
            <li key={row.id} className="text-body-xs-regular">
              <Link to={`/${workspaceSlug}/customers/${row.customer_id}`} className="text-primary hover:underline">
                {row.name}
              </Link>
              {row.customer_request_name ? (
                <span className="text-secondary"> · {row.customer_request_name}</span>
              ) : null}
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
