/**
 * Workbench app layout skeleton.
 *
 * Usage:
 * <WorkbenchApp
 *   results={results}
 *   isLoading={isLoading}
 *   onSearch={handleSearch}
 *   onHowItWorksClick={handleHowItWorksClick}
 * />
 */
import { useRef, useState } from "react";

import { HowItWorksSection } from "@/components/app/HowItWorksSection";
import { AppSearchForm } from "@/components/app/AppSearchForm";
import { SourceResultItem } from "@/components/app/SourceResultItem";
import type { WorkbenchResult } from "@/components/app/types";
import { Card, CardContent } from "@/components/ui/card";
import { TypographyH1 } from "@/components/ui/typography";
import { LoadingState } from "@/components/LoadingState";

interface WorkbenchAppProps {
  results: WorkbenchResult[];
  isLoading: boolean;
  errorMessage?: string | null;
  summary?: string | null;
  limitations?: string[];
  onSearch: (query: string) => void;
  onHowItWorksClick: () => void;
}

export function WorkbenchApp({
  results,
  isLoading,
  errorMessage,
  summary,
  limitations = [],
  onSearch,
  onHowItWorksClick,
}: WorkbenchAppProps) {
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
    <main className="min-h-screen bg-[#f5f5f4] text-[#292524]">
      <div className="mx-auto flex max-w-5xl flex-col gap-12 px-6 pb-14 pt-16">
        <header className="flex items-center justify-between border-b border-[#e7e5e4] pb-4">
          <span className="text-[17px] font-medium leading-none tracking-tight text-[#292524]">Workbench</span>
        </header>

        <section className="px-2 text-center">
          <p className="mb-4 text-sm font-medium uppercase tracking-[0.18em] text-[#78716c]">
            Skip the scrolling.
          </p>
          <TypographyH1 className="mb-4 text-balance text-4xl font-bold leading-tight text-[#292524] md:text-5xl">
            Get the best DIY advice from Reddit, and get it done.
          </TypographyH1>
          <p
            className={`mx-auto max-w-2xl text-pretty text-base font-normal leading-relaxed text-[#57534e] md:max-w-4xl md:text-lg ${
              isIdleState ? "mb-20" : "mb-14"
            }`}
          >
            Less researching, more doing.
          </p>
          <AppSearchForm
            query={query}
            onQueryChange={setQuery}
            onSubmit={handleSubmit}
          />
          <p className="mt-3 px-1 text-sm font-medium text-[#78716c]">
            Currently scoped to DIY and home improvement communities on Reddit. More topics coming soon.
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
            {submittedQuery ? (
              <div className="mb-6 px-1">
                <p className="text-sm leading-6 text-[#57534e] md:text-base">
                  Results for{" "}
                  <span className="font-medium text-[#292524]">
                    "{submittedQuery}"
                  </span>
                </p>
              </div>
            ) : null}
            <div className="grid gap-5 md:grid-cols-2">
              {results.length === 0 ? null : (
                <div>
                  <p className="mb-3 px-1 text-sm text-[#78716c]">
                    Relevant threads
                  </p>
                  <Card className="overflow-hidden rounded-2xl border border-[#e7e5e4] bg-[#fafaf9] shadow-sm">
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

              <div className="space-y-5">
                {SHOW_SUMMARY_LAYOUT && !isLoading && !errorMessage && summary ? (
                  <div>
                    <p className="mb-3 px-1 text-sm text-[#78716c]">Overview</p>
                    <Card className="rounded-2xl border border-[#e7e5e4] bg-[#fafaf9] shadow-sm">
                      <CardContent className="px-5 py-4">
                        <p className="text-[15px] leading-7 text-[#57534e] md:text-base">
                          {summary}
                        </p>
                      </CardContent>
                    </Card>
                  </div>
                ) : null}

                {SHOW_SUMMARY_LAYOUT && !isLoading && !errorMessage && limitations.length > 0 ? (
                  <div>
                    <p className="mb-3 px-1 text-sm text-[#78716c]">Considerations</p>
                    <Card className="rounded-2xl border border-[#e7e5e4] bg-[#fafaf9] shadow-sm">
                      <CardContent className="px-5 py-4">
                        <ul className="space-y-2 text-sm leading-6 text-[#57534e]">
                          {limitations.map((item) => (
                            <li
                              key={item}
                              className="flex gap-2"
                            >
                              <span className="mt-[9px] h-1.5 w-1.5 shrink-0 rounded-full bg-[#78716c]" />
                              <span>{item}</span>
                            </li>
                          ))}
                        </ul>
                      </CardContent>
                    </Card>
                  </div>
                ) : null}
              </div>

            </div>
          </section>
        ) : null}

        <HowItWorksSection
          isOpen={howItWorksOpen}
          animationKey={howItWorksAnimKey}
          onToggle={toggleHowItWorks}
          onImpression={handleHowItWorksImpression}
        />

        <footer className="border-t border-[#e7e5e4] pt-6">
          <p className="text-sm font-medium text-[#292524]">Workbench</p>
          <p className="mt-8 text-xs text-[#78716c]">
            Built by a software engineer and woodworker who got tired of losing hours on DIY subreddits.
          </p>
        </footer>
      </div>
    </main>
  );
}
