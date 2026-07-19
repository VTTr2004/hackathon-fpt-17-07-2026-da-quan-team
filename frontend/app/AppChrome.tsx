"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { tabsForRole } from "@/lib/deskTabs";
import { industryOptions, stageOptions } from "@/lib/profileFields";

const THEME_KEY = "startup-lens-theme";
const SIDEBAR_KEY = "startup-lens-sidebar";

function MIcon({ name, className }: { name: string; className?: string }) {
  return <span className={`material-symbols-outlined${className ? ` ${className}` : ""}`} aria-hidden="true">{name}</span>;
}

type NavItem = { kind: "route" | "hash"; href: string; label: string; icon: string; active?: boolean; disabled?: boolean; badge?: number };
type WorkspaceItem = {
  id: string;
  name: string;
  industry: string | null;
  stage: string | null;
  primary_location: string | null;
};

export default function AppChrome({ children }: { children: React.ReactNode }) {
  const { user, loading, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const publicPage = pathname === "/login";

  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [confirmLogout, setConfirmLogout] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [createBusy, setCreateBusy] = useState(false);
  const [createError, setCreateError] = useState("");
  const [workspaceItems, setWorkspaceItems] = useState<WorkspaceItem[]>([]);
  const [pendingAccessByStartup, setPendingAccessByStartup] = useState<Record<string, number>>({});
  const [searchQuery, setSearchQuery] = useState("");
  const [searchFocused, setSearchFocused] = useState(false);

  // Tìm kiếm thật: lọc trực tiếp danh sách hồ sơ trong workspace theo tên/ngành/giai đoạn/địa điểm.
  const searchResults = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return [];
    return workspaceItems
      .filter((s) =>
        [s.name, s.industry, s.stage, s.primary_location]
          .filter((v): v is string => Boolean(v))
          .some((v) => v.toLowerCase().includes(q)),
      )
      .slice(0, 8);
  }, [searchQuery, workspaceItems]);

  useEffect(() => {
    const updatePendingAccess = (event: Event) => {
      const detail = (event as CustomEvent<{ startupId?: string; pendingCount?: number }>).detail;
      if (!detail?.startupId || typeof detail.pendingCount !== "number") return;
      setPendingAccessByStartup((current) => ({ ...current, [detail.startupId!]: detail.pendingCount! }));
    };
    window.addEventListener("startup-access-updated", updatePendingAccess);
    return () => window.removeEventListener("startup-access-updated", updatePendingAccess);
  }, []);

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
    const loadWorkspace = () => {
      api
        .listStartups()
        .then((data) => {
          if (!ignore) {
            setWorkspaceItems(data.map((s) => ({
              id: s.id,
              name: s.name,
              industry: s.industry,
              stage: s.stage,
              primary_location: s.primary_location,
            })));
          }
        })
        .catch(() => { /* im lặng: sidebar chỉ là điều hướng phụ */ });
    };
    loadWorkspace();
    window.addEventListener("startup-workspace-updated", loadWorkspace);
    return () => {
      ignore = true;
      window.removeEventListener("startup-workspace-updated", loadWorkspace);
    };
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

  function openSearchResult(id: string) {
    setSearchQuery("");
    setSearchFocused(false);
    closeMobile();
    router.push(`/startups/${id}`);
  }

  function onSearchSubmit(event: FormEvent) {
    event.preventDefault();
    if (searchResults[0]) openSearchResult(searchResults[0].id);
  }

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

  async function createStartup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const name = String(form.get("name") ?? "").trim();
    const industry = String(form.get("industry") ?? "").trim();
    const stage = String(form.get("stage") ?? "").trim();
    const primaryLocation = String(form.get("primary_location") ?? "").trim();
    if (!name || !industry || !stage || !primaryLocation) {
      setCreateError("Vui lòng nhập đủ 4 thông tin nền trước khi tiếp tục.");
      return;
    }
    setCreateBusy(true);
    setCreateError("");
    try {
      const startup = await api.createStartup({ name, industry, stage, primary_location: primaryLocation });
      setWorkspaceItems((current) => [
        { id: startup.id, name: startup.name, industry: startup.industry, stage: startup.stage, primary_location: startup.primary_location },
        ...current,
      ]);
      setCreateOpen(false);
      router.push(`/startups/${startup.id}#tab-profile`);
    } catch (reason) {
      setCreateError(reason instanceof Error ? reason.message : "Không thể tạo hồ sơ startup.");
    } finally {
      setCreateBusy(false);
    }
  }

  if (!publicPage && (loading || !user)) {
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
  const currentWorkspace = deskMatch ? workspaceItems.find((item) => item.id === deskMatch[1]) : undefined;
  const pendingAccessCount = deskMatch ? pendingAccessByStartup[deskMatch[1]] ?? 0 : 0;
  const coreProfileIncomplete = Boolean(
    onDesk && currentWorkspace && (!currentWorkspace.name.trim() || !currentWorkspace.industry || !currentWorkspace.stage || !currentWorkspace.primary_location),
  );

  let nav: NavItem[];
  if (onDesk) {
    // Trên "Bàn thẩm định": sidebar là các phần của hồ sơ (điều hướng bằng hash #tab-...).
    nav = [
      { kind: "route", href: "/", label: isInvestor ? "Deal room" : "Danh sách hồ sơ", icon: "arrow_back" },
      ...tabsForRole(user.role).map((t) => ({
        kind: "hash" as const,
        href: `#tab-${t.id}`,
        label: t.label,
        icon: t.icon,
        active: activeHash === `#tab-${t.id}`,
        disabled: coreProfileIncomplete && t.id !== "overview" && t.id !== "profile",
        badge: !isInvestor && t.id === "review" ? pendingAccessCount : undefined,
      })),
    ];
  } else {
    nav = [
      { kind: "route", href: "/", label: isInvestor ? "Bàn thẩm định" : "Hồ sơ của tôi", icon: "dashboard", active: pathname === "/" },
      ...(isInvestor ? [
        { kind: "route" as const, href: "/investor/candidates", label: "Khám phá startup", icon: "travel_explore", active: pathname === "/investor/candidates" },
        { kind: "route" as const, href: "/investor/pipeline", label: "Pipeline", icon: "view_kanban", active: pathname === "/investor/pipeline" },
        { kind: "route" as const, href: "/investor/preferences", label: "Investment thesis", icon: "tune", active: pathname === "/investor/preferences" },
      ] : []),
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
              <strong>
                <span className="brandWordA">Hải Đăng</span>{" "}
                <span className="brandWordB">Khởi Nghiệp</span>
              </strong>
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
            ) : item.disabled ? (
              <span
                key={item.href}
                className="appNavItem is-disabled"
                title="Hoàn thiện 4 thông tin nền trong tab Hồ sơ để mở tính năng này"
                aria-disabled="true"
              >
                <span className="appNavIcon"><MIcon name={item.icon} /></span>
                <span className="appNavLabel">{item.label}</span>
                {Boolean(item.badge) && <span className="appNavBadge" aria-label={`${item.badge} yêu cầu chờ duyệt`}>{item.badge}</span>}
              </span>
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
                {Boolean(item.badge) && <span className="appNavBadge" aria-label={`${item.badge} yêu cầu chờ duyệt`}>{item.badge}</span>}
              </a>
            ),
          )}
          {!onDesk && workspaceItems.length === 0 && (
            <p className="appNavHint">{isInvestor ? "Chưa có hồ sơ nào được chia sẻ với bạn." : "Tạo hồ sơ đầu tiên để bắt đầu thẩm định."}</p>
          )}
        </nav>

        <div className="appSidebarFoot">
          {!isInvestor && (
            <button
              type="button"
              className="appNewBtn"
              title="Tạo hồ sơ mới"
              onClick={() => {
                closeMobile();
                setCreateError("");
                setCreateOpen(true);
              }}
            >
              <MIcon name="add" />
              <span className="appNavLabel">Tạo hồ sơ mới</span>
            </button>
          )}
          <div className="appReadiness">
            <strong>{isInvestor ? "Vai trò nhà đầu tư" : "Vai trò startup"}</strong>
            <span>
              {isInvestor
                ? "Xem hồ sơ được chia sẻ, chạy phân tích và rà soát bằng chứng."
                : "Tạo và cập nhật hồ sơ, tải tài liệu và nộp bản chính thức."}
            </span>
          </div>
        </div>
      </aside>

      <div className="appMain">
        <header className="appTopbar">
          <button type="button" className="appMenuBtn" onClick={() => setMobileOpen((v) => !v)} aria-label="Mở thanh bên">
            <MIcon name="menu" />
          </button>

          <div className="appSearchWrap">
            <form className="appSearch" role="search" onSubmit={onSearchSubmit}>
              <MIcon name="search" />
              <input
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                onFocus={() => setSearchFocused(true)}
                onBlur={() => window.setTimeout(() => setSearchFocused(false), 120)}
                onKeyDown={(event) => {
                  if (event.key === "Escape") {
                    setSearchQuery("");
                    event.currentTarget.blur();
                  }
                }}
                placeholder="Tìm hồ sơ theo tên, ngành, giai đoạn, địa điểm..."
                aria-label="Tìm kiếm trong không gian làm việc"
                autoComplete="off"
              />
              {searchQuery ? (
                <button
                  type="button"
                  className="appSearchClear"
                  onClick={() => setSearchQuery("")}
                  aria-label="Xóa tìm kiếm"
                  tabIndex={-1}
                >
                  <MIcon name="close" />
                </button>
              ) : null}
            </form>
            {searchFocused && searchQuery.trim() ? (
              <div className="appSearchResults" role="listbox" aria-label="Kết quả tìm kiếm">
                {searchResults.length ? (
                  searchResults.map((s) => (
                    <button
                      key={s.id}
                      type="button"
                      role="option"
                      aria-selected="false"
                      className="appSearchResult"
                      onMouseDown={(event) => event.preventDefault()}
                      onClick={() => openSearchResult(s.id)}
                    >
                      <MIcon name={isInvestor ? "storefront" : "description"} />
                      <span className="appSearchResultText">
                        <strong>{s.name}</strong>
                        <small>
                          {[s.industry, s.stage, s.primary_location].filter(Boolean).join(" · ") || "Chưa có thông tin nền"}
                        </small>
                      </span>
                    </button>
                  ))
                ) : (
                  <p className="appSearchEmpty">Không tìm thấy hồ sơ khớp “{searchQuery.trim()}”.</p>
                )}
              </div>
            ) : null}
          </div>

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

      {createOpen && (
        <div className="appModalOverlay" role="dialog" aria-modal="true" aria-labelledby="createStartupTitle">
          <button type="button" className="appModalScrim" aria-label="Đóng" onClick={() => !createBusy && setCreateOpen(false)} />
          <div className="appModalCard appCreateModal">
            <div className="appModalIcon appCreateModalIcon"><MIcon name="add_business" /></div>
            <h2 id="createStartupTitle">Tạo hồ sơ startup</h2>
            <p>Nhập đủ 4 thông tin nền. Các dữ liệu chuyên sâu sẽ được bổ sung trong trang hồ sơ.</p>
            <form className="appCreateForm" onSubmit={createStartup}>
              <label>
                Tên startup
                <input name="name" required autoFocus placeholder="Ví dụ: Mộc Coffee" />
              </label>
              <label>
                Lĩnh vực
                <select name="industry" required defaultValue="">
                  <option value="" disabled>Chọn lĩnh vực</option>
                  {industryOptions.map((option) => <option key={option}>{option}</option>)}
                </select>
              </label>
              <label>
                Giai đoạn
                <select name="stage" required defaultValue="">
                  <option value="" disabled>Chọn giai đoạn</option>
                  {stageOptions.map((option) => <option key={option}>{option}</option>)}
                </select>
              </label>
              <label>
                Địa chỉ trụ sở chính
                <input name="primary_location" required placeholder="Quận 1, TP.HCM" />
              </label>
              {createError && <div className="hdAlert" role="alert"><MIcon name="error" /><span>{createError}</span></div>}
              <div className="appModalActions">
                <button type="button" className="secondaryButton" disabled={createBusy} onClick={() => setCreateOpen(false)}>
                  Hủy
                </button>
                <button type="submit" className="primaryButton" disabled={createBusy}>
                  {createBusy ? "Đang tạo..." : "Tạo và mở hồ sơ"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

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
