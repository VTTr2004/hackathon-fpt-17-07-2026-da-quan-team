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
    <div className="pageShell">
      <header className="chatPageHeader">
        <Link href={`/startups/${id}`} className="muted">
          ← Về hồ sơ
        </Link>
        <h1>Chat tra cứu tài liệu</h1>
        <p className="muted">{startup ? startup.name : "Đang tải..."}</p>
      </header>
      <section className="surface chatPagePanel">
        <DocumentChat startupId={id} />
      </section>
    </div>
  );
}
