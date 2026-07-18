export type Startup = {
  id: string;
  owner_id: string | null;
  name: string;
  industry: string | null;
  stage: string | null;
  primary_location: string | null;
  facts: Record<string, unknown>;
  status: string;
  current_version: number;
  discoverable: boolean;
  public_summary: Record<string, boolean>;
  created_at: string;
  updated_at: string;
};

export type DocumentItem = {
  id: string;
  startup_id: string;
  filename: string;
  content_type: string | null;
  status: string;
  extractable: boolean;
  visibility: "private" | "shared" | "restricted";
  category: DocumentCategory;
  categorized_by: "ai" | "rules" | "pending";
  created_at: string;
};

export type DocumentCategory =
  | "legal"
  | "sales_revenue"
  | "purchases_expenses"
  | "accounting_cashflow"
  | "location_operations"
  | "unclassified";

export type ProfileExtractionEvidence = {
  document_id: string;
  block_id: string;
  filename: string;
  quote: string;
  page?: number | null;
  slide?: number | null;
  sheet?: string | null;
  table?: number | string | null;
  row?: number | null;
  cell_range?: string | null;
};

export type ProfileExtractionCandidate = {
  id: string;
  field_key: string;
  label: string;
  value_type: string;
  proposed_value: unknown;
  evidence: ProfileExtractionEvidence[];
  confidence: number;
  status: "found" | "not_found" | "ambiguous" | "conflicting";
  warnings: string[];
  user_decision: string | null;
  confirmed_value: unknown;
};

export type ProfileExtractionJob = {
  id: string;
  startup_id: string;
  status: "pending" | "running" | "completed" | "failed" | "applied";
  document_ids: string[];
  field_keys: string[];
  schema_version: string;
  based_on_startup_updated_at: string;
  warnings: string[];
  error: string | null;
  completed_at: string | null;
  applied_at: string | null;
  created_at: string;
  candidates: ProfileExtractionCandidate[];
};

export type AnalysisModule = "business_model" | "cash_flow" | "surrounding_area";

export type Analysis = {
  id: string;
  startup_id: string;
  startup_version_id: string | null;
  created_by_id: string | null;
  module: AnalysisModule;
  version: string;
  status: string;
  score: number | null;
  summary: string;
  report: ModuleReport;
  rubric_version: string;
  created_at: string;
};

export type UserRole = "startup" | "investor";

export type User = {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  status: string;
  created_at: string;
};

export type AuthResponse = {
  access_token: string;
  token_type: "bearer";
  user: User;
};

export type Completeness = {
  complete: boolean;
  completed_fields: number;
  total_fields: number;
  missing_fields: string[];
  missing_documents: string[];
  format_errors: string[];
  can_submit: boolean;
};

export type StartupVersion = {
  id: string;
  startup_id: string;
  version_number: number;
  status: string;
  snapshot: Record<string, unknown>;
  document_ids: string[];
  created_by_id: string;
  submitted_at: string;
  locked_at: string;
};

export type InvestorAccess = {
  investor_id: string;
  investor_name: string;
  investor_email: string;
  status: "pending" | "active" | "rejected" | "revoked";
  request_reason: string | null;
};

export type InvestorPreference = {
  preferred_industries: string[];
  preferred_subsectors: string[];
  preferred_stages: string[];
  preferred_locations: string[];
  ticket_min: number | null;
  ticket_max: number | null;
  minimum_monthly_revenue: number | null;
  minimum_revenue_growth: number | null;
  maximum_runway_months: number | null;
  required_capabilities: string[];
  strategic_capabilities: string[];
  exclusion_rules: Record<string, unknown>;
  weights: Record<string, number>;
};

export type Candidate = {
  startup_id: string;
  name: string;
  industry: string | null;
  subsector: string | null;
  stage: string | null;
  location: string | null;
  traction_summary: string | null;
  fundraising_need: string | null;
  runway_months: number | null;
  revenue_growth: number | null;
  fit_score: number;
  confidence_score: number;
  score_breakdown: Record<string, number>;
  matched_reasons: string[];
  mismatched_reasons: string[];
  missing_evidence: string[];
  recommended_action: string;
  access_status: "none" | "pending" | "active" | "rejected" | "revoked";
  pipeline_status: string;
};

export type PipelineItem = {
  id: string;
  startup_id: string;
  startup_name: string;
  status: "discovered" | "shortlisted" | "access_requested" | "reviewing" | "interested" | "passed";
  note: string | null;
  fit_score: number | null;
  confidence_score: number | null;
  access_status: string;
  created_at: string;
  updated_at: string;
};

export type VersionDiff = {
  from_version: number;
  to_version: number;
  changes: Array<{ field: string; before: unknown; after: unknown }>;
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

export type CashFlowProposalSource = {
  document_id: string;
  filename: string;
  sheet: string;
  range?: string | null;
};

export type CashFlowAutofillProposal = {
  proposal_id: string;
  field: string;
  value: unknown;
  status: string;
  confidence: string;
  sources: CashFlowProposalSource[];
  generated_by_tool: string;
  warnings: string[];
};

export type CashFlowIngestionCall = {
  tool: string;
  document_id: string;
  sheet: string;
  header_row: number;
  columns: Record<string, number>;
  field_map?: Record<string, string>;
  notes?: string | null;
};

export type CashFlowIngestionDetails = {
  status: string;
  preview_id?: string;
  plan_source?: string;
  plan?: {
    calls: CashFlowIngestionCall[];
    ignored_sheets?: string[];
    assumptions?: string[];
  };
  supporting_metrics?: Record<string, unknown>;
  autofill_proposals?: CashFlowAutofillProposal[];
  warnings?: string[];
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
  place_id: string | null;
  name: string | null;
  category: string;
  distance_m: number;
  is_chain: boolean;
  google_maps_url: string;
  rating: number | null;
  user_ratings_total: number | null;
  price_level: number | null;
  price_label: string | null;
  reviews: Array<{
    author_name: string | null;
    rating: number | null;
    relative_time_description: string | null;
    text: string | null;
    time: number | null;
  }>;
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

export type Citation = {
  document_id: string;
  filename: string;
  excerpt: string;
  page: number | null;
  locator?: string | null;
};

export type ChatResponse = {
  answer: string;
  grounded: boolean;
  model: string | null;
  metadata?: Record<string, unknown>;
  citations: Citation[];
};

export type ChatMessageItem = {
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
  created_at: string;
};

