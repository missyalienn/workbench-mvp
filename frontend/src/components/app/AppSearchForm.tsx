/**
 * Search form used by the Workbench app surface.
 *
 * Usage:
 * <AppSearchForm query={query} onQueryChange={setQuery} onSubmit={handleSubmit} />
 */
import { Search, SendHorizontal } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface AppSearchFormProps {
  query: string;
  onQueryChange: (value: string) => void;
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
}

export function AppSearchForm({
  query,
  onQueryChange,
  onSubmit,
}: AppSearchFormProps) {
  return (
    <form onSubmit={onSubmit}>
      <div className="mx-auto flex w-full max-w-lg items-center gap-2 rounded-[20px] border border-[#d0d0de] bg-[#fbfbfc] px-2 py-1 text-[#262162] shadow-sm transition-all duration-300 focus-within:border-[#262162] focus-within:ring-2 focus-within:ring-[#b9b9da] md:max-w-xl">
        <span className="flex h-9 w-9 items-center justify-center rounded-full bg-white text-[#262162] shadow-sm">
          <Search className="h-5 w-5" />
        </span>
        <Input
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder="Start with a topic or question"
          className="h-10 flex-1 border-0 bg-transparent px-1 text-base text-[#262162] placeholder:text-[#8f8faa] focus-visible:ring-0 focus-visible:ring-offset-0 md:text-lg"
        />
        <Button
          type="submit"
          size="icon"
          variant="ghost"
          className="h-10 w-10 rounded-full bg-white p-0 shadow-sm hover:bg-[#f2f2f7]"
          aria-label="Search"
        >
          <SendHorizontal
            className="h-5 w-5 text-[#262162]"
            aria-hidden="true"
          />
        </Button>
      </div>
    </form>
  );
}
