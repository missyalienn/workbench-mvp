import { useState } from "react";

interface QueryBoxProps {
  onSubmit: (query: string) => void;
  disabled?: boolean;
}

export function QueryBox({ onSubmit, disabled = false }: QueryBoxProps) {
  const [query, setQuery] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !disabled) {
      onSubmit(query.trim());
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 text-center">
      <textarea
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Enter your question..."
        disabled={disabled}
        className="w-full resize-none px-4 py-4 border border-gray-300 rounded-md text-lg focus:outline-none focus:ring-2 focus:ring-black/10 disabled:bg-gray-100"
        rows={3}
      />
      <button
        type="submit"
        disabled={disabled || !query.trim()}
        className="px-8 py-2 bg-black text-white rounded-full hover:bg-gray-900 disabled:bg-gray-400 disabled:cursor-not-allowed"
      >
        Search for advice
      </button>
      <p className="text-sm text-[#999999]">
        Examples: "how to hang floating shelves", "fill nail holes in drywall"
      </p>
    </form>
  );
}
