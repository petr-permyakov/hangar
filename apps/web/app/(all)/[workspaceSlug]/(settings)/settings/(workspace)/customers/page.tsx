/**
 * Copyright (c) 2026-present Maciej Szymczak and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { observer } from "mobx-react";
import { useParams } from "react-router";
import { Button } from "@plane/propel/button";
import { TOAST_TYPE, setToast } from "@plane/propel/toast";
import { ToggleSwitch } from "@plane/ui";
import { PageHead } from "@/components/core/page-title";
import { SettingsContentWrapper } from "@/components/settings/content-wrapper";
import { useCustomerFeatures } from "@/plane-web/hooks/use-customer-features";
import { customerService } from "@/plane-web/services/customer.service";

const CustomersSettingsPage = observer(function CustomersSettingsPage() {
  const { workspaceSlug } = useParams();
  const slug = workspaceSlug?.toString() ?? "";
  const { isCustomersEnabled, isLoading, mutate } = useCustomerFeatures(slug);

  const toggle = async (enabled: boolean) => {
    try {
      await customerService.updateFeatures(slug, enabled);
      await mutate();
      setToast({
        type: TOAST_TYPE.SUCCESS,
        title: enabled ? "Customers enabled" : "Customers disabled",
      });
    } catch {
      setToast({ type: TOAST_TYPE.ERROR, title: "Could not update Customers." });
    }
  };

  return (
    <SettingsContentWrapper>
      <PageHead title="Customers" />
      <div className="flex items-start justify-between gap-6 border-b border-subtle pb-6">
        <div>
          <h3 className="text-lg font-semibold">Customers</h3>
          <p className="mt-1 max-w-xl text-body-xs-regular text-secondary">
            Capture customer records, attach requests, and show who a work item is for. Members can read records and
            file requests. Only administrators can create or delete customers.
          </p>
        </div>
        {isLoading ? null : isCustomersEnabled ? (
          <ToggleSwitch value={isCustomersEnabled} onChange={toggle} />
        ) : (
          <Button variant="primary" size="sm" onClick={() => toggle(true)}>
            Enable Customers
          </Button>
        )}
      </div>
      {isCustomersEnabled ? (
        <p className="pt-6 text-body-xs-regular text-secondary">
          Custom properties for customer records land in a later change. Default fields are name, description, email,
          website, industry, employees, stage, contract status, and revenue.
        </p>
      ) : null}
    </SettingsContentWrapper>
  );
});

export default CustomersSettingsPage;
