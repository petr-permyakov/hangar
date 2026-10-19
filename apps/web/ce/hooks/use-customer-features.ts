/**
 * Copyright (c) 2026-present Maciej Szymczak and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import useSWR from "swr";
import { customerService } from "@/plane-web/services/customer.service";

export const customerFeatureKey = (workspaceSlug: string) => ["customer-features", workspaceSlug] as const;

export function useCustomerFeatures(workspaceSlug: string | undefined) {
  const { data, mutate, isLoading } = useSWR(
    workspaceSlug ? customerFeatureKey(workspaceSlug) : null,
    workspaceSlug ? () => customerService.getFeatures(workspaceSlug) : null,
    { revalidateOnFocus: false }
  );
  return {
    isCustomersEnabled: Boolean(data?.is_customers_enabled),
    isLoading,
    mutate,
    features: data,
  };
}
