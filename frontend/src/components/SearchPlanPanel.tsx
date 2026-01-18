import { useState } from "react";
import type { SearchPlan } from "../types/api";

interface SearchPlanPanelProps {
  searchPlan: SearchPlan;
}

export function SearchPlanPanel({ searchPlan }: SearchPlanPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="border border-gray-200 rounded-lg p-4">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between text-left font-semibold text-gray-700"
      >
        <span>Search Plan</span>
        <span>{isExpanded ? "▼" : "▶"}</span>
      </button>
      {isExpanded && (
        <div className="mt-4 space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-gray-600 mb-2">
              Subreddits:
            </h3>
            <ul className="list-disc list-inside text-sm text-gray-700">
              {searchPlan.subreddits.map((sub, idx) => (
                <li key={idx}>r/{sub}</li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-600 mb-2">
              Search Terms:
            </h3>
            <ul className="list-disc list-inside text-sm text-gray-700">
              {searchPlan.search_terms.map((term, idx) => (
                <li key={idx}>{term}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
