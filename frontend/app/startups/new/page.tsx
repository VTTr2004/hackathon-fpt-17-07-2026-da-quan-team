"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { api } from "@/lib/api";
import { industryOptions, quickCreateFields, stageOptions } from "@/lib/profileFields";

import { useProfileDraft } from "./_components/ProfileDraftProvider";
import { cashFlowSections } from "./cash-flow/fields";

const moduleCards = [
  {
    id: "business",
    title: "Business Model",
    href: "/startups/new/business-model",
    sectionIds: ["quick-business", "quick-development"],
    detail: "Khách hàng, sản phẩm, doanh thu và kế hoạch phát triển",
  },
  {
    id: "cash",
    title: "Cash Flow",
    href: "/startups/new/cash-flow",
    sectionIds: ["quick-finance"],
    detail: "Số dư tiền và dòng tiền theo kỳ",
  },
  {
    id: "area",
    title: "Surrounding Area",
    href: "/startups/new/surrounding-area",
    sectionIds: ["quick-location"],
    detail: "Địa chỉ, phạm vi và tuyên bố về khu vực",
  },
];

function hasValue(value: unknown) {
  if (Array.isArray(value)) return value.length > 0;
  return value !== undefined && value !== null && String(value).trim() !== "";
}

export default function NewStartupOverviewPage() {
  const router = useRouter();
  const { draft, ready, cashFlowFiles, updateIdentity, clearDraft } = useProfileDraft();
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  async function createStartup() {
    if (!draft.identity.name.trim()) {
      setError("Vui lòng nhập tên startup trước khi tạo hồ sơ.");
      return;
    }
    setCreating(true);
    setError("");
    try {
      const startup = await api.createStartup({
        name: draft.identity.name.trim(),
        industry: draft.identity.industry || undefined,
        stage: draft.identity.stage || undefined,
        primary_location: draft.identity.location || undefined,
        facts: draft.facts,
      });
      for (const file of cashFlowFiles) {
        await api.uploadDocument(startup.id, file);
      }
      if (cashFlowFiles.length > 0) {
        await api.runAnalysis(startup.id, "cash_flow", {
          use_gemini: true,
          use_cash_flow_ingestion_agent: true,
          use_cash_flow_mapping_ai: true,
        });
      }
      clearDraft();
      router.push(`/startups/${startup.id}${cashFlowFiles.length > 0 ? "#tab-cashflow" : "#tab-overview"}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không thể tạo hồ sơ startup");
      setCreating(false);
    }
  }

  if (!ready) return <div className="hdCard"><p className="muted">Đang tải bản nháp hồ sơ...</p></div>;

  return (
    <div className="profileOverviewPage">
      {error && <div className="hdAlert"><span className="material-symbols-outlined">error</span><span>{error}</span></div>}
      <section className="hdCard profileIdentitySection">
        <div className="factSectionHeader">
          <div>
            <p className="eyebrow">THÔNG TIN CHUNG</p>
            <h2>Nhận diện hồ sơ</h2>
          </div>
          <p>Thông tin dùng chung cho cả ba module.</p>
        </div>
        <div className="factGrid profileIdentityGrid">
          <label>
            <span>Tên startup</span>
            <input
              required
              placeholder="Ví dụ: Mộc Coffee"
              value={draft.identity.name}
              onChange={(event) => updateIdentity({ name: event.target.value })}
              autoFocus
            />
          </label>
          <label>
            <span>Lĩnh vực</span>
            <select
              value={draft.identity.industry}
              onChange={(event) => updateIdentity({ industry: event.target.value })}
            >
              <option value="">Chọn lĩnh vực</option>
              {industryOptions.map((industry) => (
                <option key={industry}>{industry}</option>
              ))}
            </select>
          </label>
          <label>
            <span>Giai đoạn</span>
            <select value={draft.identity.stage} onChange={(event) => updateIdentity({ stage: event.target.value })}>
              <option value="">Chọn giai đoạn</option>
              {stageOptions.map((stage) => (
                <option key={stage}>{stage}</option>
              ))}
            </select>
          </label>
          <label>
            <span>Địa điểm chính</span>
            <input
              placeholder="Quận 1, TP.HCM"
              value={draft.identity.location}
              onChange={(event) => updateIdentity({ location: event.target.value })}
            />
          </label>
        </div>
      </section>

      <section className="moduleDraftGrid" aria-label="Tiến độ dữ liệu theo module">
        {moduleCards.map((module) => {
          const fields = (module.id === "cash" ? cashFlowSections : quickCreateFields)
            .filter((section) => module.id === "cash" || module.sectionIds.includes(section.id))
            .flatMap((section) => section.fields);
          const completed = fields.filter((field) => hasValue(draft.facts[field.key])).length;
          const progress = fields.length ? Math.round((completed / fields.length) * 100) : 0;
          return (
            <Link className="surface moduleDraftCard" href={module.href} key={module.id}>
              <div>
                <span className="eyebrow">{completed}/{fields.length} trường</span>
                <strong>{module.title}</strong>
                <p>{module.detail}</p>
              </div>
              <div className="progressTrack" aria-label={`Đã nhập ${progress}%`}>
                <span style={{ width: `${progress}%` }} />
              </div>
              <small>{progress}% · Mở trang nhập liệu →</small>
            </Link>
          );
        })}
      </section>

      <div className="profileSubmitBar">
        <div>
          <strong>Tạo hồ sơ khi đã nhập đủ dữ liệu cần thiết</strong>
          <span>Các module vẫn báo rõ trường còn thiếu sau khi hồ sơ được tạo.</span>
        </div>
        <div className="profileSubmitActions">
          <Link className="secondaryButton" href="/">
            Hủy
          </Link>
          <button className="primaryButton" disabled={creating} onClick={createStartup}>
            {creating
              ? cashFlowFiles.length > 0
                ? "Đang tạo và phân tích Excel..."
                : "Đang tạo hồ sơ..."
              : cashFlowFiles.length > 0
                ? `Tạo hồ sơ và phân tích ${cashFlowFiles.length} file`
                : "Tạo hồ sơ và tiếp tục"}
          </button>
        </div>
      </div>
    </div>
  );
}
