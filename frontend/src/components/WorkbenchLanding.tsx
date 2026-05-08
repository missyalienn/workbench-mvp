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

import { HowItWorksSection } from "@/components/landing/HowItWorksSection";
import { LandingSearchForm } from "@/components/landing/LandingSearchForm";
import { SourceResultItem } from "@/components/landing/SourceResultItem";
import type { WorkbenchResult } from "@/components/landing/types";
import { Card, CardContent } from "@/components/ui/card";
import { TypographyH1 } from "@/components/ui/typography";
import { LoadingState } from "@/components/LoadingState";

interface WorkbenchLandingProps {
  results: WorkbenchResult[];
  isLoading: boolean;
  errorMessage?: string | null;
  summary?: string | null;
  limitations?: string[];
  onSearch: (query: string) => void;
  onHowItWorksClick: () => void;
}

export function WorkbenchLanding({
  results,
  isLoading,
  errorMessage,
  summary,
  limitations = [],
  onSearch,
  onHowItWorksClick,
}: WorkbenchLandingProps) {
  const SHOW_SUMMARY_LAYOUT = true;
  const isIdleState =
    !isLoading &&
    !errorMessage &&
    !summary &&
    results.length === 0 &&
    limitations.length === 0;
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
    setHowItWorksOpen(false);
    onSearch(trimmedQuery);
  };

  const handleHowItWorksImpression = () => {
    if (hasFiredHowItWorks.current) {
      return;
    }
    hasFiredHowItWorks.current = true;
    onHowItWorksClick();
  };

  return (
    <main className="min-h-screen bg-[#f7f7f5] text-[#1e1b4b]">
      <div className="mx-auto flex max-w-5xl flex-col gap-12 px-6 pb-14 pt-16">
        <header className="flex items-center justify-between border-b border-[#e7e5e4] pb-4">
          <span className="text-[17px] font-medium leading-none tracking-tight text-[#1e1b4b]">Workbench</span>
        </header>

        <section className="px-2 text-center">
          <TypographyH1 className="mb-4 text-balance text-4xl font-bold leading-tight text-[#262162] md:text-5xl">
            Research agent that shows its work.

          </TypographyH1>
          <p
            className={`mx-auto max-w-2xl text-pretty text-base font-normal leading-relaxed text-[#62627a] md:max-w-4xl md:text-lg ${
              isIdleState ? "mb-14" : "mb-10"
            }`}
          >
            Multi-agent research workflow that delivers structured findings. Limitations and sources included.

          </p>
          <LandingSearchForm
            query={query}
            onQueryChange={setQuery}
            onSubmit={handleSubmit}
          />
          <p className="mt-3 px-1 text-sm font-medium text-[#78788f]">
            Demo is currently scoped to DIY and home improvement communities on Reddit.
          </p>
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

        {!isIdleState ? (
          <section className="mx-auto -mt-6 w-full max-w-5xl">
            <div className="grid gap-5 md:grid-cols-2">
              <div className="space-y-5">
                {SHOW_SUMMARY_LAYOUT && !isLoading && !errorMessage && summary ? (
                  <div>
                    <p className="mb-3 px-1 text-sm text-[#8f8faa]">Synthesis</p>
                    <Card className="rounded-2xl border border-[#e7e5e4] bg-white shadow-sm">
                      <CardContent className="px-5 py-4">
                        <p className="text-[15px] leading-7 text-[#3f3f5c] md:text-base">
                          {summary}
                        </p>
                      </CardContent>
                    </Card>
                  </div>
                ) : null}

                {SHOW_SUMMARY_LAYOUT && !isLoading && !errorMessage && limitations.length > 0 ? (
                  <div>
                    <p className="mb-3 px-1 text-sm text-[#8f8faa]">Limitations</p>
                    <Card className="rounded-2xl border border-[#eadfd0] bg-[#fcfaf6] shadow-sm">
                      <CardContent className="px-5 py-4">
                        <ul className="space-y-2 text-sm leading-6 text-[#5b5b73]">
                          {limitations.map((item) => (
                            <li
                              key={item}
                              className="flex gap-2"
                            >
                              <span className="mt-[9px] h-1.5 w-1.5 shrink-0 rounded-full bg-[#b8a78d]" />
                              <span>{item}</span>
                            </li>
                          ))}
                        </ul>
                      </CardContent>
                    </Card>
                  </div>
                ) : null}
              </div>

              {results.length === 0 ? null : (
                <div>
                  <p className="mb-3 px-1 text-sm text-[#8f8faa]">
                    {submittedQuery ? "Sources" : "Sources"}
                  </p>
                  <Card className="overflow-hidden rounded-2xl border border-[#e7e5e4] bg-white shadow-sm">
                    <CardContent className="p-0">
                      <ol className="divide-y divide-[#e7e5e4]">
                        {results.map((result) => (
                          <SourceResultItem
                            key={`${result.rank}-${result.link}`}
                            result={result}
                          />
                        ))}
                      </ol>
                    </CardContent>
                  </Card>
                </div>
              )}

            </div>
          </section>
        ) : null}

        <HowItWorksSection
          isOpen={howItWorksOpen}
          animationKey={howItWorksAnimKey}
          onToggle={toggleHowItWorks}
          onImpression={handleHowItWorksImpression}
        />

        <footer className="border-t border-[#e7e5e4] pt-6 text-sm text-[#a8a29e]">
          Workbench — Research agent that shows its work.
        </footer>
      </div>
    </main>
  );
}
