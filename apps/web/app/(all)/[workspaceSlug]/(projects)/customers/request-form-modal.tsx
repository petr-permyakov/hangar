/**
 * Copyright (c) 2026-present Maciej Szymczak and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useEffect, useState } from "react";
import { Button } from "@plane/propel/button";
import { EModalPosition, EModalWidth, ModalCore } from "@plane/ui";
import type { TCustomerRequestWrite } from "@/plane-web/types/customer";

type Props = {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (payload: TCustomerRequestWrite) => Promise<void>;
};

export function CustomerRequestModal(props: Props) {
  const { isOpen, onClose, onSubmit } = props;
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [link, setLink] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    setName("");
    setDescription("");
    setLink("");
  }, [isOpen]);

  const submit = async () => {
    if (!name.trim()) return;
    setSaving(true);
    try {
      await onSubmit({ name: name.trim(), description, link });
    } finally {
      setSaving(false);
    }
  };

  return (
    <ModalCore isOpen={isOpen} handleClose={onClose} position={EModalPosition.CENTER} width={EModalWidth.XL}>
      <div className="flex flex-col gap-4 p-5">
        <h3 className="text-lg font-semibold">Add request</h3>
        <label className="flex flex-col gap-1 text-11 text-secondary">
          Name
          <input
            className="h-8 rounded-md border border-subtle bg-surface-1 px-2 text-body-xs-regular"
            value={name}
            onChange={(event) => setName(event.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1 text-11 text-secondary">
          Description
          <textarea
            className="min-h-24 rounded-md border border-subtle bg-surface-1 px-2 py-1.5 text-body-xs-regular"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1 text-11 text-secondary">
          Source URL
          <input
            className="h-8 rounded-md border border-subtle bg-surface-1 px-2 text-body-xs-regular"
            placeholder="https://"
            value={link}
            onChange={(event) => setLink(event.target.value)}
          />
        </label>
        <div className="flex justify-end gap-2">
          <Button variant="secondary" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="primary" size="sm" onClick={submit} disabled={saving || !name.trim()}>
            Create request
          </Button>
        </div>
      </div>
    </ModalCore>
  );
}
