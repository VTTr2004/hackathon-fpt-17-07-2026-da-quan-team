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
  report: {
    risks?: string[];
    missing_data?: string[];
    tool_calls?: Array<{ name: string; version: string }>;
  };
  created_at: string;
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

