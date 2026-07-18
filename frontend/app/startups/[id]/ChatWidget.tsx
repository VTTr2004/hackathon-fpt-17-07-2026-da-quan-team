"use client";

import { useState } from "react";

import DocumentChat from "./DocumentChat";

export default function ChatWidget({ startupId }: { startupId: string }) {
  const [open, setOpen] = useState(false);

  return (
    <>
      {open ? (
        <div className="chatWindow" role="dialog" aria-label="Document Copilot">
          <div className="chatWindowHead">
            <div>
              <p className="eyebrow">DOCUMENT COPILOT</p>
              <strong>Hỏi tài liệu</strong>
            </div>
            <button
              type="button"
              className="chatWindowClose"
              onClick={() => setOpen(false)}
              aria-label="Đóng chat"
            >
              ×
            </button>
          </div>
          <div className="chatWindowBody">
            <DocumentChat startupId={startupId} />
          </div>
        </div>
      ) : null}
      <button
        type="button"
        className="chatBubble"
        onClick={() => setOpen((value) => !value)}
        aria-label={open ? "Đóng chat tài liệu" : "Mở chat tài liệu"}
      >
        {open ? "×" : "💬"}
      </button>
    </>
  );
}
