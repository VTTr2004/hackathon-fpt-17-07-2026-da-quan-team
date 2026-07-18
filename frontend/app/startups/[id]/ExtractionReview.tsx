"use client";

import { useEffect, useMemo, useState } from "react";

import { api } from "@/lib/api";
import type {
  DocumentItem,
  ProfileExtractionCandidate,
  ProfileExtractionEvidence,
  ProfileExtractionJob,
  Startup,
} from "@/types";

const SUPPORTED_FILE = /\.(pdf|docx|pptx|txt|md|json|png|jpe?g)$/i;

function editableValue(candidate: ProfileExtractionCandidate): string {
  if (Array.isArray(candidate.proposed_value)) return candidate.proposed_value.map(String).join("\n");
  return candidate.proposed_value == null ? "" : String(candidate.proposed_value);
}

function locator(evidence: ProfileExtractionEvidence): string {
  if (evidence.page != null) return `Trang ${evidence.page}`;
  if (evidence.slide != null) return `Slide ${evidence.slide}`;
  if (evidence.table != null) return `Bảng ${evidence.table}`;
  if (evidence.sheet) return `${evidence.sheet}${evidence.row != null ? ` · dòng ${evidence.row}` : ""}`;
  return "Đoạn tài liệu";
}

type Props = {
  startup: Startup;
  documents: DocumentItem[];
  onStartupUpdated: (startup: Startup) => void;
};

