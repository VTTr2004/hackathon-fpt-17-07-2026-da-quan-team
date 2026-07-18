"use client";

import Link from "next/link";
import { FormEvent, use, useEffect, useMemo, useState } from "react";

import { api } from "@/lib/api";
import {
  documentChecklist,
  formatProfileValue,
  profileSections,
  readProfileField,
  stageOptions,
  textValue,
} from "@/lib/profileFields";
import type { ProfileField } from "@/lib/profileFields";
import type { Analysis, AnalysisModule, DocumentItem, Startup } from "@/types";

import ChatWidget from "./ChatWidget";
import SurroundingArea from "./SurroundingArea";
import CashFlowAnalysis from "./CashFlowAnalysis";

const modules: Array<{ id: AnalysisModule; name: string; code: string; description: string }> = [
  {
    id: "business_model",
    name: "Mô hình kinh doanh",
    code: "BM",
    description: "Vấn đề, khách hàng, doanh thu, thị trường và khả năng mở rộng",
  },
  {
    id: "cash_flow",
    name: "Dòng tiền",
    code: "CF",
    description: "Burn rate, runway, dòng tiền theo kỳ và stress scenario",
  },
  {
    id: "surrounding_area",
    name: "Khu vực xung quanh",
    code: "SA",
    description: "Xác nhận tọa độ, POI, đối thủ và verdict theo từng tuyên bố",
  },
];

const statusCopy: Record<string, string> = {
  completed: "Hoàn tất",
  partial: "Một phần",
  insufficient_data: "Thiếu dữ liệu",
  not_applicable: "Không áp dụng",
  failed: "Lỗi",
  idle: "Chưa chạy",
};

function scoreText(score: number | null | undefined) {
  return score === null || score === undefined ? "—" : String(Math.round(score));
}

function latestByModule(analyses: Analysis[]) {
  return modules.reduce<Record<AnalysisModule, Analysis | undefined>>(
    (acc, module) => {
      acc[module.id] = analyses.find((analysis) => analysis.module === module.id);
      return acc;
    },
    { business_model: undefined, cash_flow: undefined, surrounding_area: undefined },
  );
}

const profileReadinessFields = [
  "business_type",
  "problem",
  "solution",
  "target_customers",
  "core_products",
  "revenue_model",
  "current_cash",
  "monthly_revenue",
  "monthly_expense",
  "exact_location",
  "location_type",
  "target_customer_radius_m",
];

function hasValue(value: unknown) {
  if (Array.isArray(value)) return value.length > 0;
  return value !== null && value !== undefined && String(value).trim() !== "";
}

function profileReadiness(startup: Startup) {
  const facts = startup.facts ?? {};
  const values = [startup.name, startup.industry, startup.stage, startup.primary_location, ...profileReadinessFields.map((key) => facts[key])];
  const done = values.filter(hasValue).length;
  return Math.round((done / values.length) * 100);
}

function nextAction(startup: Startup, documents: DocumentItem[], analysisMap: Record<AnalysisModule, Analysis | undefined>) {
  if (!startup.primary_location && !hasValue(startup.facts?.exact_location)) return "Bổ sung địa điểm";
  if (!documents.length) return "Tải tài liệu nền";
  if (!analysisMap.business_model) return "Chạy Business Model";
  if (!analysisMap.cash_flow) return "Chạy Cash Flow";
  if (!analysisMap.surrounding_area) return "Quét khu vực";
  return "Rà soát rủi ro";
}

