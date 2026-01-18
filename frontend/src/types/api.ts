export interface SearchPlan {
  search_terms: string[];
  subreddits: string[];
  notes?: string;
}

export interface ThreadEvidence {
  rank: number;
  post_id: string;
  title: string;
  subreddit: string;
  url: string;
  relevance_score: number;
}

export interface EvidenceResult {
  status: "ok" | "partial" | "error";
  threads: ThreadEvidence[];
  limitations: string[];
  prompt_version: string;
}

export interface DemoApiResponse {
  search_plan: SearchPlan;
  evidence_result: EvidenceResult;
}

export interface ApiError {
  type: "rate_limit" | "network" | "server" | "timeout";
  message: string;
}