export default function ExtractionReview({ startup, documents, onStartupUpdated }: Props) {
  const [job, setJob] = useState<ProfileExtractionJob | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [edits, setEdits] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState<"extract" | "apply" | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const supportedDocuments = useMemo(
    () => documents.filter(
      (document) => document.visibility === "shared" && SUPPORTED_FILE.test(document.filename),
    ),
    [documents],
  );
  const needsOcrDocuments = useMemo(
    () => documents.filter(
      (document) => document.visibility === "shared" && !document.extractable && SUPPORTED_FILE.test(document.filename),
    ),
    [documents],
  );

  function loadJob(nextJob: ProfileExtractionJob | null) {
    setJob(nextJob);
    if (!nextJob) return;
    setSelected(
      new Set(
        nextJob.candidates
          .filter((candidate) => candidate.status === "found" && candidate.confidence >= 0.8)
          .map((candidate) => candidate.id),
      ),
    );
    setEdits(Object.fromEntries(nextJob.candidates.map((candidate) => [candidate.id, editableValue(candidate)])));
  }

  useEffect(() => {
    let cancelled = false;
    void api.listExtractions(startup.id).then((jobs) => {
      if (!cancelled) loadJob(jobs[0] ?? null);
    }).catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [startup.id]);

  async function extract() {
    if (!supportedDocuments.length) {
      setError("Hãy tải lên PDF có text, DOCX, PPTX, TXT hoặc Markdown trước khi trích xuất.");
      return;
    }
    setBusy("extract");
    setError("");
    setMessage("");
    try {
      const result = await api.createExtraction(startup.id, supportedDocuments.map((document) => document.id));
      loadJob(result);
      if (result.status !== "failed") {
        setMessage("Đã tạo đề xuất. Hãy kiểm tra giá trị và bằng chứng trước khi áp dụng.");
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể trích xuất hồ sơ.");
    } finally {
      setBusy(null);
    }
  }

  function toggle(candidateId: string) {
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(candidateId)) next.delete(candidateId);
      else next.add(candidateId);
      return next;
    });
  }

  async function apply() {
    if (!job || job.status !== "completed") return;
    const decisions = job.candidates.map((candidate) => {
      if (!selected.has(candidate.id)) {
        return { candidate_id: candidate.id, action: "reject" as const };
      }
      const value = edits[candidate.id]?.trim() ?? "";
      if (!value) return { candidate_id: candidate.id, action: "reject" as const };
      const changed = value !== editableValue(candidate) || candidate.status !== "found";
      return changed
        ? { candidate_id: candidate.id, action: "edit" as const, value }
        : { candidate_id: candidate.id, action: "accept" as const };
    });
    if (!decisions.some((decision) => decision.action !== "reject")) {
      setError("Hãy chọn ít nhất một đề xuất để áp dụng.");
      return;
    }
    setBusy("apply");
    setError("");
    setMessage("");
    try {
      const updated = await api.confirmExtraction(startup.id, job.id, decisions);
      onStartupUpdated(updated);
      loadJob(await api.getExtraction(startup.id, job.id));
      setMessage("Đã áp dụng các trường được xác nhận vào bản nháp hồ sơ.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể áp dụng đề xuất.");
    } finally {
      setBusy(null);
    }
  }

  const actionable = job?.candidates.filter((candidate) => candidate.proposed_value != null) ?? [];
  const selectedCount = actionable.filter((candidate) => selected.has(candidate.id)).length;

  return (
    <section className="profileExtraction" aria-label="Trích xuất hồ sơ từ tài liệu">
      <div className="cashFlowIntakeHeader">
        <div>
          <span className="cashFlowStep">AI AUTOFILL · HỒ SƠ</span>
          <h4>Đề xuất điền Hồ sơ có dẫn chứng</h4>
          <p>AI đọc nguồn tại Bằng chứng và chỉ cập nhật dữ liệu sau khi bạn kiểm tra, trả lời mục mơ hồ và xác nhận.</p>
        </div>
        <button className="hdBtn primary" type="button" disabled={busy !== null || !supportedDocuments.length} onClick={extract}>
          {busy === "extract" ? "Đang trích xuất..." : job ? "Trích xuất lại" : "Trích xuất từ tài liệu"}
        </button>
      </div>

      <p className="muted">{supportedDocuments.length} tài liệu được chia sẻ và hỗ trợ · JSON, PDF, ảnh, DOCX, PPTX, TXT, Markdown</p>
      {needsOcrDocuments.length > 0 && (
        <div className="cashFlowAlert warning">
          {needsOcrDocuments.map((document) => document.filename).join(", ")}: chưa có text; hệ thống sẽ OCR bằng Gemini 3.1 Flash-Lite khi trích xuất.
        </div>
      )}
      {error && <div className="cashFlowAlert error" role="alert">{error}</div>}
      {message && <div className="cashFlowAlert info">{message}</div>}
      {job?.warnings.map((warning) => <div className="cashFlowAlert warning" key={warning}>{warning}</div>)}

      {job?.status === "failed" && <div className="cashFlowAlert error">{job.error || "Extraction thất bại."}</div>}
      {job && (job.status === "completed" || job.status === "applied") && (
        <>
          <div className="extractionCandidateList">
            {job.candidates.map((candidate) => (
              <article className={`extractionCandidate ${candidate.status}`} key={candidate.id}>
                <div className="extractionCandidateHead">
                  <label>
                    <input
                      type="checkbox"
                      checked={selected.has(candidate.id)}
                      disabled={job.status === "applied" || candidate.status === "not_found"}
                      onChange={() => toggle(candidate.id)}
                    />
                    <strong>{candidate.label}</strong>
                  </label>
                  <span className={`badgeCF ${candidate.status === "found" ? "success" : candidate.status === "not_found" ? "neutral" : "warning"}`}>
                    {candidate.status} · {Math.round(candidate.confidence * 100)}%
                  </span>
                </div>
                <textarea
                  rows={candidate.value_type === "list" ? 3 : 2}
                  value={edits[candidate.id] ?? ""}
                  disabled={job.status === "applied" || candidate.status === "not_found"}
                  placeholder={candidate.status === "not_found" ? "Không tìm thấy bằng chứng" : "Kiểm tra hoặc chỉnh sửa giá trị"}
                  onChange={(event) => setEdits((current) => ({ ...current, [candidate.id]: event.target.value }))}
                />
                <div className="extractionEvidenceList">
                  {candidate.evidence.map((evidence) => (
                    <details key={`${candidate.id}-${evidence.block_id}`}>
                      <summary>{evidence.filename} · {locator(evidence)}</summary>
                      <blockquote>{evidence.quote}</blockquote>
                    </details>
                  ))}
                  {!candidate.evidence.length && <small>Không có bằng chứng đã kiểm chứng.</small>}
                  {candidate.warnings.map((warning) => <small className="warningText" key={warning}>{warning}</small>)}
                </div>
              </article>
            ))}
          </div>
          <div className="cashFlowApplyBar">
            <div>
              <strong>{selectedCount} đề xuất được chọn</strong>
              <span>{job.status === "applied" ? "Extraction này đã được áp dụng." : "Candidate mơ hồ hoặc xung đột phải được chỉnh sửa trước khi áp dụng."}</span>
            </div>
            {job.status === "completed" && (
              <button className="hdBtn primary" type="button" disabled={busy !== null || selectedCount === 0} onClick={apply}>
                {busy === "apply" ? "Đang áp dụng..." : "Áp dụng các mục đã chọn"}
              </button>
            )}
          </div>
        </>
      )}
    </section>
  );
}
