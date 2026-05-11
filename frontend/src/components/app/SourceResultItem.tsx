/**
 * Source result row for the Workbench app surface.
 *
 * Usage:
 * <SourceResultItem result={result} />
 */
import { ArrowUpRight } from "lucide-react";

import type { WorkbenchResult } from "@/components/app/types";

interface SourceResultItemProps {
  result: WorkbenchResult;
}

const COMPACT_NUMBER_FORMAT = new Intl.NumberFormat("en-US", {
  notation: "compact",
  maximumFractionDigits: 1,
});

function formatRedditStat(value: number, noun: string): string {
  const normalizedValue = Math.max(0, value);
  const compactValue = COMPACT_NUMBER_FORMAT
    .format(normalizedValue >= 10000 ? Math.round(normalizedValue) : normalizedValue)
    .replace("K", "k")
    .replace("M", "m")
    .replace("B", "b");

  return `${compactValue} ${noun}`;
}

function getRelevanceLabel(
  relevance: number,
): { label: string; textClass: string } {
  if (relevance >= 60) {
    return { label: "High relevance", textClass: "text-green-800 font-medium" };
  }

  if (relevance >= 50) {
    return { label: "Medium relevance", textClass: "text-amber-700 font-medium" };
  }

  return { label: "Low relevance", textClass: "text-[#8f8faa]" };
}

export function SourceResultItem({ result }: SourceResultItemProps) {
  const { label, textClass } = getRelevanceLabel(result.relevance);
  const commentLabel = result.comments === 1 ? "comment" : "comments";

  return (
    <li className="grid grid-cols-[2rem_1fr] gap-3 px-5 py-4 transition-colors hover:bg-[#fafaf9]">
      <span className="pt-1 text-xs tabular-nums text-[#a8a29e]">
        {String(result.rank).padStart(2, "0")}
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-start gap-x-4 gap-y-1">
          <span className="text-sm text-[#8f8faa]">r/{result.subreddit}</span>
        </div>
        <a
          href={result.link}
          target="_blank"
          rel="noreferrer"
          className="mt-1 inline-flex items-start gap-1 text-base font-semibold leading-snug text-[#1e1b4b] underline-offset-4 transition-colors hover:text-[#312e81] hover:underline focus-visible:outline-none focus-visible:underline md:text-[17px]"
        >
          <span>{result.title}</span>
          <ArrowUpRight
            className="mt-0.5 h-3 w-3 shrink-0 text-[#a4a1b7]"
            aria-hidden="true"
          />
        </a>
        <div className="mt-2 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm font-medium text-[#8f8faa]">
          <span>{formatRedditStat(result.upvotes, "Upvotes")}</span>
          <span>·</span>
          <span>{formatRedditStat(result.comments, commentLabel)}</span>
          {Number.isFinite(result.relevance) && (
            <span className={`ml-3 ${textClass}`}>
              {label}
            </span>
          )}
        </div>
      </div>
    </li>
  );
}
