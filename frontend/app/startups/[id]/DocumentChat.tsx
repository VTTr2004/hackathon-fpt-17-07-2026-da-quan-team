"use client";

import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";

import { api } from "@/lib/api";
import type { ChatMessageItem, Citation } from "@/types";

const SUGGESTED = [
  "Tổng doanh thu thuần 3 tháng là bao nhiêu?",
  "Doanh thu thuần tháng 5/2026 là bao nhiêu?",
  "Số dư cuối kỳ trong sổ thu chi là bao nhiêu?",
  "Giá bán một ly cà phê sữa là bao nhiêu?",
  "Nhà cung cấp bao bì là đơn vị nào?",
];

type ChatTurn = ChatMessageItem & {
  pending?: boolean;
  error?: boolean;
  retrieval?: string;
  provider?: string;
  grounded?: boolean;
};

function CitationList({ citations }: { citations: Citation[] }) {
  if (!citations.length) return null;
  return (
    <div className="dcCitations">
      {citations.map((citation, index) => (
        <details key={`${citation.document_id}-${index}`} className="dcCitation">
          <summary>
            <span className="dcCitationIndex">[{index + 1}]</span> {citation.filename}
            {citation.locator ? <span className="dcCitationLoc"> · {citation.locator}</span> : null}
          </summary>
          <blockquote>{citation.excerpt}</blockquote>
        </details>
      ))}
    </div>
  );
}

export default function DocumentChat({ startupId }: { startupId: string }) {
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [question, setQuestion] = useState("");
  const [sending, setSending] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let active = true;
    api
      .chatHistory(startupId)
      .then((history) => {
        if (active) setTurns(history.map((message) => ({ ...message })));
      })
      .catch(() => {
        /* no history yet is fine */
      })
      .finally(() => active && setLoadingHistory(false));
    return () => {
      active = false;
    };
  }, [startupId]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [turns]);

  async function send(text: string) {
    const trimmed = text.trim();
    if (!trimmed || sending) return;
    setQuestion("");
    setSending(true);
    const now = new Date().toISOString();
    setTurns((prev) => [
      ...prev,
      { role: "user", content: trimmed, citations: [], created_at: now },
      { role: "assistant", content: "", citations: [], created_at: now, pending: true },
    ]);
    try {
      const response = await api.chat(startupId, trimmed);
      const meta = response.metadata ?? {};
      setTurns((prev) => {
        const next = [...prev];
        next[next.length - 1] = {
          role: "assistant",
          content: response.answer,
          citations: response.citations,
          created_at: new Date().toISOString(),
          grounded: response.grounded,
          retrieval: typeof meta.retrieval === "string" ? meta.retrieval : undefined,
          provider: typeof meta.provider === "string" ? meta.provider : undefined,
        };
        return next;
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Không thể trả lời";
      setTurns((prev) => {
        const next = [...prev];
        next[next.length - 1] = {
          role: "assistant",
          content: `Lỗi: ${message}`,
          citations: [],
          created_at: new Date().toISOString(),
          error: true,
        };
        return next;
      });
    } finally {
      setSending(false);
    }
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void send(question);
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void send(question);
    }
  }

  const empty = !turns.length && !loadingHistory;

  return (
    <div className="dcRoot">
      <div className="dcMessages" ref={scrollRef}>
        {loadingHistory ? <p className="muted dcHint">Đang tải hội thoại...</p> : null}
        {empty ? (
          <div className="dcEmpty">
            <p className="eyebrow">DOCUMENT COPILOT</p>
            <h3>Hỏi đáp tài liệu của hồ sơ</h3>
            <p className="muted">
              Câu trả lời chỉ dựa trên tài liệu đã nạp cho hồ sơ này, kèm trích dẫn nguồn (sheet / dòng / trang).
            </p>
            <div className="dcChips">
              {SUGGESTED.map((item) => (
                <button key={item} type="button" onClick={() => void send(item)}>
                  {item}
                </button>
              ))}
            </div>
          </div>
        ) : null}

        {turns.map((turn, index) => (
          <div key={index} className={`dcTurn dcTurn-${turn.role}`}>
            <div className={`dcBubble${turn.error ? " dcBubble-error" : ""}`}>
              {turn.pending ? (
                <span className="dcTyping">
                  <i />
                  <i />
                  <i />
                </span>
              ) : (
                <p className="dcText">{turn.content}</p>
              )}
              {turn.role === "assistant" && !turn.pending ? (
                <>
                  <CitationList citations={turn.citations} />
                  {turn.retrieval ? (
                    <p className="dcMeta">
                      {turn.grounded ? "Có dẫn nguồn" : "Chưa đủ dữ liệu"} · retrieval: {turn.retrieval}
                      {turn.provider ? ` · ${turn.provider}` : ""}
                    </p>
                  ) : null}
                </>
              ) : null}
            </div>
          </div>
        ))}
      </div>

      <form className="dcForm" onSubmit={onSubmit}>
        <textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Nhập câu hỏi về tài liệu... (Enter để gửi, Shift+Enter xuống dòng)"
          rows={2}
        />
        <button className="primaryButton" disabled={sending || !question.trim()}>
          {sending ? "Đang đọc..." : "Gửi"}
        </button>
      </form>
    </div>
  );
}
