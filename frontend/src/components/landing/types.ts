/**
 * Shared landing-page result types.
 *
 * Usage:
 * import type { WorkbenchResult } from "@/components/landing/types";
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
