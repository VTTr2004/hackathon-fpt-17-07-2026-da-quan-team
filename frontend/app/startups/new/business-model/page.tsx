"use client";

import { ModuleFormPage } from "../_components/ModuleFormPage";
import { businessModelGroups, businessModelSections } from "./fields";

export default function BusinessModelProfilePage() {
  return (
    <ModuleFormPage
      eyebrow="MODULE 01"
      title="Business Model Analysis"
      description="Khách hàng, sản phẩm, mô hình doanh thu, unit economics cấp đơn hàng và kế hoạch phát triển."
      sections={businessModelSections}
      groupsBySection={businessModelGroups}
      previousHref="/startups/new"
      nextHref="/startups/new/cash-flow"
    />
  );
}
