"use client";

import { ModuleFormPage } from "../_components/ModuleFormPage";
import { surroundingAreaGroups, surroundingAreaSections } from "./fields";

export default function SurroundingAreaProfilePage() {
  return (
    <ModuleFormPage
      eyebrow="MODULE 03"
      title="Surrounding Area Analysis"
      description="Địa chỉ, mức phụ thuộc vị trí và các tuyên bố cần kiểm chứng bằng dữ liệu bản đồ."
      sections={surroundingAreaSections}
      groupsBySection={surroundingAreaGroups}
      previousHref="/startups/new/cash-flow"
      nextHref="/startups/new"
      nextLabel="Lưu và về tổng quan"
    />
  );
}
