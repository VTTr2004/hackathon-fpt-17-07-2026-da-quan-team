import type { UserRole } from "@/types";

export type DeskTab = {
  id: string;
  label: string;
  icon: string;
  roles?: UserRole[];
};

// Các tab của "Bàn thẩm định" (trang chi tiết hồ sơ). Dùng chung cho sidebar + trang detail.
export const deskTabs: DeskTab[] = [
  { id: "overview", label: "Tổng quan", icon: "dashboard" },
  { id: "business", label: "Kinh doanh", icon: "storefront", roles: ["investor"] },
  { id: "profile", label: "Hồ sơ", icon: "description", roles: ["startup"] },
  { id: "cashflow", label: "Dòng tiền", icon: "monitoring" },
  { id: "area", label: "Khu vực", icon: "map" },
  { id: "evidence", label: "Bằng chứng", icon: "inventory_2" },
  { id: "assistant", label: "Trợ lý", icon: "assistant", roles: ["startup"] },
  { id: "review", label: "Rà soát", icon: "rate_review" },
];

export function tabsForRole(role: UserRole | undefined): DeskTab[] {
  return deskTabs.filter((tab) => !tab.roles || (role && tab.roles.includes(role)));
}

export function isValidTab(id: string, role: UserRole | undefined): boolean {
  return tabsForRole(role).some((tab) => tab.id === id);
}
