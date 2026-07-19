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
  InvestorPreference,
  Candidate,
  PipelineItem,
  ProfileExtractionJob,
  ProfileInterviewSession,
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
  deleteStartup: (id: string) => request<void>(`/startups/${id}`, { method: "DELETE" }),
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
  updateDiscovery: (id: string, discoverable: boolean, publicSummary?: Record<string, boolean>) =>
    request<Startup>(`/startups/${id}/discovery`, {
      method: "PATCH",
      body: JSON.stringify({ discoverable, public_summary: publicSummary }),
    }),
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
  approveAccess: (id: string, investorId: string) =>
    request<InvestorAccess>(`/startups/${id}/access/${investorId}/approve`, { method: "POST" }),
  rejectAccess: (id: string, investorId: string) =>
    request<InvestorAccess>(`/startups/${id}/access/${investorId}/reject`, { method: "POST" }),
  requestAccess: (id: string, reason?: string) =>
    request<InvestorAccess>(`/startups/${id}/access-request`, {
      method: "POST",
      body: JSON.stringify({ reason: reason || null }),
    }),
  getInvestorPreferences: () => request<InvestorPreference>("/investor/preferences"),
  updateInvestorPreferences: (payload: Partial<InvestorPreference>) =>
    request<InvestorPreference>("/investor/preferences", { method: "PATCH", body: JSON.stringify(payload) }),
  generateMatches: () => request<Candidate[]>("/investor/matches", { method: "POST" }),
  listCandidates: (params?: URLSearchParams) =>
    request<Candidate[]>(`/investor/candidates${params?.size ? `?${params.toString()}` : ""}`),
  compareCandidates: (startupIds: string[]) =>
    request<Candidate[]>("/investor/compare", { method: "POST", body: JSON.stringify({ startup_ids: startupIds }) }),
  shortlistCandidate: (id: string) =>
    request<PipelineItem>(`/investor/candidates/${id}/shortlist`, { method: "POST" }),
  listPipeline: () => request<PipelineItem[]>("/investor/pipeline"),
  updatePipeline: (id: string, status: PipelineItem["status"], note?: string | null) =>
    request<PipelineItem>(`/investor/pipeline/${id}`, {
      method: "PATCH", body: JSON.stringify({ status, note: note ?? null }),
    }),
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
  deleteDocument: (id: string, documentId: string) =>
    request<void>(`/startups/${id}/documents/${documentId}`, { method: "DELETE" }),
  listExtractions: (id: string) => request<ProfileExtractionJob[]>(`/startups/${id}/extractions`),
  createExtraction: (id: string, documentIds: string[], fieldKeys: string[] = []) =>
    request<ProfileExtractionJob>(`/startups/${id}/extractions`, {
      method: "POST",
      body: JSON.stringify({ document_ids: documentIds, field_keys: fieldKeys }),
    }),
  getExtraction: (id: string, extractionId: string) =>
    request<ProfileExtractionJob>(`/startups/${id}/extractions/${extractionId}`),
  confirmExtraction: (
    id: string,
    extractionId: string,
    decisions: Array<{ candidate_id: string; action: "accept" | "edit" | "reject"; value?: unknown }>,
  ) =>
    request<Startup>(`/startups/${id}/extractions/${extractionId}/confirm`, {
      method: "POST",
      body: JSON.stringify({ decisions }),
    }),
  createProfileInterview: (id: string) =>
    request<ProfileInterviewSession>(`/startups/${id}/profile-interviews`, { method: "POST" }),
  answerProfileInterview: (id: string, interviewId: string, answer: string) =>
    request<ProfileInterviewSession>(`/startups/${id}/profile-interviews/${interviewId}/answer`, {
      method: "POST",
      body: JSON.stringify({ answer }),
    }),
  confirmProfileInterview: (
    id: string,
    interviewId: string,
    decisions: Array<{ field_key: string; action: "accept" | "edit" | "reject"; value?: unknown }>,
  ) => request<Startup>(`/startups/${id}/profile-interviews/${interviewId}/confirm`, {
    method: "POST",
    body: JSON.stringify({ decisions }),
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

