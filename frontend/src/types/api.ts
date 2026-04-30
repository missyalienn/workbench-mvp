export interface SearchPlan {
  search_terms: string[];
  subreddits: string[];
}

export interface ClientThread {
  rank: number;
  title: string;
  subreddit: string;
  url: string;
  relevance_score: number;
}

export interface ApiResponse {
  search_plan: SearchPlan;
  status: "ok" | "partial" | "insufficient";
  summary: string;
  threads: ClientThread[];
  limitations: string[];
}

export interface ApiError {
  type: "rate_limit" | "network" | "server" | "timeout";
  message: string;
}
