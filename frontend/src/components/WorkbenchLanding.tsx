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
import { ChevronUp, Search, SendHorizontal } from "lucide-react";
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
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [howItWorksOpen, setHowItWorksOpen] = useState(true);
  const [howItWorksAnimKey, setHowItWorksAnimKey] = useState(0);
  const hasFiredHowItWorks = useRef(false);

  const toggleHowItWorks = () => {
    if (!howItWorksOpen) setHowItWorksAnimKey((k) => k + 1);
    setHowItWorksOpen((prev) => !prev);
  };

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmedQuery = query.trim();
    if (!trimmedQuery) {
      return;
    }
    setSubmittedQuery(trimmedQuery);
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
          <section className="mx-auto w-full max-w-lg md:max-w-xl">
            <LoadingState />
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
            <>
              <p className="mb-3 px-1 text-sm text-[#8f8faa]">
                {submittedQuery
                  ? <>Top results for <span className="font-medium text-[#5b5b73]">"{submittedQuery}"</span></>
                  : "Example results"}
              </p>
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
            </>
          )}
        </section>

        <section onMouseEnter={handleHowItWorksImpression}>
          <div className="mb-4 flex items-center justify-center gap-2">
            <TypographyH2 className="border-b-0 pb-0 text-[22px] text-[#262162] md:text-[26px]">
              How it works
            </TypographyH2>
            <button
              onClick={toggleHowItWorks}
              aria-label={howItWorksOpen ? "Collapse how it works" : "Expand how it works"}
              className="mt-0.5 flex h-7 w-7 items-center justify-center rounded-full text-[#8f8faa] transition-colors hover:bg-[#ebebf4] hover:text-[#262162]"
            >
              <ChevronUp
                className="h-4 w-4 transition-transform duration-300"
                style={{ transform: howItWorksOpen ? "rotate(0deg)" : "rotate(180deg)" }}
              />
            </button>
          </div>

          <div
            className="overflow-hidden transition-all duration-300 ease-in-out"
            style={{ maxHeight: howItWorksOpen ? "600px" : "0px", opacity: howItWorksOpen ? 1 : 0 }}
          >
            <Card className="mx-auto max-w-2xl border-[#e7e5e4] bg-white shadow-sm">
              <CardContent className="p-0">
                <div className="divide-y divide-[#e7e5e4]">
                  {[
                    { title: "Plan your search", description: "Maps your question to targeted Reddit queries" },
                    { title: "Fetch discussions", description: "Pulls relevant threads and top comments" },
                    { title: "Rank by relevance", description: "Scores posts against your query via embeddings" },
                    { title: "Synthesize results", description: "Extracts key evidence and surfaces citations" },
                  ].map((step, index) => (
                    <div
                      key={`${step.title}-${howItWorksAnimKey}`}
                      className="relative flex items-start gap-4 px-5 py-4 md:px-6"
                      style={{
                        animation: howItWorksOpen ? `fadeSlideIn 400ms ease-out both` : "none",
                        animationDelay: `${index * 150}ms`,
                      }}
                    >
                      <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#262162] text-[11px] font-semibold text-white">
                        {index + 1}
                      </span>
                      <div>
                        <p className="text-sm font-semibold text-[#262162]">{step.title}</p>
                        <p className="mt-0.5 text-sm text-[#5b5b73]">{step.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </section>

        <footer className="border-t border-[#e7e5e4] pt-6 text-sm text-[#a8a29e]">
          Workbench — Agent-based research for DIY and home improvement.
        </footer>
      </div>
    </main>
  );
}
