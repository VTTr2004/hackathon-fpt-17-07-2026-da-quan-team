"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { api } from "@/lib/api";
import { quickCreateFields, readProfileField, stageOptions, textValue } from "@/lib/profileFields";
import type { ProfileField } from "@/lib/profileFields";
import type { Startup } from "@/types";

const workflowSteps = [
  { title: "Intake", detail: "Hồ sơ & dữ kiện nền" },
  { title: "Evidence", detail: "Tài liệu và trích xuất" },
  { title: "Analyze", detail: "Business, cash flow, area" },
  { title: "Review", detail: "Rủi ro & dữ liệu thiếu" },
  { title: "Decision", detail: "Câu hỏi đầu tư tiếp theo" },
];

function readiness(startup: Startup) {
  const facts = startup.facts ?? {};
  const fields = [
    startup.industry,
    startup.stage,
    startup.primary_location,
    facts.business_type,
    facts.problem,
    facts.solution,
    facts.target_customers,
    facts.core_products,
    facts.revenue_model,
    facts.current_cash,
    facts.monthly_revenue,
    facts.monthly_expense,
  ];
  const done = fields.filter((value) => {
    if (Array.isArray(value)) return value.length > 0;
    return value !== null && value !== undefined && String(value).trim() !== "";
  }).length;
  return Math.round((done / fields.length) * 100);
}

function readinessTone(progress: number) {
  if (progress >= 75) return "strong";
  if (progress >= 45) return "medium";
  return "weak";
}

function readinessLabel(progress: number) {
  if (progress >= 75) return "Sẵn sàng phân tích";
  if (progress >= 45) return "Cần bổ sung";
  return "Thiếu dữ kiện";
}

function FactFieldInput({ field }: { field: ProfileField }) {
  return (
    <label className={field.type === "textarea" ? "wideField" : undefined}>
      {field.label}
      {field.type === "textarea" ? (
        <textarea name={field.key} rows={field.rows ?? 3} placeholder={field.placeholder} />
      ) : field.type === "select" ? (
        <select name={field.key} defaultValue="">
          <option value="">Chọn</option>
          {field.options?.map((option) => (
            <option key={option}>{option}</option>
          ))}
        </select>
      ) : (
        <input
          name={field.key}
          inputMode={field.type === "number" ? "numeric" : undefined}
          type={field.type === "date" ? "date" : "text"}
          placeholder={field.placeholder}
        />
      )}
    </label>
  );
}

