import { quickCreateFieldGroups, quickCreateFields } from "@/lib/profileFields";

// File sở hữu của thành viên Business Model. Có thể thêm/bớt field và group tại đây
// mà không cần sửa trang Cash Flow hoặc Surrounding Area.
export const businessModelSections = quickCreateFields.filter((section) =>
  ["quick-business", "quick-development"].includes(section.id),
);

export const businessModelGroups = Object.fromEntries(
  businessModelSections.map((section) => [section.id, quickCreateFieldGroups[section.id] ?? []]),
);
