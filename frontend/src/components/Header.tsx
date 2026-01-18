import { useState } from "react";

export function Header() {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <header className="border-b border-gray-200 pb-8 text-center">
      <h1 className="text-[40px] font-bold tracking-[-0.04em] leading-none text-black">
        Workbench
      </h1>
      <p className="mt-3 text-[40px] font-semibold tracking-[-0.04em] leading-none text-[#999999]">
        Agent-based research for DIY and home improvement. Ranked Reddit threads
        with source links.
      </p>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="mt-6 text-sm font-medium text-black hover:text-[#999999]"
      >
        {isExpanded ? "▼" : "▶"} How it works
      </button>
      {isExpanded && (
        <div className="mt-4 text-sm text-[#999999]">
          <p className="max-w-3xl mx-auto text-left">
            Ask a DIY or home improvement question, and let our research agent
            scan Reddit for the most relevant advice. Filtered, ranked results
            with source links to the most relevant discussions.
          </p>
        </div>
      )}
    </header>
  );
}
