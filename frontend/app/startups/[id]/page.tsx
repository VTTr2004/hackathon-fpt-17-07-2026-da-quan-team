"use client";

import { FormEvent, use, useCallback, useEffect, useMemo, useState } from "react";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { isValidTab, tabsForRole } from "@/lib/deskTabs";
import {
  cashFlowProfileSections,
  developmentPlanSections,
  documentChecklist,
  formatProfileValue,
  profileSections,
  readProfileField,
  stageOptions,
  textValue,
} from "@/lib/profileFields";
import type { ProfileField } from "@/lib/profileFields";
import type {
  Analysis,
  AnalysisModule,
  Completeness,
  DocumentItem,
  InvestorAccess,
  Startup,
  StartupVersion,
  VersionDiff,
} from "@/types";

import CashFlowAnalysis from "./CashFlowAnalysis";
import CashFlowDataWorkspace from "./CashFlowDataWorkspace";
import ChatWidget from "./ChatWidget";
import ExtractionReview from "./ExtractionReview";
import SurroundingArea from "./SurroundingArea";

const modules: Array<{ id: AnalysisModule; name: string; icon: string; tone: string; description: string }> = [
  { id: "business_model", name: "Mô hình kinh doanh", icon: "storefront", tone: "", description: "Khách hàng, doanh thu và khả năng mở rộng" },
  { id: "cash_flow", name: "Dòng tiền", icon: "monitoring", tone: "blue", description: "Burn rate, runway và stress scenario" },
  { id: "surrounding_area", name: "Khu vực xung quanh", icon: "map", tone: "amber", description: "POI, đối thủ và kiểm chứng địa điểm" },
];

function latestByModule(analyses: Analysis[]) {
  return modules.reduce<Record<AnalysisModule, Analysis | undefined>>((result, module) => {
    result[module.id] = analyses.find((analysis) => analysis.module === module.id);
    return result;
  }, { business_model: undefined, cash_flow: undefined, surrounding_area: undefined });
}

function MIcon({ name }: { name: string }) {
  return <span className="material-symbols-outlined" aria-hidden="true">{name}</span>;
}

const STATUS_LABEL: Record<string, string> = {
  completed: "Hoàn tất",
  insufficient_data: "Thiếu dữ liệu",
  partial: "Một phần",
  not_applicable: "Không áp dụng",
  failed: "Lỗi",
};
function statusLabel(s?: string) {
  return s ? STATUS_LABEL[s] ?? s : "Chưa chạy";
}
function countArr(value: unknown) {
  return Array.isArray(value) ? value.length : 0;
}
function moduleMetrics(a: Analysis | undefined, hint: string) {
  return [
    { label: "Điểm", value: a?.score == null ? "—" : String(Math.round(a.score)), icon: "target", hint: "trên 100" },
    { label: "Trạng thái", value: statusLabel(a?.status), icon: "flag", hint },
    { label: "Rủi ro", value: String(countArr(a?.report?.risks)), icon: "warning", hint: "cần lưu ý" },
    { label: "Thiếu dữ liệu", value: String(countArr(a?.report?.missing_data)), icon: "help", hint: "cần bổ sung" },
  ];
}

function numericFact(value: unknown): number | null {
  if (value === null || value === undefined || value === "") return null;
  const number = Number(String(value).replace(/[\s,]/g, ""));
  return Number.isFinite(number) && number >= 0 ? number : null;
}

function computedCashFlowValue(field: ProfileField, facts: Record<string, unknown>): string {
  const revenue = numericFact(facts.monthly_revenue);
  const fixed = numericFact(facts.fixed_monthly_costs);
  const variable = numericFact(facts.variable_costs);
  if (field.computed === "monthly_expense") {
    return fixed !== null && variable !== null ? String(fixed + variable) : "";
  }
  if (field.computed === "variable_cost_ratio") {
    return revenue !== null && revenue > 0 && variable !== null
      ? String(Math.round((variable / revenue) * 1_000_000) / 1_000_000)
      : "";
  }
  return "";
}

function recalculateCashFlowForm(form: HTMLFormElement) {
  const read = (name: string) => numericFact((form.elements.namedItem(name) as HTMLInputElement | null)?.value);
  const write = (name: string, value: number | null) => {
    const input = form.elements.namedItem(name) as HTMLInputElement | null;
    if (input) input.value = value === null ? "" : String(value);
  };
  const revenue = read("monthly_revenue");
  const fixed = read("fixed_monthly_costs");
  const variable = read("variable_costs");
  write("monthly_expense", fixed !== null && variable !== null ? fixed + variable : null);
  write(
    "variable_cost_ratio",
    revenue !== null && revenue > 0 && variable !== null
      ? Math.round((variable / revenue) * 1_000_000) / 1_000_000
      : null,
  );
}

const tabLeads: Record<string, string> = {
  overview: "Tổng hợp nhanh trạng thái hồ sơ và các việc cần làm tiếp theo.",
  business: "Đánh giá mô hình kinh doanh, thị trường, khách hàng và rủi ro cần hỏi thêm.",
  profile: "Cập nhật dữ liệu nền của startup trước khi nộp phiên bản chính thức.",
  development: "Xây dựng mục tiêu, milestone và năng lực thực thi cho kế hoạch phát triển.",
  cashflow: "Chuẩn hóa dữ liệu dòng tiền và xem runway, burn rate, kịch bản căng thẳng.",
  area: "Xác nhận vị trí, quét POI, đối thủ và các tuyên bố phụ thuộc khu vực.",
  evidence: "Quản lý tài liệu nguồn dùng cho phân tích và hỏi đáp có trích dẫn.",
  review: "Theo dõi phiên bản, quyền truy cập và các điểm cần rà soát trước khi chốt.",
};

