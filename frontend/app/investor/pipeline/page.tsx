"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { PipelineItem } from "@/types";

const statuses: PipelineItem["status"][] = ["discovered", "shortlisted", "access_requested", "reviewing", "interested", "passed"];
const labels: Record<PipelineItem["status"], string> = { discovered: "Discovered", shortlisted: "Shortlisted", access_requested: "Requested", reviewing: "Reviewing", interested: "Interested", passed: "Passed" };

export default function PipelinePage() {
  const [items, setItems] = useState<PipelineItem[]>([]); const [error, setError] = useState("");
  const load = useCallback(() => api.listPipeline().then(setItems).catch((reason) => setError(reason.message)), []);
  useEffect(() => { void load(); }, [load]);
  async function move(item: PipelineItem, status: PipelineItem["status"]) {
    try { await api.updatePipeline(item.id, status, item.note); await load(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Không thể cập nhật"); }
  }
  return <div className="hdShell investorPage">
    <section className="hdPageHead"><div><h1>Investor pipeline</h1><p className="hdLead">Theo dõi quy trình đầu tư độc lập với quyền truy cập dữ liệu.</p></div></section>
    {error && <div className="hdAlert"><span>{error}</span></div>}
    <section className="pipelineBoard">{statuses.map((status) => <div className="pipelineColumn" key={status}><header><strong>{labels[status]}</strong><span>{items.filter((item) => item.status === status).length}</span></header>{items.filter((item) => item.status === status).map((item) => <article className="pipelineCard" key={item.id}><strong>{item.startup_name}</strong><div><span>Fit {item.fit_score ?? "—"}</span><span>Confidence {item.confidence_score ?? "—"}</span></div><small>Quyền: {item.access_status}</small><select value={item.status} onChange={(event) => void move(item, event.target.value as PipelineItem["status"])}>{statuses.map((value) => <option value={value} key={value}>{labels[value]}</option>)}</select>{item.access_status === "active" && <Link href={`/startups/${item.startup_id}`}>Mở data room →</Link>}</article>)}</div>)}</section>
  </div>;
}
