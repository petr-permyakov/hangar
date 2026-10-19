/**
 * Copyright (c) 2026-present Maciej Szymczak and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

export type TCustomer = {
  id: string;
  name: string;
  description: string;
  description_html: string;
  email: string;
  website_url: string;
  domain: string;
  employees: number | null;
  stage: string;
  contract_status: string;
  revenue: string;
  revenue_amount: string | null;
  logo_url: string | null;
  logo_props: Record<string, unknown>;
  external_source: string | null;
  external_id: string | null;
  archived_at: string | null;
  customer_request_count: number;
  created_at: string;
  updated_at: string;
};

export type TCustomerRequest = {
  id: string;
  customer_id: string;
  name: string;
  description: string;
  description_html: string;
  link: string;
  archived_at: string | null;
  created_at: string;
  updated_at: string;
};

export type TIssueCustomer = {
  id: string;
  customer_id: string;
  name: string;
  website_url: string;
  stage: string;
  contract_status: string;
  revenue: string;
  customer_request_id: string | null;
  customer_request_name: string | null;
};

export type TCustomerFeature = {
  is_customers_enabled: boolean;
  customers_enabled_at: string | null;
};

export type TCustomerWrite = Partial<
  Pick<
    TCustomer,
    | "name"
    | "description"
    | "description_html"
    | "email"
    | "website_url"
    | "domain"
    | "employees"
    | "stage"
    | "contract_status"
    | "revenue"
  >
>;

export type TCustomerRequestWrite = Partial<Pick<TCustomerRequest, "name" | "description" | "description_html" | "link">> & {
  work_item_ids?: string[];
};
