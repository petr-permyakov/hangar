/**
 * Copyright (c) 2026-present Maciej Szymczak and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { API_BASE_URL } from "@plane/constants";
import { APIService } from "@/services/api.service";
import type {
  TCustomer,
  TCustomerFeature,
  TCustomerRequest,
  TCustomerRequestWrite,
  TCustomerWrite,
  TIssueCustomer,
} from "@/plane-web/types/customer";

export class CustomerService extends APIService {
  constructor() {
    super(API_BASE_URL);
  }

  private unwrap<T>(promise: Promise<{ data: T }>): Promise<T> {
    return promise
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data ?? error;
      });
  }

  getFeatures(workspaceSlug: string): Promise<TCustomerFeature> {
    return this.unwrap(this.get(`/api/workspaces/${workspaceSlug}/customer-features/`));
  }

  updateFeatures(workspaceSlug: string, is_customers_enabled: boolean): Promise<TCustomerFeature> {
    return this.unwrap(this.patch(`/api/workspaces/${workspaceSlug}/customer-features/`, { is_customers_enabled }));
  }

  list(workspaceSlug: string, search?: string): Promise<TCustomer[]> {
    const query = search ? `?search=${encodeURIComponent(search)}` : "";
    return this.unwrap(this.get(`/api/workspaces/${workspaceSlug}/customers/${query}`));
  }

  retrieve(workspaceSlug: string, customerId: string): Promise<TCustomer> {
    return this.unwrap(this.get(`/api/workspaces/${workspaceSlug}/customers/${customerId}/`));
  }

  create(workspaceSlug: string, data: TCustomerWrite): Promise<TCustomer> {
    return this.unwrap(this.post(`/api/workspaces/${workspaceSlug}/customers/`, data));
  }

  update(workspaceSlug: string, customerId: string, data: TCustomerWrite): Promise<TCustomer> {
    return this.unwrap(this.patch(`/api/workspaces/${workspaceSlug}/customers/${customerId}/`, data));
  }

  destroy(workspaceSlug: string, customerId: string): Promise<void> {
    return this.unwrap(this.delete(`/api/workspaces/${workspaceSlug}/customers/${customerId}/`));
  }

  listRequests(workspaceSlug: string, customerId: string): Promise<TCustomerRequest[]> {
    return this.unwrap(this.get(`/api/workspaces/${workspaceSlug}/customers/${customerId}/requests/`));
  }

  createRequest(workspaceSlug: string, customerId: string, data: TCustomerRequestWrite): Promise<TCustomerRequest> {
    return this.unwrap(this.post(`/api/workspaces/${workspaceSlug}/customers/${customerId}/requests/`, data));
  }

  updateRequest(
    workspaceSlug: string,
    customerId: string,
    requestId: string,
    data: TCustomerRequestWrite
  ): Promise<TCustomerRequest> {
    return this.unwrap(this.patch(`/api/workspaces/${workspaceSlug}/customers/${customerId}/requests/${requestId}/`, data));
  }

  destroyRequest(workspaceSlug: string, customerId: string, requestId: string): Promise<void> {
    return this.unwrap(this.delete(`/api/workspaces/${workspaceSlug}/customers/${customerId}/requests/${requestId}/`));
  }

  listWorkItems(workspaceSlug: string, customerId: string, customerRequestId?: string) {
    const query = customerRequestId ? `?customer_request_id=${customerRequestId}` : "";
    return this.unwrap(this.get(`/api/workspaces/${workspaceSlug}/customers/${customerId}/work-items/${query}`));
  }

  manageWorkItems(
    workspaceSlug: string,
    customerId: string,
    payload: { add?: string[]; remove?: string[]; customer_request_id?: string }
  ) {
    return this.unwrap(this.post(`/api/workspaces/${workspaceSlug}/customers/${customerId}/work-items/`, payload));
  }

  listIssueCustomers(workspaceSlug: string, projectId: string, issueId: string): Promise<TIssueCustomer[]> {
    return this.unwrap(this.get(`/api/workspaces/${workspaceSlug}/projects/${projectId}/issues/${issueId}/customers/`));
  }

  manageIssueCustomers(
    workspaceSlug: string,
    projectId: string,
    issueId: string,
    payload: { add?: string[]; remove?: string[] }
  ) {
    return this.unwrap(
      this.post(`/api/workspaces/${workspaceSlug}/projects/${projectId}/issues/${issueId}/customers/`, payload)
    );
  }
}

export const customerService = new CustomerService();
