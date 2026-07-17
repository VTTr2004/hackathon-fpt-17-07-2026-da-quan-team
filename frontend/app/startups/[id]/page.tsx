"use client";

import Link from "next/link";
import { FormEvent, use, useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { Analysis, AnalysisModule, ChatResponse, DocumentItem, Startup } from "@/types";

const modules: Array<{ id: AnalysisModule; name: string; icon: string; description: string }> = [
  { id: "business_model", name: "Mô hình kinh doanh", icon: "BM", description: "Thị trường, khách hàng, giá trị và khả năng mở rộng" },
  { id: "cash_flow", name: "Dòng tiền", icon: "CF", description: "Burn rate, runway, hòa vốn và stress scenario" },
  { id: "surrounding_area", name: "Khu vực xung quanh", icon: "AR", description: "Vị trí, khoảng cách, mật độ và khả năng tiếp cận" },
];

export default function StartupDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [startup, setStartup] = useState<Startup | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [question, setQuestion] = useState("");
  const [chat, setChat] = useState<ChatResponse | null>(null);
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

  async function upload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const input = event.currentTarget.elements.namedItem("document") as HTMLInputElement;
    if (!input.files?.[0]) return;
    setBusy("upload");
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
    setBusy(module);
    try {
      const result = await api.runAnalysis(id, module);
      setAnalyses((current) => [result, ...current.filter((item) => item.module !== module)]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Phân tích thất bại");
    } finally {
      setBusy(null);
    }
  }

  async function ask(event: FormEvent) {
    event.preventDefault();
    if (!question.trim()) return;
    setBusy("chat");
    try {
      setChat(await api.chat(id, question));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không thể trả lời");
    } finally {
      setBusy(null);
    }
  }

  if (!startup) return <div className="pageShell"><p className="muted">Đang tải hồ sơ...</p></div>;

  return (
    <div className="pageShell">
      <Link href="/" className="backLink">← Danh sách startup</Link>
      <section className="detailHero">
        <div className="avatar large">{startup.name.slice(0, 2).toUpperCase()}</div>
        <div>
          <p className="eyebrow">STARTUP PROFILE</p>
          <h1>{startup.name}</h1>
          <p className="muted">{[startup.industry, startup.stage, startup.primary_location].filter(Boolean).join(" · ")}</p>
        </div>
      </section>

      {error && <div className="alert">{error}</div>}

      <section className="workspaceGrid">
        <div className="workspaceMain">
          <div className="panel">
            <div className="panelHeader">
              <div><p className="eyebrow">ANALYSIS</p><h2>Ba góc nhìn chuyên sâu</h2></div>
              <span className="muted">Tool tính toán + Gemini diễn giải</span>
            </div>
            <div className="moduleGrid">
              {modules.map((module) => {
                const result = analyses.find((item) => item.module === module.id);
                return (
                  <article className="moduleCard" key={module.id}>
                    <div className="moduleTop"><span className="moduleIcon">{module.icon}</span><span className={`status ${result?.status ?? "idle"}`}>{result?.status ?? "Chưa chạy"}</span></div>
                    <h3>{module.name}</h3>
                    <p>{module.description}</p>
                    {result && <div className="scoreRow"><strong>{result.score ?? "—"}</strong><span>/ 100</span></div>}
                    {result?.summary && <p className="resultSummary">{result.summary}</p>}
                    {result?.report.tool_calls?.length ? <p className="toolNote">Tools: {result.report.tool_calls.map((tool) => tool.name).join(", ")}</p> : null}
                    <button className="secondaryButton" disabled={busy === module.id} onClick={() => analyze(module.id)}>
                      {busy === module.id ? "Đang phân tích..." : result ? "Chạy lại" : "Bắt đầu phân tích"}
                    </button>
                  </article>
                );
              })}
            </div>
          </div>

          <div className="panel">
            <p className="eyebrow">DOCUMENTS</p>
            <h2>Tài liệu startup</h2>
            <form className="uploadBox" onSubmit={upload}>
              <input name="document" type="file" accept=".pdf,.docx,.pptx,.xlsx,.txt,.md,.csv" required />
              <button className="primaryButton" disabled={busy === "upload"}>{busy === "upload" ? "Đang xử lý..." : "Tải lên"}</button>
            </form>
            <div className="documentList">
              {documents.map((document) => <div className="documentRow" key={document.id}><span className="fileIcon">DOC</span><div><strong>{document.filename}</strong><span>{document.status}</span></div></div>)}
              {!documents.length && <p className="muted">Chưa có tài liệu.</p>}
            </div>
          </div>
        </div>

        <aside className="panel chatPanel">
          <div><p className="eyebrow">DOCUMENT COPILOT</p><h2>Hỏi Gemini</h2><p className="muted">Câu trả lời chỉ dựa trên tài liệu của startup này.</p></div>
          <div className="chatAnswer">
            {chat ? <><p>{chat.answer}</p>{chat.citations.map((citation, index) => <details key={`${citation.document_id}-${index}`}><summary>[{index + 1}] {citation.filename}</summary><blockquote>{citation.excerpt}</blockquote></details>)}</> : <div className="emptyState">Hỏi về traction, khách hàng, doanh thu hoặc thông tin trong hồ sơ.</div>}
          </div>
          <form className="chatForm" onSubmit={ask}>
            <textarea value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Startup đang có bao nhiêu khách hàng?" />
            <button className="primaryButton" disabled={busy === "chat"}>{busy === "chat" ? "Gemini đang đọc..." : "Gửi câu hỏi"}</button>
          </form>
        </aside>
      </section>
    </div>
  );
}