function ModuleReportPreview({ analysis }: { analysis: Analysis }) {
  const missing = analysis.report.missing_data ?? [];
  const risks = analysis.report.risks ?? [];
  const tools = analysis.report.tool_calls ?? [];
  const findings = analysis.report.findings ?? [];

  return (
    <div className="reportPreview">
      {analysis.summary && <p>{analysis.summary}</p>}
      {findings.slice(0, 2).map((finding) => (
        <div className="findingLine" key={`${analysis.id}-${finding.title}`}>
          <strong>{finding.title}</strong>
          <span>{finding.detail}</span>
        </div>
      ))}
      {(missing.length > 0 || risks.length > 0) && (
        <div className="tagWrap">
          {missing.slice(0, 4).map((item) => (
            <span className="tag warn" key={`missing-${item}`}>
              Thiếu: {item}
            </span>
          ))}
          {risks.slice(0, 3).map((item) => (
            <span className="tag risk" key={`risk-${item}`}>
              Rủi ro: {item}
            </span>
          ))}
        </div>
      )}
      {tools.length > 0 && (
        <div className="toolStrip">
          {tools.map((tool) => (
            <span key={`${analysis.id}-${tool.name}`}>
              {tool.name} v{tool.version}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function ProfileFieldInput({ facts, field }: { facts: Record<string, unknown>; field: ProfileField }) {
  const value = formatProfileValue(field, facts[field.key]);

  return (
    <label className={field.type === "textarea" ? "wideField" : undefined}>
      {field.label}
      {field.type === "textarea" ? (
        <textarea name={field.key} rows={field.rows ?? 3} defaultValue={value} placeholder={field.placeholder} />
      ) : field.type === "select" ? (
        <select name={field.key} defaultValue={value}>
          <option value="">Chọn</option>
          {field.options?.map((option) => (
            <option key={option}>{option}</option>
          ))}
        </select>
      ) : (
        <input
          name={field.key}
          defaultValue={value}
          inputMode={field.type === "number" ? "numeric" : undefined}
          type={field.type === "date" ? "date" : "text"}
          placeholder={field.placeholder}
        />
      )}
    </label>
  );
}

function DocumentChecklistPanel() {
  return (
    <div className="documentChecklist">
      {documentChecklist.map((group, index) => (
        <details className="checklistGroup" key={group.title} open={index < 2}>
          <summary>
            <span>{group.title}</span>
            <small>{group.items.length} mục</small>
          </summary>
          <div className="checklistItems">
            {group.items.map((item) => (
              <span key={item}>{item}</span>
            ))}
          </div>
        </details>
      ))}
    </div>
  );
}

export default function StartupDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [startup, setStartup] = useState<Startup | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let ignore = false;
    Promise.all([api.getStartup(id), api.listDocuments(id), api.listAnalyses(id)])
      .then(([startupData, documentData, analysisData]) => {
        if (!ignore) {
          setStartup(startupData);
          setDocuments(documentData);
          setAnalyses(analysisData);
        }
      })
      .catch((err: unknown) => {
        if (!ignore) setError(err instanceof Error ? err.message : "Không thể tải hồ sơ");
      });
    return () => {
      ignore = true;
    };
  }, [id]);

  const analysisMap = useMemo(() => latestByModule(analyses), [analyses]);

  function mergeAnalysis(result: Analysis) {
    setAnalyses((current) => [result, ...current.filter((item) => item.module !== result.module)]);
  }

  async function saveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!startup) return;
    const form = new FormData(event.currentTarget);
    const facts: Record<string, unknown> = { ...startup.facts };

    for (const section of profileSections) {
      for (const field of section.fields) {
        const value = readProfileField(form, field);
        if (value !== undefined) facts[field.key] = value;
        else delete facts[field.key];
      }
    }

    setBusy("profile");
    setError("");
    try {
      const updated = await api.updateStartup(id, {
        name: textValue(form, "name"),
        industry: textValue(form, "industry") || null,
        stage: textValue(form, "stage") || null,
        primary_location: textValue(form, "location") || null,
        facts,
      });
      setStartup(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không thể lưu hồ sơ");
    } finally {
      setBusy(null);
    }
  }

  async function upload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const input = event.currentTarget.elements.namedItem("document") as HTMLInputElement;
    if (!input.files?.[0]) return;
    setBusy("upload");
    setError("");
    try {
      const document = await api.uploadDocument(id, input.files[0]);
      setDocuments((current) => [document, ...current]);
      event.currentTarget.reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload thất bại");
    } finally {
      setBusy(null);
    }
  }

  async function analyze(module: AnalysisModule) {
    if (module === "surrounding_area") {
      document.getElementById("surrounding-area")?.scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }
    setBusy(module);
    setError("");
    try {
      mergeAnalysis(await api.runAnalysis(id, module));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Phân tích thất bại");
    } finally {
      setBusy(null);
    }
  }

  if (!startup) {
    return (
      <div className="pageShell">
        <p className="muted">Đang tải hồ sơ...</p>
      </div>
    );
  }

  const facts = startup.facts ?? {};
  const profileScore = profileReadiness(startup);
  const completedModules = modules.filter((module) => analysisMap[module.id]).length;
  const latestScore = analyses.find((analysis) => analysis.score !== null && analysis.score !== undefined)?.score;
  const actionLabel = nextAction(startup, documents, analysisMap);

  return (
    <div className="pageShell">
      <Link href="/" className="backLink">
        ← Danh sách startup
      </Link>

      <section className="detailHeader">
        <div className="avatar large">{startup.name.slice(0, 2).toUpperCase()}</div>
        <div>
          <p className="eyebrow">STARTUP PROFILE</p>
          <h1>{startup.name}</h1>
          <p className="muted">
            {[startup.industry, startup.stage, startup.primary_location].filter(Boolean).join(" · ") ||
              "Chưa đủ thông tin hồ sơ"}
          </p>
        </div>
      </section>

      <nav className="pageQuickNav" aria-label="Điều hướng hồ sơ">
        <a href="#analysis-modules">Analysis</a>
        <a href="#profile-facts">Profile</a>
        <a href="#surrounding-area">Area scan</a>
        <a href="#startup-documents">Documents</a>
        <a href="#document-copilot">Copilot</a>
      </nav>

      <section className="detailInsightGrid" aria-label="Tóm tắt trạng thái hồ sơ">
        <div className="insightTile primary">
          <span>Mức sẵn sàng</span>
          <strong>{profileScore}%</strong>
          <small>Dữ kiện hồ sơ, tài chính và vị trí</small>
        </div>
        <div className="insightTile">
          <span>Module đã có kết quả</span>
          <strong>
            {completedModules}/{modules.length}
          </strong>
          <small>Business model, cash flow, surrounding area</small>
        </div>
        <div className="insightTile">
          <span>Tài liệu</span>
          <strong>{documents.length}</strong>
          <small>Pháp lý, doanh thu, chi phí, vận hành</small>
        </div>
        <div className="insightTile action">
          <span>Việc tiếp theo</span>
          <strong>{actionLabel}</strong>
          <small>{latestScore !== null && latestScore !== undefined ? `Điểm gần nhất ${Math.round(latestScore)}/100` : "Chưa có điểm module"}</small>
        </div>
      </section>

      {error && <div className="alert">{error}</div>}

      <section className="workspaceGrid">
        <div className="workspaceMain">
          <div className="surface" id="analysis-modules">
            <div className="sectionHeader">
              <div>
                <p className="eyebrow">ANALYSIS</p>
                <h2>Module phân tích</h2>
              </div>
              <span className="muted">Kết quả giữ nguyên theo từng module</span>
            </div>

            <div className="moduleList">
              {modules.map((module) => {
                const result = analysisMap[module.id];
                const status = result?.status ?? "idle";
                return (
                  <article className="moduleRow" key={module.id}>
                    <div className="moduleCode">{module.code}</div>
                    <div className="moduleBody">
                      <div className="moduleTitleRow">
                        <div>
                          <h3>{module.name}</h3>
                          <p>{module.description}</p>
                        </div>
                        <span className={`status ${status}`}>{statusCopy[status] ?? status}</span>
                      </div>
                      {result ? (
                        module.id === "cash_flow" ? (
                          <CashFlowAnalysis analysis={result} />
                        ) : (
                          <ModuleReportPreview analysis={result} />
                        )
                      ) : (
                        <p className="muted smallText">Chưa có báo cáo cho module này.</p>
                      )}
                    </div>
                    <div className="moduleAction">
                      <strong>{scoreText(result?.score)}</strong>
                      <span>/100</span>
                      <button className="secondaryButton" disabled={busy === module.id} onClick={() => analyze(module.id)}>
                        {module.id === "surrounding_area"
                          ? "Mở wizard"
                          : busy === module.id
                            ? "Đang chạy..."
                            : result
                              ? "Chạy lại"
                              : "Chạy"}
                      </button>
                    </div>
                  </article>
                );
              })}
            </div>
          </div>

          <div className="surface" id="profile-facts">
            <div className="sectionHeader">
              <div>
                <p className="eyebrow">PROFILE FACTS</p>
                <h2>Dữ kiện phân tích</h2>
              </div>
              <span className="muted">Lưu trước khi chạy module</span>
            </div>
            <form className="stackForm" onSubmit={saveProfile} key={startup.updated_at}>
              <div className="formRow three">
                <label>
                  Tên
                  <input name="name" required defaultValue={startup.name} />
                </label>
                <label>
                  Lĩnh vực
                  <input name="industry" defaultValue={startup.industry ?? ""} />
                </label>
                <label>
                  Giai đoạn
                  <select name="stage" defaultValue={startup.stage ?? ""}>
                    <option value="">Chọn</option>
                    {stageOptions.map((stage) => (
                      <option key={stage}>{stage}</option>
                    ))}
                  </select>
                </label>
              </div>
              <label>
                Địa điểm chính
                <input name="location" defaultValue={startup.primary_location ?? ""} />
              </label>
              {profileSections.map((section) => (
                <div className="factSection" key={section.id}>
                  <div className="factSectionHeader">
                    <div>
                      <p className="eyebrow">{section.eyebrow}</p>
                      <h3>{section.title}</h3>
                    </div>
                    <p>{section.description}</p>
                  </div>
                  <div className="factGrid">
                    {section.fields.map((field) => (
                      <ProfileFieldInput facts={facts} field={field} key={field.key} />
                    ))}
                  </div>
                </div>
              ))}
              <button className="primaryButton" disabled={busy === "profile"}>
                {busy === "profile" ? "Đang lưu..." : "Lưu dữ kiện"}
              </button>
            </form>
          </div>

          <SurroundingArea
            startupId={id}
            industry={startup.industry}
            initialAddress={startup.primary_location ?? ""}
            facts={facts}
            initialAnalysis={analysisMap.surrounding_area}
            onAnalysisComplete={mergeAnalysis}
          />

          <div className="surface" id="startup-documents">
            <div className="sectionHeader">
              <div>
                <p className="eyebrow">DOCUMENTS</p>
                <h2>Tài liệu startup</h2>
              </div>
              <span className="muted">{documents.length} tài liệu</span>
            </div>
            <form className="uploadBox" onSubmit={upload}>
              <input name="document" type="file" accept=".pdf,.docx,.pptx,.xlsx,.txt,.md,.csv" required />
              <button className="primaryButton" disabled={busy === "upload"}>
                {busy === "upload" ? "Đang xử lý..." : "Tải lên"}
              </button>
            </form>
            <DocumentChecklistPanel />
            <div className="documentList">
              {documents.map((document) => (
                <div className="documentRow" key={document.id}>
                  <span className="fileIcon">DOC</span>
                  <div>
                    <strong>{document.filename}</strong>
                    <span>{document.status}</span>
                  </div>
                </div>
              ))}
              {!documents.length && <p className="muted">Chưa có tài liệu.</p>}
            </div>
          </div>
        </div>

      </section>
      <ChatWidget startupId={id} />
    </div>
  );
}
