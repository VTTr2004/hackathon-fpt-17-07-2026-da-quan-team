import type {
  Analysis,
  AnalysisModule,
  ChatMessageItem,
  ChatResponse,
  DocumentItem,
  GeocodeResult,
  SatelliteContext,
  Startup,
  SurroundingMapData,
} from "@/types";

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
  listDocuments: (id: string) => request<DocumentItem[]>(`/startups/${id}/documents`),
  uploadDocument: (id: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return request<DocumentItem>(`/startups/${id}/documents`, { method: "POST", body: formData });
  },
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

