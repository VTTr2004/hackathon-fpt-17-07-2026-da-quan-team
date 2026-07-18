"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "@/lib/auth";

export default function AppChrome({ children }: { children: React.ReactNode }) {
  const { user, loading, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const publicPage = pathname === "/login";

  useEffect(() => {
    if (!loading && !user && !publicPage) router.replace("/login");
    if (!loading && user && publicPage) router.replace("/");
  }, [loading, pathname, publicPage, router, user]);

  if (loading || (!user && !publicPage)) {
    return <main><div className="pageShell"><p className="muted">Đang kiểm tra phiên đăng nhập...</p></div></main>;
  }

  return (
    <>
      <header className="topbar">
        <Link href="/" className="brand">
          <span className="brandMark">SL</span>
          <span>Startup Lens</span>
        </Link>
        {user ? (
          <div className="sessionBar">
            <span className="roleBadge">{user.role === "startup" ? "STARTUP" : "NHÀ ĐẦU TƯ"}</span>
            <span>{user.full_name}</span>
            <button className="secondaryButton compactButton" onClick={logout}>Đăng xuất</button>
          </div>
        ) : <span className="providerBadge">Phân quyền an toàn</span>}
      </header>
      <main>{children}</main>
    </>
  );
}
