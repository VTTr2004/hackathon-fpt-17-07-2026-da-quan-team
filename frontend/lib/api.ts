import type {
  Analysis,
  AnalysisModule,
  ChatMessageItem,
  ChatResponse,
  DocumentItem,
  GeocodeResult,
  SatelliteContext,
  Startup,
  AuthResponse,
  Completeness,
  InvestorAccess,
  StartupVersion,
  User,
  VersionDiff,
  SurroundingMapData,
} from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

const TOKEN_KEY = "startup_lens_token";

// Lưu token ở localStorage (nhớ đăng nhập) hoặc sessionStorage (chỉ phiên này).
export const tokenStore = {
  get(): string | null {
    if (typeof window === "undefined") return null;
    return window.sessionStorage.getItem(TOKEN_KEY) ?? window.localStorage.getItem(TOKEN_KEY);
  },
  set(token: string, remember: boolean) {
    if (typeof window === "undefined") return;
    if (remember) {
      window.localStorage.setItem(TOKEN_KEY, token);
      window.sessionStorage.removeItem(TOKEN_KEY);
    } else {
      window.sessionStorage.setItem(TOKEN_KEY, token);
      window.localStorage.removeItem(TOKEN_KEY);
    }
  },
  clear() {
    if (typeof window === "undefined") return;
    window.localStorage.removeItem(TOKEN_KEY);
    window.sessionStorage.removeItem(TOKEN_KEY);
  },
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = tokenStore.get();
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init?.headers,
    },
  });
  if (!response.ok) {
    if (response.status === 401 && token && typeof window !== "undefined") {
      window.localStorage.removeItem("startup_lens_token");
      window.dispatchEvent(new Event("startup-lens-auth-invalidated"));
    }
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.detail ?? `API error ${response.status}`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  register: (payload: { email: string; full_name: string; password: string; role: "startup" | "investor" }) =>
    request<AuthResponse>("/auth/register", { method: "POST", body: JSON.stringify(payload) }),
  login: (email: string, password: string) =>
    request<AuthResponse>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  me: () => request<User>("/auth/me"),
  listInvestors: () => request<User[]>("/auth/investors"),
  listStartups: () => request<Startup[]>("/startups"),
  getStartup: (id: string) => request<Startup>(`/startups/${id}`),
  createStartup: (payload: {
    name: string;
    industry?: string;
    stage?: string;
    primary_location?: string;
    facts?: Record<string, unknown>;
  }) => request<Startup>("/startups", { method: "POST", body: JSON.stringify(payload) }),
  updateStartup: (
    id: string,
    payload: Partial<{
      name: string;
      industry: string | null;
      stage: string | null;
      primary_location: string | null;
      facts: Record<string, unknown>;
    }>,
  ) => request<Startup>(`/startups/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  completeness: (id: string) => request<Completeness>(`/startups/${id}/completeness`),
  submitStartup: (id: string) => request<StartupVersion>(`/startups/${id}/submit`, { method: "POST" }),
  createNextDraft: (id: string) => request<Startup>(`/startups/${id}/draft`, { method: "POST" }),
  listVersions: (id: string) => request<StartupVersion[]>(`/startups/${id}/versions`),
  compareVersions: (id: string, fromVersion: number, toVersion: number) =>
    request<VersionDiff>(`/startups/${id}/versions/diff?from_version=${fromVersion}&to_version=${toVersion}`),
  listAccess: (id: string) => request<InvestorAccess[]>(`/startups/${id}/access`),
  grantAccess: (id: string, investorId: string) =>
    request<InvestorAccess>(`/startups/${id}/access`, {
      method: "POST",
      body: JSON.stringify({ investor_id: investorId }),
    }),
  revokeAccess: (id: string, investorId: string) =>
    request<void>(`/startups/${id}/access/${investorId}`, { method: "DELETE" }),
  listDocuments: (id: string) => request<DocumentItem[]>(`/startups/${id}/documents`),
  uploadDocument: (id: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return request<DocumentItem>(`/startups/${id}/documents`, { method: "POST", body: formData });
  },
  updateDocumentVisibility: (id: string, documentId: string, visibility: string) =>
    request<DocumentItem>(`/startups/${id}/documents/${documentId}`, {
      method: "PATCH",
      body: JSON.stringify({ visibility }),
    }),
  listAnalyses: (id: string) => request<Analysis[]>(`/startups/${id}/analyses`),
  runAnalysis: (id: string, module: AnalysisModule, options: Record<string, unknown> = { use_gemini: true }) =>
    request<Analysis>(`/startups/${id}/analyses/${module}`, {
      method: "POST",
      body: JSON.stringify({ options }),
    }),
  chat: (id: string, question: string) =>
    request<ChatResponse>(`/startups/${id}/chat`, {
      method: "POST",
      body: JSON.stringify({ question }),
    }),
  chatHistory: (id: string) => request<ChatMessageItem[]>(`/startups/${id}/chat/history`),

  // --- Surrounding-area module ---------------------------------------------
  geocode: (address: string) =>
    request<GeocodeResult>("/surrounding/geocode", {
      method: "POST",
      body: JSON.stringify({ address }),
    }),
  surroundingMap: (lat: number, lon: number, industry?: string, radiusM?: number) => {
    const params = new URLSearchParams({ lat: String(lat), lon: String(lon) });
    if (industry) params.set("industry", industry);
    if (radiusM) params.set("radius_m", String(radiusM));
    return request<SurroundingMapData>(`/surrounding/map?${params.toString()}`);
  },
  satelliteContext: (lat: number, lon: number, radiusM?: number) => {
    const params = new URLSearchParams({ lat: String(lat), lon: String(lon) });
    if (radiusM) params.set("radius_m", String(radiusM));
    return request<SatelliteContext>(`/surrounding/satellite?${params.toString()}`);
  },
  analyzeSurrounding: (id: string, options: Record<string, unknown>) =>
    request<Analysis>(`/startups/${id}/analyses/surrounding_area`, {
      method: "POST",
      body: JSON.stringify({ options }),
    }),
};

