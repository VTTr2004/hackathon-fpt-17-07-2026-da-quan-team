"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { tabsForRole } from "@/lib/deskTabs";

const THEME_KEY = "startup-lens-theme";
const SIDEBAR_KEY = "startup-lens-sidebar";

function MIcon({ name, className }: { name: string; className?: string }) {
  return <span className={`material-symbols-outlined${className ? ` ${className}` : ""}`} aria-hidden="true">{name}</span>;
}

type NavItem = { kind: "route" | "hash"; href: string; label: string; icon: string; active?: boolean };

export default function AppChrome({ children }: { children: React.ReactNode }) {
  const { user, loading, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const publicPage = pathname === "/login";

  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [confirmLogout, setConfirmLogout] = useState(false);
  const [workspaceItems, setWorkspaceItems] = useState<Array<{ id: string; name: string }>>([]);

  // Đồng bộ trạng thái ban đầu từ DOM (đã được inline script đặt) + localStorage.
  // Giữ giá trị mặc định khớp SSR (light/expanded) rồi cập nhật sau khi mount để tránh lệch hydrate.
  useEffect(() => {
    const domTheme = document.documentElement.dataset.theme === "dark" ? "dark" : "light";
    let nextCollapsed = false;
    try {
      nextCollapsed = localStorage.getItem(SIDEBAR_KEY) === "collapsed";
    } catch {
      /* localStorage có thể bị chặn */
    }
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setTheme(domTheme);
    setCollapsed(nextCollapsed);
  }, []);

  // Điều hướng theo phiên đăng nhập (giữ nguyên hành vi cũ).
  useEffect(() => {
    if (!loading && !user && !publicPage) router.replace("/login");
    if (!loading && user && publicPage) router.replace("/");
  }, [loading, pathname, publicPage, router, user]);

  // Nạp danh sách hồ sơ để đưa vào sidebar (điều hướng nhanh, lấp đầy như mockup).
  useEffect(() => {
    if (loading || !user || publicPage) return;
    let ignore = false;
    api
      .listStartups()
      .then((data) => { if (!ignore) setWorkspaceItems(data.map((s) => ({ id: s.id, name: s.name }))); })
      .catch(() => { /* im lặng: sidebar chỉ là điều hướng phụ */ });
    return () => { ignore = true; };
  }, [loading, user, publicPage, pathname]);

  // Theo dõi hash để đánh dấu mục section đang mở trên sidebar (trang detail).
  const [activeHash, setActiveHash] = useState("");
  useEffect(() => {
    const update = () => setActiveHash(window.location.hash || "#tab-overview");
    update();
    window.addEventListener("hashchange", update);
    return () => window.removeEventListener("hashchange", update);
  }, [pathname]);

  const closeMobile = () => setMobileOpen(false);

  function toggleTheme() {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    document.documentElement.dataset.theme = next;
    try {
      localStorage.setItem(THEME_KEY, next);
    } catch {
      /* bỏ qua nếu storage bị chặn */
    }
  }

  function toggleCollapsed() {
    setCollapsed((prev) => {
      const next = !prev;
      try {
        localStorage.setItem(SIDEBAR_KEY, next ? "collapsed" : "expanded");
      } catch {
        /* bỏ qua */
      }
      return next;
    });
  }

  if (loading || (!user && !publicPage)) {
    return (
      <main>
        <div className="pageShell">
          <p className="muted">Đang kiểm tra phiên đăng nhập...</p>
        </div>
      </main>
    );
  }

  // Trang login giữ layout riêng, không có shell/sidebar.
  if (publicPage || !user) {
    return <main>{children}</main>;
  }

  const isInvestor = user.role === "investor";
  const deskMatch = pathname.match(/^\/startups\/([^/]+)$/);
  const onDesk = Boolean(deskMatch && deskMatch[1] !== "new");

  let nav: NavItem[];
  if (onDesk) {
    // Trên "Bàn thẩm định": sidebar là các phần của hồ sơ (điều hướng bằng hash #tab-...).
    nav = [
      { kind: "route", href: "/", label: isInvestor ? "Deal room" : "Danh sách hồ sơ", icon: "arrow_back" },
      ...tabsForRole(user.role).map((t) => ({ kind: "hash" as const, href: `#tab-${t.id}`, label: t.label, icon: t.icon, active: activeHash === `#tab-${t.id}` })),
    ];
  } else {
    nav = [
      { kind: "route", href: "/", label: isInvestor ? "Bàn thẩm định" : "Hồ sơ của tôi", icon: "dashboard", active: pathname === "/" },
      ...workspaceItems.map((s) => ({
        kind: "route" as const,
        href: `/startups/${s.id}`,
        label: s.name,
        icon: isInvestor ? "storefront" : "description",
        active: pathname === `/startups/${s.id}`,
      })),
    ];
  }

  return (
    <div className={`appShell${collapsed ? " is-collapsed" : ""}${mobileOpen ? " is-mobile-open" : ""}`}>
      <aside className="appSidebar" aria-label="Không gian làm việc">
        <div className="appSidebarHead">
          <Link href="/" className="appBrand" title="Hải Đăng Khởi Nghiệp" onClick={closeMobile}>
            <span className="appBrandMark" aria-hidden="true">
              <span className="appBrandMarkImage" />
            </span>
            <span className="appBrandText">
              <strong>Hải Đăng Khởi Nghiệp</strong>
              <span>Venture Due Diligence</span>
            </span>
          </Link>
          <button
            type="button"
            className="appCollapseBtn"
            onClick={toggleCollapsed}
            title={collapsed ? "Mở rộng thanh bên" : "Thu gọn thanh bên"}
            aria-label={collapsed ? "Mở rộng thanh bên" : "Thu gọn thanh bên"}
            aria-pressed={collapsed}
          >
            <MIcon name="chevron_left" />
          </button>
        </div>

        <nav className="appNav">
          {nav.map((item) =>
            item.kind === "route" ? (
              <Link
                key={item.href}
                href={item.href}
                className={`appNavItem${item.active ? " active" : ""}`}
                title={item.label}
                aria-current={item.active ? "page" : undefined}
                onClick={closeMobile}
              >
                <span className="appNavIcon"><MIcon name={item.icon} className={item.active ? "fill-icon" : undefined} /></span>
                <span className="appNavLabel">{item.label}</span>
              </Link>
            ) : (
              <a
                key={item.href}
                href={item.href}
                className={`appNavItem${item.active ? " active" : ""}`}
                title={item.label}
                aria-current={item.active ? "page" : undefined}
                onClick={closeMobile}
              >
                <span className="appNavIcon"><MIcon name={item.icon} className={item.active ? "fill-icon" : undefined} /></span>
                <span className="appNavLabel">{item.label}</span>
              </a>
            ),
          )}
          {!onDesk && workspaceItems.length === 0 && (
            <p className="appNavHint">{isInvestor ? "Chưa có hồ sơ nào được chia sẻ với bạn." : "Tạo hồ sơ đầu tiên để bắt đầu thẩm định."}</p>
          )}
        </nav>

        <div className="appSidebarFoot">
          {!isInvestor && (
            <Link href="/startups/new" className="appNewBtn" title="Tạo hồ sơ mới" onClick={closeMobile}>
              <MIcon name="add" />
              <span className="appNavLabel">Tạo hồ sơ mới</span>
            </Link>
          )}
          <div className="appReadiness">
            <strong>{isInvestor ? "Vai trò nhà đầu tư" : "Vai trò startup"}</strong>
            <span>
              {isInvestor
                ? "Xem hồ sơ được chia sẻ, chạy phân tích và rà soát bằng chứng."
                : "Tạo và cập nhật hồ sơ, tải tài liệu và nộp bản chính thức."}
            </span>
          </div>
          <button type="button" className="appNavItem appLogoutItem" onClick={() => setConfirmLogout(true)} title="Đăng xuất">
            <span className="appNavIcon"><MIcon name="logout" /></span>
            <span className="appNavLabel">Đăng xuất</span>
          </button>
        </div>
      </aside>

      <div className="appMain">
        <header className="appTopbar">
          <button type="button" className="appMenuBtn" onClick={() => setMobileOpen((v) => !v)} aria-label="Mở thanh bên">
            <MIcon name="menu" />
          </button>

          <label className="appSearch">
            <MIcon name="search" />
            <input placeholder="Tìm hồ sơ, tài liệu, câu hỏi..." aria-label="Tìm kiếm trong không gian làm việc" />
          </label>

          <div className="appTopActions">
            <button
              type="button"
              className="appIconBtn"
              onClick={toggleTheme}
              title={theme === "dark" ? "Chuyển sang chế độ sáng" : "Chuyển sang chế độ tối"}
              aria-label={theme === "dark" ? "Chuyển sang chế độ sáng" : "Chuyển sang chế độ tối"}
            >
              <MIcon name={theme === "dark" ? "light_mode" : "dark_mode"} />
            </button>
            <div className="appUser">
              <span className="appRoleBadge">{isInvestor ? "NHÀ ĐẦU TƯ" : "STARTUP"}</span>
              <span className="appUserName">{user.full_name}</span>
            </div>
            <button type="button" className="appIconBtn" onClick={() => setConfirmLogout(true)} title="Đăng xuất" aria-label="Đăng xuất">
              <MIcon name="logout" />
            </button>
          </div>
        </header>

        <main className="appContent">{children}</main>
      </div>

      <button
        type="button"
        className="appScrim"
        aria-label="Đóng thanh bên"
        tabIndex={mobileOpen ? 0 : -1}
        onClick={closeMobile}
      />

      {confirmLogout && (
        <div className="appModalOverlay" role="dialog" aria-modal="true" aria-labelledby="logoutTitle">
          <button type="button" className="appModalScrim" aria-label="Đóng" onClick={() => setConfirmLogout(false)} />
          <div className="appModalCard">
            <div className="appModalIcon"><MIcon name="logout" /></div>
            <h2 id="logoutTitle">Đăng xuất?</h2>
            <p>Bạn sẽ cần đăng nhập lại để tiếp tục truy cập bàn thẩm định.</p>
            <div className="appModalActions">
              <button type="button" className="secondaryButton" onClick={() => setConfirmLogout(false)}>
                Ở lại
              </button>
              <button type="button" className="primaryButton" onClick={logout}>
                Đăng xuất
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
