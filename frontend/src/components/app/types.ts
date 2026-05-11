/**
 * Shared app result types.
 *
 * Usage:
 * import type { WorkbenchResult } from "@/components/app/types";
 */
export interface WorkbenchResult {
  rank: number;
  subreddit: string;
  title: string;
  link: string;
  comments: number;
  upvotes: number;
  relevance: number;
}
