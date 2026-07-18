"use client";

import { FormEvent, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { InvestorPreference } from "@/types";

const split = (value: FormDataEntryValue | null) => String(value ?? "").split(",").map((item) => item.trim()).filter(Boolean);
const number = (value: FormDataEntryValue | null) => value ? Number(value) : null;

export default function InvestorPreferencesPage() {
  const [preference, setPreference] = useState<InvestorPreference | null>(null);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => { api.getInvestorPreferences().then(setPreference).catch((error) => setMessage(error.message)); }, []);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const form = new FormData(event.currentTarget); setBusy(true);
    try {
      const updated = await api.updateInvestorPreferences({
        preferred_industries: split(form.get("industries")), preferred_subsectors: split(form.get("subsectors")),
        preferred_stages: split(form.get("stages")), preferred_locations: split(form.get("locations")),
        ticket_min: number(form.get("ticket_min")), ticket_max: number(form.get("ticket_max")),
        minimum_monthly_revenue: number(form.get("minimum_monthly_revenue")),
        maximum_runway_months: number(form.get("maximum_runway_months")),
        strategic_capabilities: split(form.get("capabilities")),
      });
      setPreference(updated); setMessage("Đã lưu khẩu vị đầu tư.");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Không thể lưu"); }
    finally { setBusy(false); }
  }

  if (!preference) return <div className="hdShell"><p>{message || "Đang tải khẩu vị đầu tư…"}</p></div>;
  return <div className="hdShell investorPage">
    <section className="hdPageHead"><div><h1>Investment thesis</h1><p className="hdLead">Thiết lập tiêu chí hard filter và tín hiệu dùng để xếp hạng startup.</p></div></section>
    {message && <div className="hdAlert"><span>{message}</span></div>}
    <form className="hdCard thesisForm" onSubmit={save}>
      <div className="hdSectionHead"><h2>Khẩu vị đầu tư</h2><span className="hdCount">Phân cách nhiều giá trị bằng dấu phẩy</span></div>
      <div className="investorFormGrid">
        <label>Lĩnh vực<input name="industries" defaultValue={preference.preferred_industries.join(", ")} placeholder="F&B, Retail" /></label>
        <label>Subsector<input name="subsectors" defaultValue={preference.preferred_subsectors.join(", ")} placeholder="Coffee, Restaurant" /></label>
        <label>Giai đoạn<input name="stages" defaultValue={preference.preferred_stages.join(", ")} placeholder="Pre-seed, Seed" /></label>
        <label>Địa điểm<input name="locations" defaultValue={preference.preferred_locations.join(", ")} placeholder="Hà Nội, TP.HCM" /></label>
        <label>Ticket tối thiểu<input name="ticket_min" type="number" min="0" defaultValue={preference.ticket_min ?? ""} /></label>
        <label>Ticket tối đa<input name="ticket_max" type="number" min="0" defaultValue={preference.ticket_max ?? ""} /></label>
        <label>Doanh thu tháng tối thiểu<input name="minimum_monthly_revenue" type="number" min="0" defaultValue={preference.minimum_monthly_revenue ?? ""} /></label>
        <label>Runway tối đa (tháng)<input name="maximum_runway_months" type="number" min="0" defaultValue={preference.maximum_runway_months ?? ""} /></label>
        <label className="wideField">Năng lực có thể cung cấp<input name="capabilities" defaultValue={preference.strategic_capabilities.join(", ")} placeholder="vốn, mở rộng chuỗi, phân phối" /></label>
      </div>
      <button className="hdBtn primary" disabled={busy}>{busy ? "Đang lưu…" : "Lưu investment thesis"}</button>
    </form>
  </div>;
}
