import type { ThreadEvidence } from "../types/api";

interface ResultsListProps {
  threads: ThreadEvidence[];
}

export function ResultsList({ threads }: ResultsListProps) {
  if (threads.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">No results found</div>
    );
  }

  return (
    <div className="divide-y divide-gray-200">
      {threads.map((thread) => (
        <div
          key={thread.post_id}
          className="py-4"
        >
          <div className="grid gap-3 md:grid-cols-[160px_1fr_160px] md:items-start">
            <div className="flex items-center gap-3">
              <span className="text-xl font-semibold text-black">
                #{thread.rank}
              </span>
              <span className="inline-flex items-center px-2 py-1 text-xs text-[#999999] border border-gray-200 rounded-full">
                r/{thread.subreddit}
              </span>
            </div>
            <div className="min-w-0">
              <a
                href={thread.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block text-base font-semibold text-black hover:text-gray-700"
              >
                {thread.title}
              </a>
              <a
                href={thread.url}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-1 inline-block text-sm text-[#999999] hover:text-gray-700"
              >
                View discussion on Reddit →
              </a>
            </div>
            <div className="text-sm text-[#999999] md:text-right">
              Relevance:{" "}
              {Number.isFinite(thread.relevance_score)
                ? thread.relevance_score.toFixed(2)
                : "—"}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