function ProfileFieldInput({ facts, field, disabled }: { facts: Record<string, unknown>; field: ProfileField; disabled?: boolean }) {
  const value = field.computed ? computedCashFlowValue(field, facts) : formatProfileValue(field, facts[field.key]);
  const priority = field.importance === "required" ? "**" : field.importance === "major" ? "*" : "";
  const label = <span className="fieldLabelText">{field.label}{priority && <span className={`fieldPriority ${field.importance}`} title={field.importance === "required" ? "Bắt buộc" : "Điểm cộng lớn"}> {priority}</span>}{field.computed && <span className="computedBadge" title="Giá trị được tính tự động">Tự tính</span>}</span>;
  if (disabled) return <div className="readOnlyFact">{label}<strong>{value || "—"}</strong></div>;
  return (
    <label className={[field.type === "textarea" ? "wideField" : "", field.computed ? "computedField" : ""].filter(Boolean).join(" ") || undefined}>
      {label}
      {field.type === "textarea" ? (
        <textarea name={field.key} rows={field.rows ?? 3} defaultValue={value} placeholder={field.placeholder} />
      ) : field.type === "select" ? (
        <select name={field.key} defaultValue={value}>
          <option value="">Chọn</option>
          {field.options?.map((option) => <option key={option}>{option}</option>)}
        </select>
      ) : (
        <input name={field.key} defaultValue={value} type={field.type === "date" ? "date" : "text"} placeholder={field.placeholder} readOnly={Boolean(field.computed)} aria-readonly={field.computed ? "true" : undefined} />
      )}
      {field.helper && <small className="fieldHelper">{field.helper}</small>}
    </label>
  );
}

function AnalysisPreview({ analysis }: { analysis: Analysis }) {
  if (analysis.module === "cash_flow") return <CashFlowAnalysis analysis={analysis} />;
  return (
    <div className="reportPreview">
      <p>{analysis.summary}</p>
      <div className="tagWrap">
        {(analysis.report.risks ?? []).slice(0, 4).map((item) => <span className="tag risk" key={item}>Rủi ro: {item}</span>)}
        {(analysis.report.missing_data ?? []).slice(0, 4).map((item) => <span className="tag warn" key={item}>Thiếu: {item}</span>)}
      </div>
    </div>
  );
}

