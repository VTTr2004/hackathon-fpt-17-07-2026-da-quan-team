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
    return <div className="pageShell"><div className="alert">Chỉ tài khoản Startup được tạo hồ sơ.</div></div>;
  }
  return (
    <ProfileDraftProvider>
      <div className="pageShell profileBuilderShell">
        <Link className="backLink" href="/">
          ← Quay lại danh sách hồ sơ
        </Link>
        <section className="pageHeader profileBuilderHeader">
          <div>
            <p className="eyebrow">NEW PROFILE</p>
            <h1>Tạo hồ sơ startup</h1>
            <p className="pageLead">Mỗi module sở hữu một trang nhập liệu riêng và cùng đóng góp vào một hồ sơ.</p>
          </div>
          <span className="systemBadge">Bản nháp lưu trong phiên làm việc</span>
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
