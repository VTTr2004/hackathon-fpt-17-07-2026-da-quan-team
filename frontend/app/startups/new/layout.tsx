"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { useAuth } from "@/lib/auth";

import { ProfileDraftProvider } from "./_components/ProfileDraftProvider";

const steps = [
  { href: "/startups/new", label: "Thông tin chung", code: "01" },
  { href: "/startups/new/business-model", label: "Business Model", code: "02" },
  { href: "/startups/new/cash-flow", label: "Cash Flow", code: "03" },
  { href: "/startups/new/surrounding-area", label: "Surrounding Area", code: "04" },
];

export default function NewStartupLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { user } = useAuth();
  if (user?.role !== "startup") {
    return <div className="hdShell"><div className="hdAlert"><span className="material-symbols-outlined">lock</span><span>Chỉ tài khoản Startup được tạo hồ sơ.</span></div></div>;
  }
  return (
    <ProfileDraftProvider>
      <div className="hdShell profileBuilderShell">
        <Link className="hdBtn" href="/" style={{ width: "fit-content", marginBottom: 18 }}>
          <span className="material-symbols-outlined">arrow_back</span>
          Danh sách hồ sơ
        </Link>
        <section className="hdPageHead">
          <div>
            <p className="hdEyebrow">Hồ sơ mới</p>
            <h1>Tạo hồ sơ startup</h1>
            <p className="hdLead">Mỗi module có một trang nhập liệu riêng và cùng đóng góp vào một hồ sơ.</p>
          </div>
          <span className="hdChip"><span className="material-symbols-outlined" style={{ fontSize: 15, marginRight: 4, verticalAlign: "-3px" }}>save</span>Bản nháp lưu trong phiên</span>
        </section>

        <div className="profileBuilderLayout">
          <nav className="surface profileBuilderNav" aria-label="Các bước tạo hồ sơ">
            {steps.map((step) => {
              const active = pathname === step.href;
              return (
                <Link className={active ? "active" : ""} href={step.href} key={step.href}>
                  <span>{step.code}</span>
                  <strong>{step.label}</strong>
                </Link>
              );
            })}
          </nav>
          <div className="profileBuilderContent">{children}</div>
        </div>
      </div>
    </ProfileDraftProvider>
  );
}
