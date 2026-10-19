/**
 * Copyright (c) 2026-present Maciej Szymczak and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { Outlet } from "react-router";
import { WikiShell } from "@/plane-web/components/wiki/shell";

export default function WikiLayout() {
  return (
    <WikiShell>
      <Outlet />
    </WikiShell>
  );
}
