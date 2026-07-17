export type Startup = {
  id: string;
  name: string;
  industry: string | null;
  stage: string | null;
  primary_location: string | null;
  facts: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type DocumentItem = {
  id: string;
  startup_id: string;
  filename: string;
  content_type: string | null;
  status: string;
  created_at: string;
};

export type AnalysisModule = "business_model" | "cash_flow" | "surrounding_area";

export type Analysis = {
  id: string;
  startup_id: string;
  module: AnalysisModule;
  version: string;
  status: string;
  score: number | null;
  summary: string;
  report: ModuleReport;
  created_at: string;
};

export type Finding = {
  title: string;
  detail: string;
  evidence_ids: string[];
  confidence: string;
};

export type Evidence = {
  evidence_id: string;
  source_type: string;
  title: string;
  publisher?: string | null;
  url?: string | null;
  accessed_at?: string | null;
  reliability?: string;
  notes?: string | null;
};

export type ToolCall = {
  name: string;
  version: string;
  input?: Record<string, unknown>;
  output?: Record<string, unknown>;
  warnings?: string[];
};

export type ModuleReport = {
  status?: string;
  score?: number | null;
  summary?: string;
  findings?: Finding[];
  risks?: string[];
  missing_data?: string[];
  assumptions?: string[];
  recommended_questions?: string[];
  evidence?: Evidence[];
  methodology?: string[];
  tool_calls?: ToolCall[];
  details?: {
    verdicts?: { claims?: ClaimVerdict[]; overall_summary?: string };
    coverage?: {
      tier?: string;
      density_1km?: number;
      coverage_ratio?: number;
      warnings?: string[];
      can_assess_saturation?: boolean;
    };
    metrics?: Record<string, unknown>;
    map?: SurroundingMapData;
    places_enrichment?: PlacesEnrichment;
    satellite_context?: SatelliteContext | null;
    [key: string]: unknown;
  };
};

// --- Surrounding-area module ------------------------------------------------

export type GeocodeCandidate = {
  lat: number;
  lon: number;
  display_name: string;
  provider: string;
  confidence: string;
};

export type GeocodeResult = {
  query: string;
  provider: string;
  needs_confirmation: boolean;
  candidates: GeocodeCandidate[];
  warnings: string[];
};

export type MapPoi = {
  name: string | null;
  category?: string;
  category_key?: string;
  lat: number;
  lon: number;
  distance_m: number;
  is_chain?: boolean;
  source?: string;
  source_id?: string;
  position_quality?: "point" | "polygon_centroid";
  maps_match_status?: "unverified_google_maps" | "verified_google_maps";
  google_maps_url?: string;
};

export type SurroundingMapData = {
  center: { lat: number; lon: number };
  eateries: MapPoi[];
  residential: MapPoi[];
  competitors: MapPoi[];
};

export type SatelliteScene = {
  id: string;
  collection: string;
  datetime: string | null;
  cloud_cover: number | null;
  gsd_m: number | null;
  thumbnail_url: string | null;
  visual_url: string | null;
  product_url: string | null;
};

export type SatelliteContext = {
  provider: string;
  collection: string;
  source_url: string;
  radius_m: number;
  days: number;
  status: string;
  best_scene: SatelliteScene | null;
  scenes: SatelliteScene[];
  warnings: string[];
};

export type PlacesEnrichmentItem = {
  name: string | null;
  category: string;
  distance_m: number;
  is_chain: boolean;
  google_maps_url: string;
  rating: number | null;
  user_ratings_total: number | null;
  price_level: number | null;
  price_label: string | null;
  source: "google_places" | "manual_survey_link";
};

export type PlacesEnrichment = {
  configured: boolean;
  items: PlacesEnrichmentItem[];
  warnings: string[];
};

export type ClaimVerdict = {
  claim: string;
  claim_type: string;
  verdict: string;
  verdict_vi: string;
  reason: string;
  evidence: string[];
  confidence: string;
  explanation: string | null;
};

export type ChatResponse = {
  answer: string;
  grounded: boolean;
  model: string | null;
  citations: Array<{
    document_id: string;
    filename: string;
    excerpt: string;
    page: number | null;
  }>;
};

