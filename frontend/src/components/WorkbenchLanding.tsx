/**
 * Workbench landing page layout skeleton.
 *
 * Usage:
 * <WorkbenchLanding
 *   results={results}
 *   isLoading={isLoading}
 *   onSearch={handleSearch}
 *   onHowItWorksClick={handleHowItWorksClick}
 * />
 */
import { useRef, useState } from "react";
import { Search, SendHorizontal } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { TypographyH1, TypographyH2 } from "@/components/ui/typography";
import { LoadingState } from "@/components/LoadingState";

export interface WorkbenchResult {
  rank: number;
  subreddit: string;
  title: string;
  link: string;
  comments: number;
  upvotes: number;
  relevance: number;
}

interface WorkbenchLandingProps {
  results: WorkbenchResult[];
  isLoading: boolean;
  errorMessage?: string | null;
  onSearch: (query: string) => void;
  onHowItWorksClick: () => void;
}

export function WorkbenchLanding({
  results,
  isLoading,
  errorMessage,
  onSearch,
  onHowItWorksClick,
}: WorkbenchLandingProps) {
  const [query, setQuery] = useState("");
  const hasFiredHowItWorks = useRef(false);

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmedQuery = query.trim();
    if (!trimmedQuery) {
      return;
    }
    onSearch(trimmedQuery);
  };

  const handleHowItWorksImpression = () => {
    if (hasFiredHowItWorks.current) {
      return;
    }
    hasFiredHowItWorks.current = true;
    onHowItWorksClick();
  };

  const getRelevanceLabel = (relevance: number): { label: string; textClass: string } => {
    if (relevance >= 60) return { label: "High relevance", textClass: "text-green-800 font-medium" };
    if (relevance >= 50) return { label: "Medium relevance", textClass: "text-amber-700 font-medium" };
    return { label: "Low relevance", textClass: "text-[#8f8faa]" };
  };



  return (
    <main className="min-h-screen bg-[#f7f7f5] text-[#1e1b4b]">
      <div className="mx-auto flex max-w-5xl flex-col gap-12 px-6 py-14">
        <header className="flex items-center justify-between border-b border-[#e7e5e4] pb-4">
          <span className="text-lg font-semibold text-[#262162]">Workbench</span>
        </header>

        <section className="px-2 text-center">
          <TypographyH1 className="mb-4 text-balance text-[36px] font-bold leading-[1.1] tracking-[0.005em] text-[#262162] md:text-[48px]">
            Find your starting point, faster.
          </TypographyH1>
          <p className="mx-auto mb-12 max-w-xl text-[17px] font-normal leading-[1.55] text-[#62627a] md:text-[19px]">
            Workbench turns your question into a targeted search plan, removes low-value results, and ranks relevant material so you can get started with a clear direction.
          </p>
          <p className="mb-3 text-sm font-medium text-[#62627a]">Start with a topic or question.</p>
          <form onSubmit={handleSubmit}>
            <div className="mx-auto flex w-full max-w-lg items-center gap-2 rounded-[20px] border border-[#d0d0de] bg-[#fbfbfc] px-2 py-1 text-[#262162] shadow-sm transition-all duration-300 focus-within:border-[#262162] focus-within:ring-2 focus-within:ring-[#b9b9da] md:max-w-xl">
              <span className="flex h-9 w-9 items-center justify-center rounded-full bg-white text-[#262162] shadow-sm">
                <Search className="h-5 w-5" />
              </span>
              <Input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="how do i hang floating shelves?"
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
        </section>

        {isLoading ? (
          <section className="mx-auto w-full max-w-2xl">
            <LoadingState stageMessage="Analyzing results..." />
          </section>
        ) : null}

        {errorMessage ? (
          <section className="mx-auto w-full max-w-4xl">
            <Card className="border-[#fed7aa] bg-[#fff7ed] shadow-sm">
              <CardContent className="py-4 text-sm text-[#b45309]">
                {errorMessage}
              </CardContent>
            </Card>
          </section>
        ) : null}

        <section className="mx-auto -mt-6 w-full max-w-lg md:max-w-xl">
          {results.length === 0 ? (
            <p className="py-8 text-center text-sm text-[#a8a29e]">No results yet.</p>
          ) : (
            <Card className="overflow-hidden rounded-2xl border border-[#e7e5e4] bg-white shadow-sm">
              <CardContent className="p-0">
                <ol className="divide-y divide-[#e7e5e4]">
                  {results.map((result) => {
                    const { label, textClass } = getRelevanceLabel(result.relevance);
                    return (
                      <li
                        key={`${result.rank}-${result.link}`}
                        className="grid grid-cols-[2rem_1fr] gap-3 px-5 py-3 transition-colors hover:bg-[#fafaf9]"
                      >
                        <span className="pt-0.5 text-xs tabular-nums text-[#a8a29e]">
                          {String(result.rank).padStart(2, "0")}
                        </span>
                        <div className="min-w-0 flex-1">
                          <a
                            href={result.link}
                            target="_blank"
                            rel="noreferrer"
                            className="text-base font-semibold leading-snug text-[#1e1b4b] hover:underline"
                          >
                            {result.title}
                          </a>
                          <div className="mt-1 flex flex-wrap items-center gap-1.5 text-sm text-[#8f8faa]">
                            <span>r/{result.subreddit}</span>
                            {Number.isFinite(result.relevance) && (
                              <>
                                <span>·</span>
                                <span className={textClass}>{label}</span>
                              </>
                            )}
                          </div>
                        </div>
                      </li>
                    );
                  })}
                </ol>
              </CardContent>
            </Card>
          )}
        </section>

        <section onMouseEnter={handleHowItWorksImpression}>
          <div className="mb-4 text-center">
            <TypographyH2 className="border-b-0 pb-0 text-[22px] text-[#262162] md:text-[26px]">
              How it works
            </TypographyH2>
          </div>
          <Card className="mx-auto max-w-2xl border-[#e7e5e4] bg-white shadow-sm">
            <CardContent className="p-0">
              <div className="divide-y divide-[#e7e5e4]">
                {[
                  "Collect source threads",
                  "Screen for relevance",
                  "Extract key evidence",
                  "Rank results with citations",
                ].map((item, index) => (
                  <div
                    key={item}
                    className="relative flex items-center gap-3 px-4 py-4 pl-12 text-sm text-[#5b5b73] md:px-6 md:pl-14"
                  >
                    <span
                      className="absolute left-[18px] flex h-2.5 w-2.5 items-center justify-center rounded-full border border-[#262162] md:left-[22px]"
                      style={{
                        backgroundColor:
                          index === 0
                            ? "transparent"
                            : `rgba(38, 33, 98, ${0.2 + index * 0.2})`,
                      }}
                    />
                    <span className="flex-1">{item}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </section>

        <footer className="border-t border-[#e7e5e4] pt-6 text-sm text-[#a8a29e]">
          Workbench — Agent-based research for DIY and home improvement.
        </footer>
      </div>
    </main>
  );
}