export default function StartupDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { user } = useAuth();
  const isStartup = user?.role === "startup";
  const [startup, setStartup] = useState<Startup | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [completeness, setCompleteness] = useState<Completeness | null>(null);
  const [versions, setVersions] = useState<StartupVersion[]>([]);
  const [access, setAccess] = useState<InvestorAccess[]>([]);
  const [versionDiff, setVersionDiff] = useState<VersionDiff | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [tab, setTab] = useState("overview");
  const coreProfileComplete = Boolean(
    startup?.name.trim() && startup.industry && startup.stage && startup.primary_location,
  );

  const load = useCallback(async () => {
    if (!user) return;
    const common = [api.getStartup(id), api.listDocuments(id), api.listVersions(id)] as const;
    try {
      if (isStartup) {
        const [profile, docs, history, check, grants, draftAnalyses] = await Promise.all([
          ...common,
          api.completeness(id),
          api.listAccess(id),
          api.listAnalyses(id),
        ]);
        setStartup(profile); setDocuments(docs); setVersions(history); setCompleteness(check);
        setAccess(grants); setAnalyses(draftAnalyses);
        if (history.length >= 2) setVersionDiff(await api.compareVersions(id, history[1].version_number, history[0].version_number));
      } else {
        const [profile, docs, history, results] = await Promise.all([...common, api.listAnalyses(id)]);
        setStartup(profile); setDocuments(docs); setVersions(history); setAnalyses(results);
        if (history.length >= 2) setVersionDiff(await api.compareVersions(id, history[1].version_number, history[0].version_number));
      }
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không thể tải hồ sơ");
    }
  }, [id, isStartup, user]);

  useEffect(() => {
    const task = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(task);
  }, [load]);

  // Đồng bộ tab với URL hash (#tab-...) để sidebar điều hướng được.
  useEffect(() => {
    function applyHash() {
      const raw = window.location.hash.replace("#tab-", "");
      if (raw && isValidTab(raw, user?.role)) {
        if (startup && !coreProfileComplete && raw !== "overview" && raw !== "profile") {
          setTab("profile");
          window.history.replaceState(null, "", "#tab-profile");
          return;
        }
        setTab(raw);
        document.querySelector(".deskContext")?.scrollIntoView({ behavior: "smooth", block: "start" });
      } else if (raw) {
        setTab("overview");
        window.history.replaceState(null, "", "#tab-overview");
      }
    }
    applyHash();
    window.addEventListener("hashchange", applyHash);
    return () => window.removeEventListener("hashchange", applyHash);
  }, [coreProfileComplete, startup, user?.role]);

  const analysisMap = useMemo(() => latestByModule(analyses), [analyses]);

  function goTab(next: string) {
    if (!coreProfileComplete && next !== "overview" && next !== "profile") {
      setTab("profile");
      setError("Hãy nhập đủ tên, lĩnh vực, giai đoạn và địa chỉ trụ sở chính trước khi mở các tính năng khác.");
      if (typeof window !== "undefined") window.history.replaceState(null, "", "#tab-profile");
      return;
    }
    setTab(next);
    if (typeof window !== "undefined") window.history.replaceState(null, "", `#tab-${next}`);
  }

  function mergeAnalysis(result: Analysis) {
    setAnalyses((current) => [result, ...current.filter((item) => item.module !== result.module)]);
  }

  async function saveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!startup || !isStartup) return;
    const form = new FormData(event.currentTarget);
    const facts: Record<string, unknown> = { ...startup.facts };
    for (const key of ["variable_cost_per_order", "alternatives", "expansion_plan", "headquarters_address", "facility_address"]) delete facts[key];
    for (const section of profileSections) for (const field of section.fields) {
      const value = readProfileField(form, field);
      if (value !== undefined) facts[field.key] = value; else delete facts[field.key];
    }
    setBusy("profile");
    try {
      const updated = await api.updateStartup(id, {
        name: textValue(form, "name"), industry: textValue(form, "industry") || null,
        stage: textValue(form, "stage") || null, primary_location: textValue(form, "location") || null, facts,
      });
      setStartup(updated);
      window.dispatchEvent(new Event("startup-workspace-updated"));
      setCompleteness(await api.completeness(id));
    } catch (err) { setError(err instanceof Error ? err.message : "Không thể lưu hồ sơ"); }
    finally { setBusy(null); }
  }

  async function saveCashFlowProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!startup || !isStartup || !editable) return;
    const form = new FormData(event.currentTarget);
    const facts: Record<string, unknown> = { ...startup.facts };
    for (const key of ["fixed_costs", "average_price", "opening_cash", "reported_ending_cash"]) delete facts[key];
    for (const section of cashFlowProfileSections) for (const field of section.fields) {
      const value = readProfileField(form, field);
      if (value !== undefined) facts[field.key] = value; else delete facts[field.key];
    }
    setBusy("cashflow-profile");
    try {
      const updated = await api.updateStartup(id, { facts });
      setStartup(updated);
      setCompleteness(await api.completeness(id));
    } catch (err) { setError(err instanceof Error ? err.message : "Không thể lưu dữ liệu dòng tiền"); }
    finally { setBusy(null); }
  }

  async function saveDevelopmentPlan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!startup || !isStartup || !editable) return;
    const form = new FormData(event.currentTarget);
    const facts: Record<string, unknown> = { ...startup.facts };
    for (const section of developmentPlanSections) for (const field of section.fields) {
      const value = readProfileField(form, field);
      if (value !== undefined) facts[field.key] = value; else delete facts[field.key];
    }
    setBusy("development-plan");
    try {
      const updated = await api.updateStartup(id, { facts });
      setStartup(updated);
      setCompleteness(await api.completeness(id));
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Không thể lưu kế hoạch phát triển."); }
    finally { setBusy(null); }
  }

  async function upload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const input = form.elements.namedItem("document") as HTMLInputElement;
    if (!input.files?.[0]) return;
    const file = input.files[0];
    setBusy("upload");
    try {
      const item = await api.uploadDocument(id, file);
      setDocuments((current) => [item, ...current]);
      setCompleteness(await api.completeness(id));
      form.reset();
    } catch (err) { setError(err instanceof Error ? err.message : "Tải tài liệu thất bại"); }
    finally { setBusy(null); }
  }

  async function applyEvidenceUpdate(updated: Startup) {
    setStartup(updated);
    setCompleteness(await api.completeness(id));
  }

  async function submitProfile() {
    setBusy("submit");
    try { await api.submitStartup(id); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : "Không thể nộp hồ sơ"); }
    finally { setBusy(null); }
  }

  async function createDraft() {
    setBusy("draft");
    try { setStartup(await api.createNextDraft(id)); setCompleteness(await api.completeness(id)); }
    catch (err) { setError(err instanceof Error ? err.message : "Không thể tạo bản nháp"); }
    finally { setBusy(null); }
  }

  async function analyze(module: AnalysisModule) {
    if (module === "surrounding_area") { goTab("area"); return; }
    setBusy(module);
    try {
      const result = await api.runAnalysis(id, module);
      setAnalyses((current) => [result, ...current]);
    } catch (err) { setError(err instanceof Error ? err.message : "Phân tích thất bại"); }
    finally { setBusy(null); }
  }

  async function changeVisibility(documentId: string, visibility: string) {
    try {
      const updated = await api.updateDocumentVisibility(id, documentId, visibility);
      setDocuments((current) => current.map((item) => item.id === documentId ? updated : item));
    } catch (err) { setError(err instanceof Error ? err.message : "Không thể cập nhật quyền tài liệu"); }
  }

  async function revoke(investorId: string) {
    try { await api.revokeAccess(id, investorId); setAccess(await api.listAccess(id)); }
    catch (err) { setError(err instanceof Error ? err.message : "Không thể thu hồi quyền"); }
  }

  async function toggleDiscovery(discoverable: boolean) {
    setBusy("discovery");
    try { setStartup(await api.updateDiscovery(id, discoverable)); }
    catch (err) { setError(err instanceof Error ? err.message : "Không thể cập nhật discovery"); }
    finally { setBusy(null); }
  }

  async function decideAccess(investorId: string, decision: "approve" | "reject") {
    setBusy(`${decision}-${investorId}`);
    try {
      if (decision === "approve") await api.approveAccess(id, investorId);
      else await api.rejectAccess(id, investorId);
      setAccess(await api.listAccess(id));
    } catch (err) { setError(err instanceof Error ? err.message : "Không thể xử lý yêu cầu"); }
    finally { setBusy(null); }
  }

  if (!startup) {
    return (
      <div className="hdShell">
        {error ? <div className="hdAlert"><MIcon name="error" /><span>{error}</span></div> : <p className="muted">Đang tải hồ sơ...</p>}
      </div>
    );
  }

  const editable = isStartup && startup.status === "draft";
  const facts = startup.facts ?? {};
  const tabs = tabsForRole(user?.role);
  const activeTab = isValidTab(tab, user?.role) ? tab : "overview";

  const moduleScores = modules.map((m) => analysisMap[m.id]?.score).filter((s): s is number => s != null);
  const investorScore = moduleScores.length ? Math.round(moduleScores.reduce((a, b) => a + b, 0) / moduleScores.length) : null;
  const completenessPct = completeness && completeness.total_fields
    ? Math.round((completeness.completed_fields / completeness.total_fields) * 100)
    : null;
  const scoreVal = isStartup ? completenessPct : investorScore;
  const analyzedCount = modules.filter((m) => analysisMap[m.id]).length;
  const tags = [startup.industry, startup.stage, startup.primary_location].filter(Boolean) as string[];

  const metrics = isStartup
    ? [
        { label: "Độ đầy đủ", value: completenessPct != null ? `${completenessPct}%` : "—", icon: "fact_check", hint: `${completeness?.completed_fields ?? 0}/${completeness?.total_fields ?? 0} trường` },
        { label: "Tài liệu", value: String(documents.length), icon: "description", hint: "Đã tải lên" },
        { label: "Phiên bản", value: `V${startup.current_version}`, icon: "history", hint: startup.status === "draft" ? "Bản nháp" : "Đã khóa" },
        { label: "Trạng thái", value: startup.status === "draft" ? "Nháp" : "Đã nộp", icon: "flag", hint: startup.status !== "draft" ? "Phiên bản đã khóa" : completeness?.can_submit ? "Đủ điều kiện nộp" : "Cần bổ sung" },
      ]
    : [
        { label: "Điểm trung bình", value: investorScore != null ? String(investorScore) : "—", icon: "target", hint: "Trung bình các module" },
        { label: "Module đã chạy", value: `${analyzedCount}/3`, icon: "analytics", hint: "Business · Cash · Area" },
        { label: "Tài liệu", value: String(documents.length), icon: "description", hint: "Được chia sẻ" },
        { label: "Phiên bản", value: `V${startup.current_version}`, icon: "history", hint: startup.status },
      ];

  const missingItems = completeness
    ? [...completeness.missing_fields, ...completeness.missing_documents, ...completeness.format_errors]
    : [];

  const activeTabDef = tabs.find((t) => t.id === activeTab);

  function metricsFor(t: string) {
    switch (t) {
      case "business":
        return moduleMetrics(analysisMap.business_model, "Mô hình KD");
      case "development": {
        const fields = developmentPlanSections.flatMap((section) => section.fields);
        const filled = fields.filter((field) => formatProfileValue(field, facts[field.key]).trim()).length;
        const majorFields = fields.filter((field) => field.importance === "major");
        const majorFilled = majorFields.filter((field) => formatProfileValue(field, facts[field.key]).trim()).length;
        return [
          { label: "Đã điền", value: `${filled}/${fields.length}`, icon: "edit_note", hint: "trường kế hoạch" },
          { label: "Điểm cộng lớn", value: `${majorFilled}/${majorFields.length}`, icon: "star", hint: "trường có dấu *" },
          { label: "Còn thiếu", value: String(fields.length - filled), icon: "help", hint: "có thể bổ sung" },
          { label: "Trạng thái", value: filled === fields.length ? "Đầy đủ" : filled ? "Đang soạn" : "Chưa nhập", icon: "flag", hint: "bản nháp" },
        ];
      }
      case "cashflow":
        return moduleMetrics(analysisMap.cash_flow, "Dòng tiền");
      case "area": {
        if (!isStartup) return moduleMetrics(analysisMap.surrounding_area, "Khu vực");
        const areaClaims = facts.area_claims ?? facts.location_claims;
        const exactLocation = startup?.primary_location;
        return [
          { label: "Địa điểm", value: exactLocation ? "Có" : "Thiếu", icon: "location_on", hint: "địa chỉ phân tích" },
          { label: "Tuyên bố", value: String(countArr(areaClaims)), icon: "gavel", hint: "cần kiểm chứng" },
          { label: "Trạng thái", value: statusLabel(analysisMap.surrounding_area?.status), icon: "flag", hint: "kết quả draft" },
          { label: "Thiếu dữ liệu", value: String(countArr(analysisMap.surrounding_area?.report?.missing_data)), icon: "help", hint: "cần bổ sung" },
        ];
      }
      case "evidence":
        return [
          { label: "Tổng tài liệu", value: String(documents.length), icon: "description", hint: "đã tải" },
          { label: "Chia sẻ", value: String(documents.filter((d) => d.visibility === "shared").length), icon: "share", hint: "investor xem" },
          { label: "Riêng tư", value: String(documents.filter((d) => d.visibility === "private").length), icon: "lock", hint: "chỉ startup" },
          { label: "Hạn chế", value: String(documents.filter((d) => d.visibility === "restricted").length), icon: "visibility_off", hint: "giới hạn" },
        ];
      case "review":
        return [
          { label: "Phiên bản", value: String(versions.length), icon: "history", hint: "đã khóa" },
          { label: "Đã cấp Data Room", value: String(access.filter((a) => a.status === "active").length), icon: "lock_open", hint: "nhà đầu tư" },
          { label: "Rủi ro (tổng)", value: String(modules.reduce((n, m) => n + countArr(analysisMap[m.id]?.report?.risks), 0)), icon: "warning", hint: "các module" },
          { label: "Thiếu (tổng)", value: String(modules.reduce((n, m) => n + countArr(analysisMap[m.id]?.report?.missing_data), 0)), icon: "help", hint: "các module" },
        ];
      default:
        return metrics;
    }
  }
  const sectionMetrics = metricsFor(activeTab);

  return (
    <div className="hdShell">
      <div className="desk">
        {error && <div className="hdAlert" role="alert"><MIcon name="error" /><span>{error}</span></div>}

        {/* Hero */}
        {activeTab === "overview" && <section className="hdCard deskHero">
          <div className="deskId">
            <div className="deskAvatar">{startup.name.slice(0, 2).toUpperCase()}</div>
            <div className="deskIdText">
              <p className="hdEyebrow">{isStartup ? "Hồ sơ startup" : "Bàn thẩm định"}</p>
              <h1>{startup.name}</h1>
              <div className="deskTags">
                {tags.length ? tags.map((t) => <span className="hdChip" key={t}>{t}</span>) : <span className="hdChip">Chưa đủ thông tin</span>}
              </div>
              <p className="deskLead">
                {isStartup
                  ? "Chuẩn bị dữ liệu, kiểm tra độ đầy đủ và nộp phiên bản hồ sơ cho nhà đầu tư."
                  : (analysisMap.business_model?.summary || "Thẩm định có dẫn chứng: chạy từng module, kiểm chứng tuyên bố và chốt câu hỏi trước buổi rà soát.")}
              </p>
            </div>
          </div>
          <div className="deskScore">
            <div className="scoreRing" style={{ "--val": scoreVal ?? 0 } as React.CSSProperties}>
              <strong>{scoreVal != null ? scoreVal : "—"}</strong>
              <span>{isStartup ? "Đầy đủ" : "Score"}</span>
            </div>
            <small>{isStartup ? "Độ đầy đủ dữ liệu, không phải điểm thành công" : "Trung bình độ đầy đủ của các module đã chạy"}</small>
          </div>
        </section>}

        {/* Tiêu đề mục đang xem + chỉ số liên quan; điều hướng chính nằm ở sidebar. */}
        <section className="deskContext" id="desk-context">
          <div className="deskContextHead">
            <div>
              <p className="hdEyebrow">Mục đang xem</p>
              <h2>
                <span className="deskContextIcon"><MIcon name={activeTabDef?.icon ?? "dashboard"} /></span>
                {activeTabDef?.label ?? "Tổng quan"}
              </h2>
              <p>{tabLeads[activeTab] ?? tabLeads.overview}</p>
            </div>
          </div>
          <div className="deskContextStats" aria-label="Chỉ số theo mục">
            {sectionMetrics.map((metric) => (
              <div className="deskContextStat" key={metric.label}>
                <MIcon name={metric.icon} />
                <span>
                  <small>{metric.label}</small>
                  <strong>{metric.value}</strong>
                  <em>{metric.hint}</em>
                </span>
              </div>
            ))}
          </div>
        </section>

        <div className="deskBody noRail">
          <main className="deskMain">
            {/* ---- Overview ---- */}
            <div className="deskPanel" hidden={activeTab !== "overview"}>
              {!isStartup && (
                <section className="deskModules" aria-label="Kết quả module">
                  {modules.map((module) => {
                    const result = analysisMap[module.id];
                    return (
                      <article className={`verdictCard2 ${module.tone}`} key={module.id}>
                        <div className="vrail" />
                        <div className="vbody">
                          <div className="vtop">
                            <h4><MIcon name={module.icon} />{module.name}</h4>
                            <span className="verdictScore">{result?.score == null ? "Chưa chạy" : `${Math.round(result.score)}/100`}</span>
                          </div>
                          <p>{result?.summary ? result.summary.slice(0, 130) : module.description}</p>
                          <div className="hdHeadActions">
                            {module.id === "surrounding_area" ? (
                              <button className="hdBtn" type="button" onClick={() => goTab("area")}><MIcon name="map" />Mở khu vực</button>
                            ) : (
                              <button className="hdBtn" type="button" disabled={busy === module.id} onClick={() => analyze(module.id)}>
                                <MIcon name="play_arrow" />{result ? "Chạy lại" : "Chạy phân tích"}
                              </button>
                            )}
                          </div>
                        </div>
                      </article>
                    );
                  })}
                </section>
              )}

              {isStartup && completeness && (
                <section className="hdCard">
                  <div className="hdSectionHead">
                    <h2><MIcon name="fact_check" />Kiểm tra độ đầy đủ</h2>
                    {editable
                      ? <button className="hdBtn primary" disabled={!completeness.can_submit || busy === "submit"} onClick={submitProfile}><MIcon name="lock" />Nộp và khóa phiên bản</button>
                      : <button className="hdBtn primary" disabled={busy === "draft"} onClick={createDraft}><MIcon name="edit_document" />Tạo phiên bản cập nhật</button>}
                  </div>
                  {missingItems.length > 0
                    ? <ul className="missingList">{missingItems.map((item) => <li key={item}>{item}</li>)}</ul>
                    : <p className="muted">Hồ sơ đã đủ các trường và tài liệu bắt buộc. Hệ thống không chấm điểm hoặc phân tích ở bước này.</p>}
                </section>
              )}
            </div>

            {/* ---- Business (investor) ---- */}
            {!isStartup && (
              <div className="deskPanel" hidden={activeTab !== "business"}>
                <section className="hdCard">
                  <div className="hdSectionHead">
                    <h2><MIcon name="storefront" />Mô hình kinh doanh</h2>
                    <button className="hdBtn" disabled={busy === "business_model"} onClick={() => analyze("business_model")}><MIcon name="play_arrow" />{analysisMap.business_model ? "Chạy lại" : "Chạy phân tích"}</button>
                  </div>
                  {analysisMap.business_model
                    ? <AnalysisPreview analysis={analysisMap.business_model} />
                    : <div className="deskEmpty"><strong>Chưa có phân tích</strong><span>Nhấn “Chạy phân tích” để hệ thống tổng hợp mô hình kinh doanh từ hồ sơ.</span></div>}
                </section>
                <section className="hdCard">
                  <div className="hdSectionHead"><h2><MIcon name="description" />Dữ liệu hồ sơ</h2><span className="hdCount">Chỉ đọc</span></div>
                  <div className="fieldPriorityLegend"><span><b>**</b> Bắt buộc</span><span><b>*</b> Điểm cộng lớn</span><span>Không dấu: điểm cộng</span></div>
                  {profileSections.map((section) => (
                    <div className="factSection" key={section.id}>
                      <div className="factSectionHeader"><div><p className="eyebrow">{section.eyebrow}</p><h3>{section.title}</h3></div></div>
                      <div className="factGrid">{section.fields.map((field) => <ProfileFieldInput facts={facts} field={field} disabled key={field.key} />)}</div>
                    </div>
                  ))}
                </section>
              </div>
            )}

            {/* ---- Profile (startup) ---- */}
            {isStartup && (
              <div className="deskPanel" hidden={activeTab !== "profile"}>
                <section className="hdCard">
                  <div className="hdSectionHead"><h2><MIcon name="description" />Dữ liệu hồ sơ</h2><span className="hdCount">{editable ? "Bản nháp có thể chỉnh sửa" : "Chỉ đọc"}</span></div>
                  <form className="stackForm" onSubmit={saveProfile} key={startup.updated_at}>
                    <div className="fieldPriorityLegend"><span><b>**</b> Bắt buộc</span><span><b>*</b> Điểm cộng lớn</span><span>Không dấu: điểm cộng</span></div>
                    <div className="formRow three">
                      <label><span className="fieldLabelText">Tên<span className="fieldPriority required"> **</span></span><input name="name" required defaultValue={startup.name} disabled={!editable} /></label>
                      <label><span className="fieldLabelText">Lĩnh vực<span className="fieldPriority required"> **</span></span><input name="industry" defaultValue={startup.industry ?? ""} disabled={!editable} /></label>
                      <label><span className="fieldLabelText">Giai đoạn<span className="fieldPriority required"> **</span></span><select name="stage" defaultValue={startup.stage ?? ""} disabled={!editable}><option value="">Chọn</option>{stageOptions.map((stage) => <option key={stage}>{stage}</option>)}</select></label>
                    </div>
                    <label><span className="fieldLabelText">Địa chỉ trụ sở chính<span className="fieldPriority required"> **</span></span><input name="location" defaultValue={startup.primary_location ?? ""} disabled={!editable} /></label>
                    {profileSections.map((section) => (
                      <div className="factSection" key={section.id}>
                        <div className="factSectionHeader"><div><p className="eyebrow">{section.eyebrow}</p><h3>{section.title}</h3></div></div>
                        <div className="factGrid">{section.fields.map((field) => <ProfileFieldInput facts={facts} field={field} disabled={!editable} key={field.key} />)}</div>
                      </div>
                    ))}
                    {editable && <button className="hdBtn primary" disabled={busy === "profile"}><MIcon name="save" />Lưu bản nháp</button>}
                  </form>
                </section>
              </div>
            )}

            {/* ---- Development Plan ---- */}
            <div className="deskPanel" hidden={activeTab !== "development"}>
              <section className="hdCard">
                <div className="hdSectionHead"><h2><MIcon name="route" />Kế hoạch phát triển</h2><span className="hdCount">{editable ? "Có thể chỉnh sửa" : "Chỉ đọc"}</span></div>
                <div className="fieldPriorityLegend"><span><b>**</b> Bắt buộc</span><span><b>*</b> Điểm cộng lớn</span><span>Không dấu: điểm cộng</span></div>
                {isStartup ? (
                  <form className="stackForm" onSubmit={saveDevelopmentPlan} key={`development-${startup.updated_at}`}>
                    {developmentPlanSections.map((section) => (
                      <div className="factSection" key={section.id}>
                        <div className="factSectionHeader"><div><p className="eyebrow">{section.eyebrow}</p><h3>{section.title}</h3></div><p>{section.description}</p></div>
                        <div className="factGrid">{section.fields.map((field) => <ProfileFieldInput facts={facts} field={field} disabled={!editable} key={field.key} />)}</div>
                      </div>
                    ))}
                    {editable && <button className="hdBtn primary" disabled={busy === "development-plan"}><MIcon name="save" />Lưu kế hoạch phát triển</button>}
                  </form>
                ) : developmentPlanSections.map((section) => (
                  <div className="factSection" key={section.id}>
                    <div className="factSectionHeader"><div><p className="eyebrow">{section.eyebrow}</p><h3>{section.title}</h3></div><p>{section.description}</p></div>
                    <div className="factGrid">{section.fields.map((field) => <ProfileFieldInput facts={facts} field={field} disabled key={field.key} />)}</div>
                  </div>
                ))}
              </section>
            </div>

            {/* ---- Cash Flow ---- */}
            <div className="deskPanel" hidden={activeTab !== "cashflow"}>
              {isStartup ? (
                <>
                  <section className="hdCard">
                    <div className="hdSectionHead">
                      <h2><MIcon name="edit_note" />Dữ liệu dòng tiền thủ công</h2>
                      <span className="hdCount">{editable ? "Có thể chỉnh sửa" : "Chỉ đọc"}</span>
                    </div>
                    <form className="stackForm" onSubmit={saveCashFlowProfile} onInput={(event) => recalculateCashFlowForm(event.currentTarget)} key={`cash-${startup.updated_at}`}>
                      <div className="fieldPriorityLegend"><span><b>**</b> Bắt buộc</span><span><b>*</b> Điểm cộng lớn</span><span>Không dấu: điểm cộng</span></div>
                      {cashFlowProfileSections.map((section) => (
                        <div className="factSection" key={section.id}>
                          <div className="factSectionHeader"><div><p className="eyebrow">{section.eyebrow}</p><h3>{section.title}</h3></div><p>{section.description}</p></div>
                          <div className="factGrid">{section.fields.map((field) => <ProfileFieldInput facts={facts} field={field} disabled={!editable} key={field.key} />)}</div>
                        </div>
                      ))}
                      {editable && <button className="hdBtn primary" disabled={busy === "cashflow-profile"}><MIcon name="save" />Lưu dữ liệu dòng tiền</button>}
                    </form>
                  </section>
                  {analysisMap.cash_flow && <CashFlowAnalysis analysis={analysisMap.cash_flow} />}
                </>
              ) : (
                <>
                  <section className="hdCard">
                    <div className="hdSectionHead">
                      <h2><MIcon name="monitoring" />Phân tích dòng tiền</h2>
                      <button className="hdBtn" disabled={busy === "cash_flow"} onClick={() => analyze("cash_flow")}><MIcon name="play_arrow" />{analysisMap.cash_flow ? "Chạy lại" : "Chạy phân tích"}</button>
                    </div>
                    {analysisMap.cash_flow
                      ? <CashFlowAnalysis analysis={analysisMap.cash_flow} />
                      : <div className="deskEmpty"><strong>Chưa có phân tích dòng tiền</strong><span>Chạy phân tích để xem burn rate, runway và kịch bản căng thẳng.</span></div>}
                  </section>
                  <section className="hdCard">
                    <div className="hdSectionHead"><h2><MIcon name="description" />Dữ liệu dòng tiền</h2><span className="hdCount">Chỉ đọc</span></div>
                    <div className="fieldPriorityLegend"><span><b>**</b> Bắt buộc</span><span><b>*</b> Điểm cộng lớn</span><span>Không dấu: điểm cộng</span></div>
                    {cashFlowProfileSections.map((section) => (
                      <div className="factSection" key={section.id}>
                        <div className="factSectionHeader"><div><p className="eyebrow">{section.eyebrow}</p><h3>{section.title}</h3></div></div>
                        <div className="factGrid">{section.fields.map((field) => <ProfileFieldInput facts={facts} field={field} disabled key={field.key} />)}</div>
                      </div>
                    ))}
                  </section>
                </>
              )}
            </div>

            {/* ---- Area ---- */}
            <div className="deskPanel comingSoonMaskHost" hidden={activeTab !== "area"}>
              <SurroundingArea
                startupId={id}
                industry={startup.industry}
                initialAddress={startup.primary_location ?? ""}
                facts={facts}
                initialAnalysis={analysisMap.surrounding_area}
                compactHeader
                onAnalysisComplete={(result) => setAnalyses((current) => [result, ...current])}
                onStartupUpdated={isStartup ? (updated) => {
                    setStartup(updated);
                    window.dispatchEvent(new Event("startup-workspace-updated"));
                    void api.completeness(id).then(setCompleteness);
                  } : undefined}
              />
              <div className="comingSoonMask" role="status" aria-label="Comming Soon">
                <div className="comingSoonMaskCard">
                  <MIcon name="construction" />
                  <strong>Comming Soon</strong>
                  <span>Tính năng Khu vực đang được hoàn thiện.</span>
                </div>
              </div>
            </div>

            {/* ---- Evidence / Documents ---- */}
            <div className="deskPanel" hidden={activeTab !== "evidence"}>
              <section className="hdCard" id="startup-documents">
                <div className="hdSectionHead"><h2><MIcon name="inventory_2" />{isStartup ? "Tài liệu hồ sơ" : "Tài liệu được chia sẻ"}</h2><span className="hdCount">{documents.length} tài liệu</span></div>
                {editable && <form className="uploadBox" onSubmit={upload}><input name="document" type="file" accept=".pdf,.docx,.pptx,.xlsx,.txt,.md,.csv,.json,.png,.jpg,.jpeg" required /><button className="hdBtn primary" disabled={busy === "upload"}><MIcon name="upload" />Tải lên</button></form>}
                {isStartup && <div className="documentChecklist">{documentChecklist.map((group) => <details className="checklistGroup" key={group.title}><summary>{group.title}</summary><div className="checklistItems">{group.items.map((item) => <span key={item}>{item}</span>)}</div></details>)}</div>}
                <div className="documentList">{documents.map((item) => <div className="documentRow" key={item.id}><span className="fileIcon">DOC</span><div><strong>{item.filename}</strong><span>{item.status} · {item.visibility}</span></div>{editable && <select value={item.visibility} onChange={(event) => void changeVisibility(item.id, event.target.value)}><option value="shared">Chia sẻ</option><option value="private">Riêng tư</option><option value="restricted">Hạn chế</option></select>}</div>)}
                  {!documents.length && <div className="deskEmpty"><strong>Chưa có tài liệu</strong><span>{editable ? "Tải lên hợp đồng, sổ thu chi, bảng giá… để làm bằng chứng." : "Chưa có tài liệu nào được chia sẻ."}</span></div>}
                </div>
                {isStartup && editable && (
                  <div className="evidenceAutofillStack">
                    <ExtractionReview startup={startup} documents={documents} onStartupUpdated={applyEvidenceUpdate} />
                    <CashFlowDataWorkspace
                      startup={startup}
                      documents={documents}
                      analysis={analysisMap.cash_flow}
                      onAnalysisComplete={(analysis) => setAnalyses((current) => [analysis, ...current.filter((item) => item.id !== analysis.id)])}
                      onStartupUpdated={applyEvidenceUpdate}
                    />
                  </div>
                )}
              </section>
            </div>

            {/* ---- Review ---- */}
            <div className="deskPanel" hidden={activeTab !== "review"}>
              {isStartup && (
                <section className="hdCard accessPanel">
                  <div className="hdSectionHead"><h2><MIcon name="folder_shared" />Quyền truy cập Data Room</h2><span className="hdCount">{access.filter((item) => item.status === "pending").length} yêu cầu chờ duyệt</span></div>
                  <div className="discoverySetting">
                    <div><strong>Cho phép nhà đầu tư tìm thấy hồ sơ công khai</strong><small>Không cần phê duyệt để investor xem candidate card, shortlist hoặc so sánh. Tài liệu và dữ liệu chi tiết vẫn được khóa.</small></div>
                    <label className="toggle"><input type="checkbox" checked={startup.discoverable} disabled={startup.current_version < 1 || busy === "discovery"} onChange={(event) => void toggleDiscovery(event.target.checked)} /><span /></label>
                  </div>
                  <p className="dataRoomNotice"><MIcon name="shield_lock" />Startup chỉ phê duyệt khi investor yêu cầu mở Data Room. Quyền này bao gồm tài liệu shared, phân tích và document chat.</p>
                  <div className="accessList">{access.map((item) => <div className="accessRow" key={item.investor_id}><span><strong>{item.investor_name}</strong><small>{item.investor_email}</small>{item.request_reason && <small className="requestReason">Lý do mở Data Room: {item.request_reason}</small>}</span><div className="headerActions"><span className={`status accessStatus-${item.status}`}>{item.status === "pending" ? "Chờ phê duyệt" : item.status === "active" ? "Đã cấp Data Room" : item.status === "rejected" ? "Đã từ chối" : "Đã thu hồi"}</span>{item.status === "pending" && <><button className="hdBtn primary compactButton" onClick={() => void decideAccess(item.investor_id, "approve")} type="button">Cấp quyền Data Room</button><button className="hdBtn compactButton" onClick={() => void decideAccess(item.investor_id, "reject")} type="button">Từ chối</button></>}{item.status === "active" && <button className="hdBtn compactButton" onClick={() => void revoke(item.investor_id)} type="button">Thu hồi Data Room</button>}</div></div>)}
                    {!access.length && <p className="muted">Chưa có nhà đầu tư nào yêu cầu mở Data Room.</p>}
                  </div>
                </section>
              )}
              <section className="hdCard versionPanel">
                <div className="hdSectionHead"><h2><MIcon name="history" />Lịch sử phiên bản</h2></div>
                <div className="versionList">{versions.map((item) => <div className="versionRow" key={item.id}><strong>Phiên bản V{item.version_number}</strong><span>{new Date(item.submitted_at).toLocaleString("vi-VN")} · {item.status}</span></div>)}{!versions.length && <p className="muted">Chưa có phiên bản nào được nộp.</p>}</div>
                {versionDiff && <div className="versionDiff"><h3>Thay đổi V{versionDiff.from_version} → V{versionDiff.to_version}</h3>{versionDiff.changes.map((change) => <div className="diffRow" key={change.field}><strong>{change.field}</strong><span>{JSON.stringify(change.before) ?? "—"}</span><span>→</span><span>{JSON.stringify(change.after) ?? "—"}</span></div>)}</div>}
              </section>
            </div>
          </main>

        </div>
      </div>

      <ChatWidget startupId={id} />
    </div>
  );
}
