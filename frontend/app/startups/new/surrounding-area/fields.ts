import { quickCreateFieldGroups, quickCreateFields } from "@/lib/profileFields";

// File sở hữu của thành viên Surrounding Area. Field mới của module nên được khai báo tại đây.
export const surroundingAreaSections = quickCreateFields.filter((section) => section.id === "quick-location");
export const surroundingAreaGroups = Object.fromEntries(
  surroundingAreaSections.map((section) => [section.id, quickCreateFieldGroups[section.id] ?? []]),
);
