"use client";

import Link from "next/link";
import { FormEvent, use, useCallback, useEffect, useMemo, useState } from "react";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import {
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
  User,
  VersionDiff,
} from "@/types";

import CashFlowAnalysis from "./CashFlowAnalysis";
import ChatWidget from "./ChatWidget";
import SurroundingArea from "./SurroundingArea";

const modules: Array<{ id: AnalysisModule; name: string; code: string; description: string }> = [
  { id: "business_model", name: "Mô hình kinh doanh", code: "BM", description: "Khách hàng, doanh thu và khả năng mở rộng" },
  { id: "cash_flow", name: "Dòng tiền", code: "CF", description: "Burn rate, runway và stress scenario" },
  { id: "surrounding_area", name: "Khu vực xung quanh", code: "SA", description: "POI, đối thủ và kiểm chứng địa điểm" },
];

function latestByModule(analyses: Analysis[]) {
  return modules.reduce<Record<AnalysisModule, Analysis | undefined>>((result, module) => {
    result[module.id] = analyses.find((analysis) => analysis.module === module.id);
    return result;
  }, { business_model: undefined, cash_flow: undefined, surrounding_area: undefined });
}

function ProfileFieldInput({ facts, field, disabled }: { facts: Record<string, unknown>; field: ProfileField; disabled?: boolean }) {
  const value = formatProfileValue(field, facts[field.key]);
  if (disabled) return <div className="readOnlyFact"><span>{field.label}</span><strong>{value || "—"}</strong></div>;
  return (
    <label className={field.type === "textarea" ? "wideField" : undefined}>
      {field.label}
      {field.type === "textarea" ? (
        <textarea name={field.key} rows={field.rows ?? 3} defaultValue={value} placeholder={field.placeholder} />
      ) : field.type === "select" ? (
        <select name={field.key} defaultValue={value}>
          <option value="">Chọn</option>
          {field.options?.map((option) => <option key={option}>{option}</option>)}
        </select>
      ) : (
        <input name={field.key} defaultValue={value} type={field.type === "date" ? "date" : "text"} placeholder={field.placeholder} />
      )}
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
  const [investors, setInvestors] = useState<User[]>([]);
  const [access, setAccess] = useState<InvestorAccess[]>([]);
  const [versionDiff, setVersionDiff] = useState<VersionDiff | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!user) return;
    const common = [api.getStartup(id), api.listDocuments(id), api.listVersions(id)] as const;
    try {
      if (isStartup) {
        const [profile, docs, history, check, investorUsers, grants] = await Promise.all([
          ...common,
          api.completeness(id),
          api.listInvestors(),
          api.listAccess(id),
        ]);
        setStartup(profile); setDocuments(docs); setVersions(history); setCompleteness(check);
        setInvestors(investorUsers); setAccess(grants);
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
  const analysisMap = useMemo(() => latestByModule(analyses), [analyses]);

  async function saveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!startup || !isStartup) return;
    const form = new FormData(event.currentTarget);
    const facts: Record<string, unknown> = { ...startup.facts };
    for (const section of profileSections) for (const field of section.fields) {
      const value = readProfileField(form, field);
      if (value !== undefined) facts[field.key] = value; else delete facts[field.key];
    }
    setBusy("profile");
    try {
      setStartup(await api.updateStartup(id, {
        name: textValue(form, "name"), industry: textValue(form, "industry") || null,
        stage: textValue(form, "stage") || null, primary_location: textValue(form, "location") || null, facts,
      }));
      setCompleteness(await api.completeness(id));
    } catch (err) { setError(err instanceof Error ? err.message : "Không thể lưu hồ sơ"); }
    finally { setBusy(null); }
  }

  async function upload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const input = event.currentTarget.elements.namedItem("document") as HTMLInputElement;
    if (!input.files?.[0]) return;
    setBusy("upload");
    try {
      const item = await api.uploadDocument(id, input.files[0]);
      setDocuments((current) => [item, ...current]);
      setCompleteness(await api.completeness(id));
      event.currentTarget.reset();
    } catch (err) { setError(err instanceof Error ? err.message : "Tải tài liệu thất bại"); }
    finally { setBusy(null); }
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
    if (module === "surrounding_area") {
      document.getElementById("surrounding-area")?.scrollIntoView({ behavior: "smooth" }); return;
    }
    setBusy(module);
    try {
      const result = await api.runAnalysis(id, module);
      setAnalyses((current) => [result, ...current]);
    } catch (err) { setError(err instanceof Error ? err.message : "Phân tích thất bại"); }
    finally { setBusy(null); }
  }

  async function grant(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const investorId = String(new FormData(event.currentTarget).get("investor_id") ?? "");
    if (!investorId) return;
    setBusy("grant");
    try { await api.grantAccess(id, investorId); setAccess(await api.listAccess(id)); }
    catch (err) { setError(err instanceof Error ? err.message : "Không thể cấp quyền"); }
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

  if (!startup) return <div className="pageShell">{error ? <div className="alert">{error}</div> : <p className="muted">Đang tải hồ sơ...</p>}</div>;
  const editable = isStartup && startup.status === "draft";
  const facts = startup.facts ?? {};

  return (
    <div className="pageShell">
      <Link href="/" className="backLink">← Danh sách hồ sơ</Link>
      <section className="detailHeader">
        <div className="avatar large">{startup.name.slice(0, 2).toUpperCase()}</div>
        <div><p className="eyebrow">{isStartup ? "HỒ SƠ STARTUP" : "HỒ SƠ THẨM ĐỊNH"}</p><h1>{startup.name}</h1>
          <p className="muted">{[startup.industry, startup.stage, startup.primary_location].filter(Boolean).join(" · ") || "Chưa đủ thông tin"}</p></div>
      </section>

      {error && <div className="alert">{error}</div>}

      <section className="detailInsightGrid">
        <div className="insightTile primary"><span>Vai trò</span><strong>{isStartup ? "Startup" : "Nhà đầu tư"}</strong><small>{isStartup ? "Chuẩn bị và nộp dữ liệu" : "Phân tích và đánh giá"}</small></div>
        <div className="insightTile"><span>Phiên bản khóa</span><strong>V{startup.current_version}</strong><small>{startup.status}</small></div>
        <div className="insightTile"><span>Tài liệu</span><strong>{documents.length}</strong><small>{isStartup ? "Tài liệu của hồ sơ" : "Được phép chia sẻ"}</small></div>
        <div className="insightTile action"><span>{isStartup ? "Độ đầy đủ" : "Kết quả phân tích"}</span>
          <strong>{isStartup ? `${completeness?.completed_fields ?? 0}/${completeness?.total_fields ?? 0}` : `${modules.filter((m) => analysisMap[m.id]).length}/3`}</strong>
          <small>{isStartup ? (completeness?.complete ? "Đủ điều kiện nộp" : "Cần bổ sung") : "Chỉ Nhà đầu tư được xem"}</small></div>
      </section>

      {isStartup && completeness && (
        <section className="surface completenessPanel">
          <div className="sectionHeader"><div><p className="eyebrow">COMPLETENESS</p><h2>Kiểm tra độ đầy đủ hồ sơ</h2></div>
            {editable ? <button className="primaryButton" disabled={!completeness.can_submit || busy === "submit"} onClick={submitProfile}>Nộp và khóa phiên bản</button>
              : <button className="primaryButton" disabled={busy === "draft"} onClick={createDraft}>Tạo phiên bản cập nhật</button>}</div>
          {[...completeness.missing_fields, ...completeness.missing_documents, ...completeness.format_errors].length > 0 ? (
            <ul className="missingList">{[...completeness.missing_fields, ...completeness.missing_documents, ...completeness.format_errors].map((item) => <li key={item}>{item}</li>)}</ul>
          ) : <p>Hồ sơ đã đủ các trường và tài liệu bắt buộc. Hệ thống không chấm điểm hoặc phân tích ở bước này.</p>}
        </section>
      )}

      {!isStartup && (
        <section className="surface" id="analysis-modules">
          <div className="sectionHeader"><div><p className="eyebrow">INVESTOR ONLY</p><h2>Phân tích và đánh giá hồ sơ</h2></div><span className="roleBadge">NHÀ ĐẦU TƯ</span></div>
          <div className="moduleList">{modules.map((module) => {
            const result = analysisMap[module.id];
            return <article className="moduleRow" key={module.id}><div className="moduleCode">{module.code}</div><div className="moduleBody"><h3>{module.name}</h3><p>{module.description}</p>{result && <AnalysisPreview analysis={result} />}</div>
              <div className="moduleAction"><strong>{result?.score == null ? "—" : Math.round(result.score)}</strong><span>/100</span><button className="secondaryButton" disabled={busy === module.id} onClick={() => analyze(module.id)}>{result ? "Chạy lại" : "Chạy phân tích"}</button></div></article>;
          })}</div>
        </section>
      )}

      <section className="surface" id="profile-facts">
        <div className="sectionHeader"><div><p className="eyebrow">PROFILE</p><h2>Dữ liệu hồ sơ</h2></div><span className="muted">{editable ? "Bản nháp có thể chỉnh sửa" : "Chỉ đọc"}</span></div>
        <form className="stackForm" onSubmit={saveProfile} key={startup.updated_at}>
          <div className="formRow three">
            <label>Tên<input name="name" required defaultValue={startup.name} disabled={!editable} /></label>
            <label>Lĩnh vực<input name="industry" defaultValue={startup.industry ?? ""} disabled={!editable} /></label>
            <label>Giai đoạn<select name="stage" defaultValue={startup.stage ?? ""} disabled={!editable}><option value="">Chọn</option>{stageOptions.map((stage) => <option key={stage}>{stage}</option>)}</select></label>
          </div>
          <label>Địa điểm chính<input name="location" defaultValue={startup.primary_location ?? ""} disabled={!editable} /></label>
          {profileSections.map((section) => <div className="factSection" key={section.id}><div className="factSectionHeader"><div><p className="eyebrow">{section.eyebrow}</p><h3>{section.title}</h3></div></div>
            <div className="factGrid">{section.fields.map((field) => <ProfileFieldInput facts={facts} field={field} disabled={!editable} key={field.key} />)}</div></div>)}
          {editable && <button className="primaryButton" disabled={busy === "profile"}>Lưu bản nháp</button>}
        </form>
      </section>

      {!isStartup && <SurroundingArea startupId={id} industry={startup.industry} initialAddress={startup.primary_location ?? ""} facts={facts} initialAnalysis={analysisMap.surrounding_area} onAnalysisComplete={(result) => setAnalyses((current) => [result, ...current])} />}

      <section className="surface" id="startup-documents">
        <div className="sectionHeader"><div><p className="eyebrow">DOCUMENTS</p><h2>{isStartup ? "Tài liệu hồ sơ" : "Tài liệu được chia sẻ"}</h2></div><span>{documents.length} tài liệu</span></div>
        {editable && <form className="uploadBox" onSubmit={upload}><input name="document" type="file" accept=".pdf,.docx,.pptx,.xlsx,.txt,.md,.csv" required /><button className="primaryButton" disabled={busy === "upload"}>Tải lên</button></form>}
        {isStartup && <div className="documentChecklist">{documentChecklist.map((group) => <details className="checklistGroup" key={group.title}><summary>{group.title}</summary><div className="checklistItems">{group.items.map((item) => <span key={item}>{item}</span>)}</div></details>)}</div>}
        <div className="documentList">{documents.map((item) => <div className="documentRow" key={item.id}><span className="fileIcon">DOC</span><div><strong>{item.filename}</strong><span>{item.status} · {item.visibility}</span></div>{editable && <select value={item.visibility} onChange={(event) => void changeVisibility(item.id, event.target.value)}><option value="shared">Chia sẻ</option><option value="private">Riêng tư</option><option value="restricted">Hạn chế</option></select>}</div>)}</div>
      </section>

      {isStartup && (
        <section className="surface accessPanel"><div className="sectionHeader"><div><p className="eyebrow">ACCESS</p><h2>Chia sẻ với Nhà đầu tư</h2></div></div>
          <form className="inlineForm" onSubmit={grant}><select name="investor_id" required><option value="">Chọn Nhà đầu tư</option>{investors.map((item) => <option value={item.id} key={item.id}>{item.full_name} · {item.email}</option>)}</select><button className="primaryButton" disabled={busy === "grant"}>Cấp quyền</button></form>
          <div className="accessList">{access.map((item) => <div className="accessRow" key={item.investor_id}><span><strong>{item.investor_name}</strong><small>{item.investor_email}</small></span><div className="headerActions"><span className="status">{item.status}</span>{item.status === "active" && <button className="secondaryButton compactButton" onClick={() => void revoke(item.investor_id)} type="button">Thu hồi</button>}</div></div>)}</div>
        </section>
      )}

      <section className="surface versionPanel"><div className="sectionHeader"><div><p className="eyebrow">VERSION HISTORY</p><h2>Lịch sử phiên bản đã khóa</h2></div></div>
        <div className="versionList">{versions.map((item) => <div className="versionRow" key={item.id}><strong>Phiên bản V{item.version_number}</strong><span>{new Date(item.submitted_at).toLocaleString("vi-VN")} · {item.status}</span></div>)}{!versions.length && <p className="muted">Chưa có phiên bản nào được nộp.</p>}</div>
        {versionDiff && <div className="versionDiff"><h3>Thay đổi V{versionDiff.from_version} → V{versionDiff.to_version}</h3>{versionDiff.changes.map((change) => <div className="diffRow" key={change.field}><strong>{change.field}</strong><span>{JSON.stringify(change.before) ?? "—"}</span><span>→</span><span>{JSON.stringify(change.after) ?? "—"}</span></div>)}</div>}
      </section>
      <ChatWidget startupId={id} />
    </div>
  );
}
