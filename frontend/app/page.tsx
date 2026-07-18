"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Startup } from "@/types";

const investorWorkflowSteps = [
  { title: "Intake", detail: "Hồ sơ & dữ kiện nền" },
  { title: "Evidence", detail: "Tài liệu và trích xuất" },
  { title: "Analyze", detail: "Business, cash flow, area" },
  { title: "Review", detail: "Rủi ro & dữ liệu thiếu" },
  { title: "Decision", detail: "Câu hỏi đầu tư tiếp theo" },
];

const startupWorkflowSteps = [
  { title: "Draft", detail: "Nhập dữ liệu hồ sơ" },
  { title: "Evidence", detail: "Tải tài liệu" },
  { title: "Check", detail: "Kiểm tra độ đầy đủ" },
  { title: "Submit", detail: "Nộp và khóa phiên bản" },
  { title: "Update", detail: "Bổ sung bằng phiên bản mới" },
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
  if (progress >= 75) return "Gần đủ trường bắt buộc";
  if (progress >= 45) return "Cần bổ sung";
  return "Thiếu dữ kiện";
}

function MIcon({ name }: { name: string }) {
  return <span className="material-symbols-outlined" aria-hidden="true">{name}</span>;
}

export default function DashboardPage() {
  const { user } = useAuth();
  const isStartup = user?.role === "startup";
  const workflowSteps = isStartup ? startupWorkflowSteps : investorWorkflowSteps;
  const [startups, setStartups] = useState<Startup[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

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

  const metrics = [
    { label: "Hồ sơ", value: String(startups.length), icon: "folder_open", hint: isStartup ? "Của bạn" : "Được chia sẻ" },
    { label: "Có ngành", value: String(stats.withIndustry), icon: "category", hint: "Đã phân loại" },
    { label: "Có địa điểm", value: String(stats.withLocation), icon: "location_on", hint: "Cho phân tích khu vực" },
    { label: "Sẵn sàng TB", value: `${stats.averageReadiness}%`, icon: "verified", hint: "Độ đầy đủ dữ liệu" },
  ];

  return (
    <div className="hdShell">
      <section className="hdPageHead">
        <div>
          <h1>{isStartup ? "Hồ sơ gọi vốn của tôi" : "Bàn thẩm định startup"}</h1>
          <p className="hdLead">
            {isStartup
              ? "Chuẩn bị dữ liệu, kiểm tra độ đầy đủ và nộp phiên bản hồ sơ cho nhà đầu tư."
              : "Phân tích và đánh giá những hồ sơ startup đã chia sẻ với bạn, có dẫn chứng."}
          </p>
        </div>
        {!isStartup && <div className="headerActions"><Link className="hdBtn" href="/investor/preferences">Investment thesis</Link><Link className="hdBtn primary" href="/investor/candidates">Khám phá startup</Link></div>}
      </section>

      <section className="hdWorkflow" aria-label="Luồng xử lý hồ sơ">
        {workflowSteps.map((step, index) => (
          <div className="hdStep" key={step.title}>
            <b>{String(index + 1).padStart(2, "0")}</b>
            <strong>{step.title}</strong>
            <small>{step.detail}</small>
          </div>
        ))}
      </section>

      <section className="hdBento" aria-label="Tổng quan hồ sơ">
        {metrics.map((metric) => (
          <div className="hdMetric" key={metric.label}>
            <div className="hdMetricTop">
              <span>{metric.label}</span>
              <MIcon name={metric.icon} />
            </div>
            <div>
              <strong>{metric.value}</strong>
              <small>{metric.hint}</small>
            </div>
          </div>
        ))}
      </section>

      {error && (
        <div className="hdAlert" role="alert">
          <MIcon name="error" />
          <span>{error}</span>
        </div>
      )}

      <section className="hdCard">
        <div className="hdSectionHead">
          <h2>
            <MIcon name="deployed_code" />
            {isStartup ? "Hồ sơ của tôi" : "Deal room"}
          </h2>
          <span className="hdCount">{loading ? "Đang tải…" : `${startups.length} hồ sơ`}</span>
        </div>

        {loading ? (
          <div className="hdSkeleton">
            <i />
            <i />
            <i />
          </div>
        ) : startups.length === 0 ? (
          <div className="hdEmpty">
            <span>{isStartup ? "Bạn chưa có hồ sơ nào." : "Chưa có hồ sơ nào được chia sẻ với bạn."}</span>
          </div>
        ) : (
          <div className="hdRecordList">
            {startups.map((startup) => {
              const progress = readiness(startup);
              const tags = [startup.industry, startup.stage, startup.primary_location].filter(Boolean) as string[];
              return (
                <div className="hdRecord" key={startup.id}>
                  <div className="hdRecordAvatar">{startup.name.slice(0, 2).toUpperCase()}</div>
                  <div className="hdRecordMain">
                    <Link href={`/startups/${startup.id}`}>
                      <strong>{startup.name}</strong>
                      <div className="hdRecordTags">
                        {tags.length ? (
                          tags.map((tag) => (
                            <span className="hdChip" key={tag}>
                              {tag}
                            </span>
                          ))
                        ) : (
                          <span className="hdChip">Chưa phân loại</span>
                        )}
                        <span className={`hdPill ${isStartup ? readinessTone(progress) : "neutral"}`}>
                          {isStartup ? readinessLabel(progress) : `Phiên bản V${startup.current_version}`}
                        </span>
                      </div>
                    </Link>
                  </div>
                  <div className="hdReadiness" aria-label={`Mức sẵn sàng ${progress}%`}>
                    <div className="track">
                      <i style={{ width: `${progress}%` }} />
                    </div>
                    <small>{progress}%</small>
                  </div>
                  <div className="hdRecordActions">
                    <Link className="hdIconAction" href={`/startups/${startup.id}`} title="Mở hồ sơ" aria-label="Mở hồ sơ">
                      <MIcon name="arrow_forward" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
