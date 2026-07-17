"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { Startup } from "@/types";

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

  async function createStartup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setCreating(true);
    const form = new FormData(event.currentTarget);
    try {
      const startup = await api.createStartup({
        name: String(form.get("name") ?? ""),
        industry: String(form.get("industry") ?? ""),
        stage: String(form.get("stage") ?? ""),
        primary_location: String(form.get("location") ?? ""),
      });
      setStartups((current) => [startup, ...current]);
      event.currentTarget.reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không thể tạo startup");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="pageShell">
      <section className="hero">
        <div>
          <p className="eyebrow">AI DUE DILIGENCE WORKSPACE</p>
          <h1>Hiểu startup từ dữ liệu, không từ phỏng đoán.</h1>
          <p className="heroCopy">
            Phân tích mô hình kinh doanh, dòng tiền, khu vực và hỏi đáp trực tiếp trên tài liệu.
          </p>
        </div>
        <div className="heroStats">
          <strong>{startups.length}</strong>
          <span>hồ sơ đang quản lý</span>
        </div>
      </section>

      {error && <div className="alert">{error}</div>}

      <section className="dashboardGrid">
        <div className="panel">
          <div className="panelHeader">
            <div>
              <p className="eyebrow">DEAL ROOM</p>
              <h2>Hồ sơ startup</h2>
            </div>
          </div>
          {loading ? (
            <p className="muted">Đang tải...</p>
          ) : startups.length === 0 ? (
            <div className="emptyState">Chưa có hồ sơ. Tạo startup đầu tiên ở biểu mẫu bên cạnh.</div>
          ) : (
            <div className="startupList">
              {startups.map((startup) => (
                <Link className="startupCard" href={`/startups/${startup.id}`} key={startup.id}>
                  <div className="avatar">{startup.name.slice(0, 2).toUpperCase()}</div>
                  <div className="startupMeta">
                    <strong>{startup.name}</strong>
                    <span>{[startup.industry, startup.stage].filter(Boolean).join(" · ") || "Chưa phân loại"}</span>
                  </div>
                  <span className="arrow">→</span>
                </Link>
              ))}
            </div>
          )}
        </div>

        <aside className="panel createPanel">
          <p className="eyebrow">NEW STARTUP</p>
          <h2>Tạo hồ sơ mới</h2>
          <form className="stackForm" onSubmit={createStartup}>
            <label>
              Tên startup
              <input name="name" required placeholder="Ví dụ: GreenFlow" />
            </label>
            <label>
              Lĩnh vực
              <input name="industry" placeholder="Climate tech" />
            </label>
            <div className="formRow">
              <label>
                Giai đoạn
                <select name="stage" defaultValue="">
                  <option value="">Chọn</option>
                  <option>Pre-seed</option>
                  <option>Seed</option>
                  <option>Series A</option>
                  <option>Growth</option>
                </select>
              </label>
              <label>
                Khu vực
                <input name="location" placeholder="Hà Nội" />
              </label>
            </div>
            <button className="primaryButton" disabled={creating}>
              {creating ? "Đang tạo..." : "Tạo hồ sơ"}
            </button>
          </form>
        </aside>
      </section>
    </div>
  );
}
