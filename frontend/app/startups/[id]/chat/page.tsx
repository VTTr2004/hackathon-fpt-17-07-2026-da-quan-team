"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";

import DocumentChat from "../DocumentChat";
import { api } from "@/lib/api";
import type { Startup } from "@/types";

export default function StartupChatPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [startup, setStartup] = useState<Startup | null>(null);

  useEffect(() => {
    let active = true;
    api
      .getStartup(id)
      .then((data) => active && setStartup(data))
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [id]);

  return (
    <div className="hdShell">
      <Link href={`/startups/${id}`} className="hdBtn" style={{ width: "fit-content", marginBottom: 18 }}>
        <span className="material-symbols-outlined">arrow_back</span>
        Về hồ sơ
      </Link>
      <header className="hdPageHead">
        <div>
          <p className="hdEyebrow">Trợ lý tài liệu</p>
          <h1>Hỏi đáp tài liệu</h1>
          <p className="hdLead">{startup ? startup.name : "Đang tải..."} · Trả lời chỉ dựa trên tài liệu đã tải lên, có trích dẫn nguồn.</p>
        </div>
      </header>
      <section className="hdCard chatPagePanel">
        <DocumentChat startupId={id} />
      </section>
    </div>
  );
}
