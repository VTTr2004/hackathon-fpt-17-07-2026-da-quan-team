"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Candidate } from "@/types";

export default function CandidatesPage() {
  const [items, setItems] = useState<Candidate[]>([]); const [selected, setSelected] = useState<string[]>([]);
  const [compare, setCompare] = useState<Candidate[]>([]); const [busy, setBusy] = useState(""); const [error, setError] = useState("");
  const load = useCallback(async (params?: URLSearchParams) => {
    try { setItems(await api.listCandidates(params)); setError(""); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Không thể tải ứng viên"); }
  }, []);
  useEffect(() => {
    const task = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(task);
  }, [load]);

  async function filter(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const form = new FormData(event.currentTarget); const params = new URLSearchParams();
    for (const key of ["industry", "stage", "location", "min_score"]) { const value = String(form.get(key) ?? "").trim(); if (value) params.set(key, value); }
    await load(params);
  }
  async function act(id: string, action: "shortlist" | "request") {
    setBusy(`${action}-${id}`);
    try {
      if (action === "shortlist") await api.shortlistCandidate(id);
      else await api.requestAccess(id, "Phù hợp investment thesis và muốn tìm hiểu data room.");
      await load();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Thao tác thất bại"); }
    finally { setBusy(""); }
  }
  async function runCompare() { if (selected.length >= 2) setCompare(await api.compareCandidates(selected)); }

  return <div className="hdShell investorPage">
    <section className="hdPageHead"><div><h1>Discover startups</h1><p className="hdLead">Chỉ hiển thị snapshot công khai của hồ sơ đã nộp và bật discovery.</p></div><button className="hdBtn primary" onClick={() => api.generateMatches().then(setItems)}>Chạy matching</button></section>
    {error && <div className="hdAlert"><span>{error}</span></div>}
    <form className="hdCard candidateFilters" onSubmit={filter}><input name="industry" placeholder="Lĩnh vực" /><input name="stage" placeholder="Giai đoạn" /><input name="location" placeholder="Địa điểm" /><input name="min_score" type="number" min="0" max="100" placeholder="Điểm tối thiểu" /><button className="hdBtn">Lọc</button></form>
    {selected.length >= 2 && <div className="compareBar"><span>Đã chọn {selected.length} startup</span><button className="hdBtn primary" onClick={() => void runCompare()}>So sánh</button></div>}
    {compare.length > 0 && <section className="hdCard"><div className="hdSectionHead"><h2>So sánh nhanh</h2><button className="hdBtn" onClick={() => setCompare([])}>Đóng</button></div><div className="compareGrid">{compare.map((item) => <div key={item.startup_id}><strong>{item.name}</strong><b>{item.fit_score} Fit</b><span>{item.confidence_score} Confidence</span></div>)}</div></section>}
    <section className="candidateGrid">{items.map((item) => <article className="hdCard candidateCard" key={item.startup_id}>
      <div className="candidateHead"><label><input type="checkbox" checked={selected.includes(item.startup_id)} onChange={(event) => setSelected((old) => event.target.checked ? [...old, item.startup_id].slice(-5) : old.filter((id) => id !== item.startup_id))} /> So sánh</label><span className={`accessBadge ${item.access_status}`}>{item.access_status}</span></div>
      <h2>{item.name}</h2><div className="hdRecordTags">{[item.industry, item.subsector, item.stage, item.location].filter(Boolean).map((tag) => <span className="hdChip" key={tag}>{tag}</span>)}</div>
      <div className="scorePair"><div><strong>{item.fit_score}</strong><span>Fit score</span></div><div><strong>{item.confidence_score}</strong><span>Confidence</span></div></div>
      <div className="candidateFacts"><span>Runway: {item.runway_months ?? "Cần xác minh"} tháng</span><span>Growth: {item.revenue_growth ?? "Cần xác minh"}</span></div>
      <ul className="matchReasons">{item.matched_reasons.slice(0, 3).map((reason) => <li key={reason}>{reason}</li>)}</ul>
      <div className="verifyList">{item.missing_evidence.slice(0, 2).map((reason) => <span key={reason}>Cần xác minh: {reason}</span>)}</div>
      <div className="candidateActions"><button className="hdBtn" disabled={item.pipeline_status === "shortlisted" || busy !== ""} onClick={() => void act(item.startup_id, "shortlist")}>Shortlist</button>{item.access_status === "active" ? <Link className="hdBtn primary" href={`/startups/${item.startup_id}`}>Mở data room</Link> : <button className="hdBtn primary" disabled={item.access_status === "pending" || busy !== ""} onClick={() => void act(item.startup_id, "request")}>Yêu cầu kết nối</button>}</div>
    </article>)}{!items.length && <div className="hdCard hdEmpty">Chưa có startup phù hợp. Hãy kiểm tra thesis hoặc dữ liệu discoverable.</div>}</section>
  </div>;
}
