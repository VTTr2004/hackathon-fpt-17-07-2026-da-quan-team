"use client";

import { createContext, ReactNode, useContext, useEffect, useMemo, useState } from "react";

export type ProfileIdentityDraft = {
  name: string;
  industry: string;
  stage: string;
  location: string;
};

type ProfileDraft = {
  identity: ProfileIdentityDraft;
  facts: Record<string, unknown>;
};

type ProfileDraftContextValue = {
  draft: ProfileDraft;
  ready: boolean;
  updateIdentity: (patch: Partial<ProfileIdentityDraft>) => void;
  saveModuleFacts: (ownedKeys: string[], values: Record<string, unknown>) => void;
  clearDraft: () => void;
};

const STORAGE_KEY = "startup-lens:new-profile-draft:v1";
const emptyDraft: ProfileDraft = {
  identity: { name: "", industry: "", stage: "", location: "" },
  facts: {},
};

const ProfileDraftContext = createContext<ProfileDraftContextValue | null>(null);

export function ProfileDraftProvider({ children }: { children: ReactNode }) {
  const [draft, setDraft] = useState<ProfileDraft>(emptyDraft);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;
    queueMicrotask(() => {
      if (cancelled) return;
      try {
        const stored = window.sessionStorage.getItem(STORAGE_KEY);
        if (stored) setDraft(JSON.parse(stored) as ProfileDraft);
      } catch {
        window.sessionStorage.removeItem(STORAGE_KEY);
      } finally {
        setReady(true);
      }
    });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (ready) window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(draft));
  }, [draft, ready]);

  const value = useMemo<ProfileDraftContextValue>(
    () => ({
      draft,
      ready,
      updateIdentity: (patch) => {
        setDraft((current) => ({
          ...current,
          identity: { ...current.identity, ...patch },
        }));
      },
      saveModuleFacts: (ownedKeys, values) => {
        setDraft((current) => {
          const nextFacts = { ...current.facts };
          for (const key of ownedKeys) delete nextFacts[key];
          return { ...current, facts: { ...nextFacts, ...values } };
        });
      },
      clearDraft: () => {
        window.sessionStorage.removeItem(STORAGE_KEY);
        setDraft(emptyDraft);
      },
    }),
    [draft, ready],
  );

  return <ProfileDraftContext.Provider value={value}>{children}</ProfileDraftContext.Provider>;
}

export function useProfileDraft() {
  const context = useContext(ProfileDraftContext);
  if (!context) throw new Error("useProfileDraft must be used inside ProfileDraftProvider");
  return context;
}
