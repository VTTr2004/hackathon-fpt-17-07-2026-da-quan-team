import type { Analysis, AnalysisModule, ChatResponse, DocumentItem, Startup } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...init?.headers,
    },
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.detail ?? `API error ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  listStartups: () => request<Startup[]>("/startups"),
  getStartup: (id: string) => request<Startup>(`/startups/${id}`),
  createStartup: (payload: {
    name: string;
    industry?: string;
    stage?: string;
    primary_location?: string;
  }) => request<Startup>("/startups", { method: "POST", body: JSON.stringify(payload) }),
  listDocuments: (id: string) => request<DocumentItem[]>(`/startups/${id}/documents`),
  uploadDocument: (id: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return request<DocumentItem>(`/startups/${id}/documents`, { method: "POST", body: formData });
  },
  listAnalyses: (id: string) => request<Analysis[]>(`/startups/${id}/analyses`),
  runAnalysis: (id: string, module: AnalysisModule) =>
    request<Analysis>(`/startups/${id}/analyses/${module}`, {
      method: "POST",
      body: JSON.stringify({ options: { use_gemini: true } }),
    }),
  chat: (id: string, question: string) =>
    request<ChatResponse>(`/startups/${id}/chat`, {
      method: "POST",
      body: JSON.stringify({ question }),
    }),
};

