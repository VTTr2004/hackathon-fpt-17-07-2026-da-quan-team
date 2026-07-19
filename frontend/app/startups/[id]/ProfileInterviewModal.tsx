"use client";

import { FormEvent, useMemo, useState } from "react";

import { api } from "@/lib/api";
import type { Completeness, ProfileInterviewSession, Startup } from "@/types";

type Props = {
  startupId: string;
  completeness: Completeness;
  onClose: () => void;
  onManual: (tab: "profile" | "cashflow" | "evidence") => void;
  onApplied: (startup: Startup) => Promise<void>;
};

function MIcon({ name }: { name: string }) {
  return <span className="material-symbols-outlined" aria-hidden="true">{name}</span>;
}

function editableValue(value: unknown): string {
  if (Array.isArray(value)) return value.map(String).join("\n");
  return value == null ? "" : String(value);
}

export default function ProfileInterviewModal({ startupId, completeness, onClose, onManual, onApplied }: Props) {
  const [session, setSession] = useState<ProfileInterviewSession | null>(null);
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState<"start" | "answer" | "apply" | null>(null);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [edits, setEdits] = useState<Record<string, string>>({});

  const completedRequired = session
    ? session.required_field_keys.length - session.pending_required_keys.length
    : 0;
  const grouped = useMemo(() => ({
    required: session?.proposals.filter((item) => item.priority === "required") ?? [],
    major: session?.proposals.filter((item) => item.priority === "major") ?? [],
    optional: session?.proposals.filter((item) => item.priority === "optional") ?? [],
  }), [session]);

  function loadSession(next: ProfileInterviewSession) {
    setSession(next);
    if (next.status !== "review") return;
    setSelected(new Set(next.proposals.map((item) => item.field_key)));
    setEdits(Object.fromEntries(next.proposals.map((item) => [item.field_key, editableValue(item.proposed_value)])));
  }

  async function startInterview() {
    setBusy("start"); setError("");
    try { loadSession(await api.createProfileInterview(startupId)); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Không thể bắt đầu phỏng vấn AI"); }
    finally { setBusy(null); }
  }

  async function sendAnswer(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const clean = answer.trim();
    if (!session || !clean) return;
    setBusy("answer"); setError("");
    try {
      loadSession(await api.answerProfileInterview(startupId, session.id, clean));
      setAnswer("");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "AI chưa thể xử lý câu trả lời"); }
    finally { setBusy(null); }
  }

  function toggle(fieldKey: string) {
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(fieldKey)) next.delete(fieldKey); else next.add(fieldKey);
      return next;
    });
  }

  async function apply() {
    if (!session) return;
    const decisions = session.proposals.map((proposal) => {
      if (!selected.has(proposal.field_key)) return { field_key: proposal.field_key, action: "reject" as const };
      const edited = edits[proposal.field_key]?.trim() ?? "";
      const original = editableValue(proposal.proposed_value);
      return edited === original
        ? { field_key: proposal.field_key, action: "accept" as const }
        : { field_key: proposal.field_key, action: "edit" as const, value: edited };
    });
    setBusy("apply"); setError("");
    try {
      const startup = await api.confirmProfileInterview(startupId, session.id, decisions);
      await onApplied(startup);
      onClose();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Không thể áp dụng đề xuất"); }
    finally { setBusy(null); }
  }

  return (
    <div className="appModalOverlay profileInterviewOverlay" role="dialog" aria-modal="true" aria-labelledby="profileInterviewTitle">
      <button className="appModalScrim" type="button" aria-label="Đóng" onClick={() => !busy && onClose()} />
      <div className="appModalCard profileInterviewModal">
        <div className="profileInterviewHeader">
          <div>
            <p className="hdEyebrow">AI PROFILE ASSISTANT</p>
            <h2 id="profileInterviewTitle">Hoàn thiện hồ sơ trước khi nộp</h2>
          </div>
          <button className="appIconBtn" type="button" aria-label="Đóng" disabled={Boolean(busy)} onClick={onClose}><MIcon name="close" /></button>
        </div>

        {error && <div className="hdAlert" role="alert"><MIcon name="error" /><span>{error}</span></div>}

        {!session && (
          <div className="profileInterviewChoice">
            <p>Hồ sơ còn <strong>{completeness.missing_fields.length} trường dữ liệu</strong> và <strong>{completeness.missing_documents.length} yêu cầu tài liệu</strong> cần xử lý.</p>
            <div className="profileInterviewChoiceGrid">
              <button type="button" className="profileInterviewChoiceCard" onClick={() => onManual(completeness.missing_documents.length ? "evidence" : completeness.format_errors.length ? "cashflow" : "profile")}>
                <MIcon name="edit_note" /><strong>Tự điền</strong><span>Mở biểu mẫu hoặc tải tài liệu và tự bổ sung các mục còn thiếu.</span>
              </button>
              <button type="button" className="profileInterviewChoiceCard ai" disabled={!completeness.missing_fields.length || busy === "start"} onClick={() => void startInterview()}>
                <MIcon name="auto_awesome" /><strong>Phỏng vấn cùng AI</strong><span>AI chỉ hỏi các trường **; câu trả lời đủ rõ có thể đề xuất thêm trường * và trường thường.</span>
              </button>
            </div>
            {!completeness.missing_fields.length && <p className="muted">Không còn trường ** cần phỏng vấn. Hãy bổ sung tài liệu để hoàn tất hồ sơ.</p>}
          </div>
        )}

        {session?.status === "active" && (
          <div className="profileInterviewConversation">
            <div className="profileInterviewProgress">
              <span>Trường ** đã có dữ liệu</span><strong>{completedRequired}/{session.required_field_keys.length}</strong>
              <div><i style={{ width: `${Math.round(completedRequired / session.required_field_keys.length * 100)}%` }} /></div>
            </div>
            <div className="profileInterviewTranscript">
              {session.transcript.map((turn, index) => <div className={`profileInterviewTurn ${turn.role}`} key={`${turn.role}-${index}`}><span>{turn.content}</span></div>)}
            </div>
            <form className="profileInterviewAnswer" onSubmit={sendAnswer}>
              <textarea value={answer} onChange={(event) => setAnswer(event.target.value)} rows={4} placeholder="Trả lời bằng thông tin thực tế của startup…" disabled={busy === "answer"} autoFocus />
              <button className="hdBtn primary" disabled={!answer.trim() || busy === "answer"}><MIcon name="send" />{busy === "answer" ? "AI đang phân tích…" : "Gửi câu trả lời"}</button>
            </form>
          </div>
        )}

        {session?.status === "review" && (
          <div className="profileInterviewReview">
            <div className="cashFlowAlert info">Đã đủ dữ liệu ** từ phiên phỏng vấn. Nhóm * và Thông tin bổ sung không bắt buộc; AI chỉ đề xuất khi câu trả lời có đủ thông tin và bạn có thể bỏ chọn trước khi áp dụng.</div>
            {(["required", "major", "optional"] as const).map((priority) => grouped[priority].length > 0 && (
              <section className="profileInterviewProposalGroup" key={priority}>
                <h3>{priority === "required" ? "Bắt buộc **" : priority === "major" ? "Điểm cộng lớn *" : "Thông tin bổ sung"}</h3>
                {grouped[priority].map((proposal) => (
                  <label className="profileInterviewProposal" key={proposal.field_key}>
                    <input type="checkbox" checked={selected.has(proposal.field_key)} onChange={() => toggle(proposal.field_key)} />
                    <span>
                      <strong>{proposal.label}<em>{Math.round(proposal.confidence * 100)}%</em></strong>
                      {proposal.value_type === "text" || proposal.value_type === "list"
                        ? <textarea rows={proposal.value_type === "list" ? 3 : 2} value={edits[proposal.field_key] ?? ""} onChange={(event) => setEdits((current) => ({ ...current, [proposal.field_key]: event.target.value }))} />
                        : <input value={edits[proposal.field_key] ?? ""} onChange={(event) => setEdits((current) => ({ ...current, [proposal.field_key]: event.target.value }))} />}
                      <small>Nguồn: “{proposal.source_quote}”</small>
                    </span>
                  </label>
                ))}
              </section>
            ))}
            <div className="profileInterviewFooter">
              <span>{selected.size} đề xuất sẽ được áp dụng. AI không tự nộp hoặc khóa phiên bản.</span>
              <button className="hdBtn primary" type="button" disabled={!selected.size || busy === "apply"} onClick={() => void apply()}><MIcon name="check" />{busy === "apply" ? "Đang áp dụng…" : "Áp dụng vào hồ sơ"}</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
