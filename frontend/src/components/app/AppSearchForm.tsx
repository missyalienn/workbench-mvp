/**
 * Search form used by the Workbench app surface.
 *
 * Usage:
 * <AppSearchForm query={query} onQueryChange={setQuery} onSubmit={handleSubmit} />
 */
import { useLayoutEffect, useRef } from "react";

import { SendHorizontal } from "lucide-react";

import { Button } from "@/components/ui/button";

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
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useLayoutEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) {
      return;
    }

    // Grow with the query while keeping a compact default height.
    textarea.style.height = "0px";
    textarea.style.height = `${textarea.scrollHeight}px`;
  }, [query]);

  return (
    <form
      onSubmit={onSubmit}
      className="mx-auto w-full max-w-2xl"
    >
      <div className="mx-auto flex w-full flex-col gap-4 rounded-[26px] border border-[#e7e5e4] bg-[#fafaf9] px-5 py-5 text-[#292524] shadow-[0_8px_24px_rgba(41,37,36,0.06)] transition-all duration-300 focus-within:border-[#78716c] focus-within:ring-2 focus-within:ring-[#e7e5e4] md:px-6 md:py-5">
        <div className="flex items-start">
          <textarea
            ref={textareaRef}
            value={query}
            onChange={(event) => onQueryChange(event.target.value)}
            aria-label="Search query"
            placeholder="What are you working on?"
            rows={1}
            className="min-h-[28px] max-h-[240px] flex-1 resize-none overflow-y-auto border-0 bg-transparent p-0 text-[15px] leading-7 text-[#292524] outline-none placeholder:text-[#78716c] focus-visible:ring-0 focus-visible:ring-offset-0 md:text-base"
          />
        </div>
        <div className="flex justify-end">
          <Button
            type="submit"
            size="icon"
            variant="ghost"
            className={`h-10 w-10 rounded-full p-0 shadow-sm transition-colors ${
              query.trim()
                ? "bg-[#292524] text-white hover:bg-[#44403c]"
                : "bg-[#f5f5f4] text-[#78716c] hover:bg-[#e7e5e4]"
            }`}
            aria-label="Search"
          >
            <SendHorizontal
              className="h-4.5 w-4.5"
              aria-hidden="true"
            />
          </Button>
        </div>
      </div>
    </form>
  );
}
