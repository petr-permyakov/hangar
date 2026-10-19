/**
 * Copyright (c) 2026-present Maciej Szymczak and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useEffect, useState } from "react";
import { Button } from "@plane/propel/button";
import { EModalPosition, EModalWidth, ModalCore } from "@plane/ui";
import type { TCustomer, TCustomerWrite } from "@/plane-web/types/customer";

type Props = {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (payload: TCustomerWrite) => Promise<void>;
  initial?: TCustomer | null;
};

const EMPTY: TCustomerWrite = {
  name: "",
  email: "",
  website_url: "",
  domain: "",
  stage: "",
  contract_status: "",
  revenue: "",
  description: "",
};

export function CustomerFormModal(props: Props) {
  const { isOpen, onClose, onSubmit, initial } = props;
  const [form, setForm] = useState<TCustomerWrite>(EMPTY);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    setForm(
      initial
        ? {
            name: initial.name,
            email: initial.email,
            website_url: initial.website_url,
            domain: initial.domain,
            stage: initial.stage,
            contract_status: initial.contract_status,
            revenue: initial.revenue,
            description: initial.description,
            employees: initial.employees ?? undefined,
          }
        : EMPTY
    );
  }, [isOpen, initial]);

  const set = (key: keyof TCustomerWrite, value: string) => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  const submit = async () => {
    if (!form.name?.trim()) return;
    setSaving(true);
    try {
      await onSubmit({
        ...form,
        employees: form.employees ? Number(form.employees) : null,
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <ModalCore isOpen={isOpen} handleClose={onClose} position={EModalPosition.CENTER} width={EModalWidth.XXL}>
      <div className="flex flex-col gap-4 p-5">
        <h3 className="text-lg font-semibold">{initial ? "Update customer" : "Create customer record"}</h3>
        <div className="grid grid-cols-2 gap-3">
          <label className="col-span-2 flex flex-col gap-1 text-11 text-secondary">
            Name
            <input
              className="h-8 rounded-md border border-subtle bg-surface-1 px-2 text-body-xs-regular"
              value={form.name ?? ""}
              onChange={(event) => set("name", event.target.value)}
            />
          </label>
          <label className="flex flex-col gap-1 text-11 text-secondary">
            Email
            <input
              className="h-8 rounded-md border border-subtle bg-surface-1 px-2 text-body-xs-regular"
              value={form.email ?? ""}
              onChange={(event) => set("email", event.target.value)}
            />
          </label>
          <label className="flex flex-col gap-1 text-11 text-secondary">
            Website
            <input
              className="h-8 rounded-md border border-subtle bg-surface-1 px-2 text-body-xs-regular"
              value={form.website_url ?? ""}
              onChange={(event) => set("website_url", event.target.value)}
            />
          </label>
          <label className="flex flex-col gap-1 text-11 text-secondary">
            Industry
            <input
              className="h-8 rounded-md border border-subtle bg-surface-1 px-2 text-body-xs-regular"
              value={form.domain ?? ""}
              onChange={(event) => set("domain", event.target.value)}
            />
          </label>
          <label className="flex flex-col gap-1 text-11 text-secondary">
            Stage
            <input
              className="h-8 rounded-md border border-subtle bg-surface-1 px-2 text-body-xs-regular"
              value={form.stage ?? ""}
              onChange={(event) => set("stage", event.target.value)}
            />
          </label>
          <label className="flex flex-col gap-1 text-11 text-secondary">
            Contract status
            <input
              className="h-8 rounded-md border border-subtle bg-surface-1 px-2 text-body-xs-regular"
              value={form.contract_status ?? ""}
              onChange={(event) => set("contract_status", event.target.value)}
            />
          </label>
          <label className="flex flex-col gap-1 text-11 text-secondary">
            Revenue
            <input
              className="h-8 rounded-md border border-subtle bg-surface-1 px-2 text-body-xs-regular"
              value={form.revenue ?? ""}
              onChange={(event) => set("revenue", event.target.value)}
            />
          </label>
          <label className="col-span-2 flex flex-col gap-1 text-11 text-secondary">
            Description
            <textarea
              className="min-h-20 rounded-md border border-subtle bg-surface-1 px-2 py-1.5 text-body-xs-regular"
              value={form.description ?? ""}
              onChange={(event) => set("description", event.target.value)}
            />
          </label>
        </div>
        <div className="flex justify-end gap-2">
          <Button variant="neutral-primary" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="primary" size="sm" onClick={submit} disabled={saving || !form.name?.trim()}>
            {initial ? "Update customer" : "Create customer record"}
          </Button>
        </div>
      </div>
    </ModalCore>
  );
}
