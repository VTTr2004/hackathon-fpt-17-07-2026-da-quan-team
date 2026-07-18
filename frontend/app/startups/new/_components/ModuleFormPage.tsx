"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, ReactNode } from "react";

import { formatProfileValue, readProfileField } from "@/lib/profileFields";
import type { ProfileField, ProfileFieldGroup, ProfileSection } from "@/lib/profileFields";

import { useProfileDraft } from "./ProfileDraftProvider";

function FieldInput({ field, value }: { field: ProfileField; value: unknown }) {
  const defaultValue = formatProfileValue(field, value);
  return (
    <label className={field.type === "textarea" ? "wideField" : undefined}>
      <span>{field.label}</span>
      {field.type === "textarea" ? (
        <textarea name={field.key} rows={field.rows ?? 3} placeholder={field.placeholder} defaultValue={defaultValue} />
      ) : field.type === "select" ? (
        <select name={field.key} defaultValue={defaultValue}>
          <option value="">Chọn</option>
          {field.options?.map((option) => (
            <option key={option}>{option}</option>
          ))}
        </select>
      ) : (
        <input
          name={field.key}
          inputMode={field.key === "variable_cost_ratio" ? "decimal" : field.type === "number" ? "numeric" : undefined}
          type={field.type === "date" ? "date" : "text"}
          placeholder={field.placeholder}
          defaultValue={defaultValue}
        />
      )}
      {field.helper && <small className="fieldHelper">{field.helper}</small>}
    </label>
  );
}

function TopicGroups({
  section,
  groups,
  facts,
}: {
  section: ProfileSection;
  groups: ProfileFieldGroup[];
  facts: Record<string, unknown>;
}) {
  const fieldMap = new Map(section.fields.map((field) => [field.key, field]));
  return (
    <div className="topicGroupList">
      {groups.map((group) => {
        const fields = group.fieldKeys
          .map((key) => fieldMap.get(key))
          .filter((field): field is ProfileField => Boolean(field));
        if (!fields.length) return null;
        return (
          <section className="topicGroup" key={group.id}>
            <div className="topicGroupHeader">
              <strong>{group.title}</strong>
              {group.description && <p>{group.description}</p>}
            </div>
            <div className="factGrid">
              {fields.map((field) => (
                <FieldInput field={field} value={facts[field.key]} key={field.key} />
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}

export function ModuleFormPage({
  eyebrow,
  title,
  description,
  sections,
  groupsBySection,
  previousHref,
  nextHref,
  nextLabel = "Lưu và tiếp tục",
  beforeSections,
}: {
  eyebrow: string;
  title: string;
  description: string;
  sections: ProfileSection[];
  groupsBySection: Record<string, ProfileFieldGroup[]>;
  previousHref: string;
  nextHref: string;
  nextLabel?: string;
  beforeSections?: ReactNode;
}) {
  const router = useRouter();
  const { draft, ready, saveModuleFacts } = useProfileDraft();
  const allFields = sections.flatMap((section) => section.fields);

  function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const values: Record<string, unknown> = {};
    for (const field of allFields) {
      const value = readProfileField(form, field);
      if (value !== undefined) values[field.key] = value;
    }
    saveModuleFacts(
      allFields.map((field) => field.key),
      values,
    );
    router.push(nextHref);
  }

  if (!ready) return <div className="surface emptyState">Đang tải bản nháp hồ sơ...</div>;

  return (
    <form className="moduleProfilePage" onSubmit={save}>
      <section className="surface moduleProfileIntro">
        <p className="eyebrow">{eyebrow}</p>
        <h2>{title}</h2>
        <p>{description}</p>
      </section>

      {beforeSections}

      {sections.map((section) => (
        <section className="surface moduleOwnedSection" key={section.id}>
          <div className="factSectionHeader">
            <div>
              <p className="eyebrow">{section.eyebrow}</p>
              <h2>{section.title}</h2>
            </div>
            <p>{section.description}</p>
          </div>
          <TopicGroups section={section} groups={groupsBySection[section.id] ?? []} facts={draft.facts} />
        </section>
      ))}

      <div className="profileSubmitBar moduleSubmitBar">
        <Link className="secondaryButton" href={previousHref}>
          Quay lại
        </Link>
        <button className="primaryButton">{nextLabel}</button>
      </div>
    </form>
  );
}