export default function DashboardPage() {
  const [startups, setStartups] = useState<Startup[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    let ignore = false;
    api
      .listStartups()
      .then((data) => {
        if (!ignore) {
          setStartups(data);
          setError("");
        }
      })
      .catch((err: unknown) => {
        if (!ignore) setError(err instanceof Error ? err.message : "Không thể tải dữ liệu");
      })
      .finally(() => {
        if (!ignore) setLoading(false);
      });
    return () => {
      ignore = true;
    };
  }, []);

  const stats = useMemo(() => {
    const withIndustry = startups.filter((startup) => startup.industry).length;
    const withLocation = startups.filter((startup) => startup.primary_location).length;
    const averageReadiness = startups.length
      ? Math.round(startups.reduce((sum, startup) => sum + readiness(startup), 0) / startups.length)
      : 0;
    return { withIndustry, withLocation, averageReadiness };
  }, [startups]);

  async function createStartup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setCreating(true);
    setError("");
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const facts: Record<string, unknown> = {};

    for (const section of quickCreateFields) {
      for (const field of section.fields) {
        const value = readProfileField(form, field);
        if (value !== undefined) facts[field.key] = value;
      }
    }

    try {
      const startup = await api.createStartup({
        name: textValue(form, "name"),
        industry: textValue(form, "industry"),
        stage: textValue(form, "stage"),
        primary_location: textValue(form, "location"),
        facts,
      });
      setStartups((current) => [startup, ...current]);
      formElement.reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không thể tạo startup");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="pageShell dashboardShell">
      <section className="pageHeader">
        <div>
          <p className="eyebrow">STARTUP LENS</p>
          <h1>Phòng thẩm định startup</h1>
          <p className="pageLead">
            Quản lý hồ sơ, tài liệu, dữ kiện phân tích và các module kiểm chứng trong cùng một không gian làm việc.
          </p>
        </div>
        <div className="headerActions">
          <span className="systemBadge">Gemini ready</span>
        </div>
      </section>

      <section className="workflowStrip" aria-label="Luồng thẩm định">
        {workflowSteps.map((step, index) => (
          <div className="workflowStep" key={step.title}>
            <span>{String(index + 1).padStart(2, "0")}</span>
            <strong>{step.title}</strong>
            <small>{step.detail}</small>
          </div>
        ))}
      </section>

      <section className="metricGrid" aria-label="Tổng quan hồ sơ">
        <div className="metricTile">
          <span>Hồ sơ</span>
          <strong>{startups.length}</strong>
        </div>
        <div className="metricTile">
          <span>Có ngành</span>
          <strong>{stats.withIndustry}</strong>
        </div>
        <div className="metricTile">
          <span>Có địa điểm</span>
          <strong>{stats.withLocation}</strong>
        </div>
        <div className="metricTile">
          <span>Sẵn sàng TB</span>
          <strong>{stats.averageReadiness}%</strong>
        </div>
      </section>

      {error && <div className="alert">{error}</div>}

      <section className="dashboardGrid">
        <div className="surface">
          <div className="sectionHeader">
            <div>
              <p className="eyebrow">DEAL ROOM</p>
              <h2>Hồ sơ startup</h2>
            </div>
            <span className="muted">{loading ? "Đang tải" : `${startups.length} hồ sơ`}</span>
          </div>

          {loading ? (
            <div className="skeletonList">
              <span />
              <span />
              <span />
            </div>
          ) : startups.length === 0 ? (
            <div className="emptyState">Chưa có hồ sơ. Tạo startup đầu tiên ở biểu mẫu bên cạnh.</div>
          ) : (
            <div className="recordList">
              {startups.map((startup) => {
                const progress = readiness(startup);
                return (
                  <Link className="recordRow" href={`/startups/${startup.id}`} key={startup.id}>
                    <div className="avatar">{startup.name.slice(0, 2).toUpperCase()}</div>
                    <div className="recordMain">
                      <strong>{startup.name}</strong>
                      <span>
                        {[startup.industry, startup.stage, startup.primary_location].filter(Boolean).join(" · ") ||
                          "Chưa có phân loại"}
                      </span>
                      <em className={`readinessPill ${readinessTone(progress)}`}>{readinessLabel(progress)}</em>
                    </div>
                    <div className="progressCell" aria-label={`Mức sẵn sàng ${progress}%`}>
                      <div className="progressTrack">
                        <span style={{ width: `${progress}%` }} />
                      </div>
                      <small>{progress}%</small>
                    </div>
                  </Link>
                );
              })}
            </div>
          )}
        </div>

        <aside className="surface createSurface">
          <div className="sectionHeader compact">
            <div>
              <p className="eyebrow">NEW PROFILE</p>
              <h2>Tạo hồ sơ</h2>
            </div>
          </div>
          <p className="sideIntro">
            Nhập dữ kiện tối thiểu để tạo deal room. Có thể bổ sung sâu hơn ở màn chi tiết.
          </p>
          <form className="stackForm" onSubmit={createStartup}>
            <label>
              Tên startup
              <input name="name" required placeholder="GreenFlow" />
            </label>
            <label>
              Lĩnh vực
              <input name="industry" placeholder="F&B, SaaS, logistics..." />
            </label>
            <div className="formRow">
              <label>
                Giai đoạn
                <select name="stage" defaultValue="">
                  <option value="">Chọn</option>
                  {stageOptions.map((stage) => (
                    <option key={stage}>{stage}</option>
                  ))}
                </select>
              </label>
              <label>
                Địa điểm chính
                <input name="location" placeholder="Quận 1, TP.HCM" />
              </label>
            </div>
            {quickCreateFields.map((section) => (
              <div className="factSection compact" key={section.id}>
                <div className="factSectionHeader">
                  <p className="eyebrow">{section.eyebrow}</p>
                  <h3>{section.title}</h3>
                </div>
                <div className="factGrid">
                  {section.fields.map((field) => (
                    <FactFieldInput field={field} key={field.key} />
                  ))}
                </div>
              </div>
            ))}
            <button className="primaryButton" disabled={creating}>
              {creating ? "Đang tạo..." : "Tạo hồ sơ"}
            </button>
          </form>
        </aside>
      </section>
    </div>
  );
}
