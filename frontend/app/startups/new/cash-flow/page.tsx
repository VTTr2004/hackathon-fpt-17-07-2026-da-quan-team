"use client";

import { ModuleFormPage } from "../_components/ModuleFormPage";
import { cashFlowGroups, cashFlowSections } from "./fields";

export default function CashFlowProfilePage() {
  return (
    <ModuleFormPage
      eyebrow="MODULE 02"
      title="Cash Flow Analysis"
      description="Số dư tiền và dòng tiền theo kỳ để tính burn, runway và chạy stress scenario."
      sections={cashFlowSections}
      groupsBySection={cashFlowGroups}
      previousHref="/startups/new/business-model"
      nextHref="/startups/new/surrounding-area"
    />
  );
}
