import { quickCreateFieldGroups, quickCreateFields } from "@/lib/profileFields";

// File sở hữu của thành viên Cash Flow. Field mới của module nên được khai báo tại đây.
export const cashFlowSections = quickCreateFields.filter((section) => section.id === "quick-finance");
export const cashFlowGroups = Object.fromEntries(
  cashFlowSections.map((section) => [section.id, quickCreateFieldGroups[section.id] ?? []]),
);
