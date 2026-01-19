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
import { Spinner } from "@/components/ui/spinner";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { TypographyH1, TypographyH2 } from "@/components/ui/typography";

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
  onSearch: (query: string) => void;
  onHowItWorksClick: () => void;
}

export function WorkbenchLanding({
  results,
  isLoading,
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



  return (
    <main className="min-h-screen bg-[#f7f7f5] text-[#1e1b4b]">
      <div className="mx-auto flex max-w-5xl flex-col gap-12 px-6 py-14">
        <header className="flex items-center justify-between border-b border-[#e7e5e4] pb-4">
          <span className="text-lg font-semibold text-[#262162]">Workbench</span>
        </header>

        <section className="px-2 text-center">
          <div className="space-y-4">
            <TypographyH1 className="text-balance text-[32px] font-semibold leading-[1.1] tracking-[0.005em] text-[#262162] md:text-[44px]">
              AI research that cites its sources.
            </TypographyH1>
            <TypographyH2 className="mx-auto max-w-xl border-b-0 pb-0 text-[18px] font-normal leading-[1.4] tracking-[0.01em] text-[#62627a] md:text-[22px]">
              <span className="block">
                Ranked answers from DIY communities on Reddit.
              </span>
              <span className="block">Built to surface signal, not noise.</span>
            </TypographyH2>
          </div>
        </section>

        <section className="px-2 pb-10 text-center pt-4">
          <div className="space-y-3">
            <TypographyH1 className="border-b-0 pb-0 text-[28px] font-normal text-[#262162] md:text-[36px]">
              Start with a DIY topic or question.
            </TypographyH1>
          </div>
          <form onSubmit={handleSubmit} className="mt-3">
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

        <section className="mx-auto mt-8 w-full max-w-4xl space-y-4">
          <div className="space-y-1 text-center">
            <TypographyH2 className="border-b-0 pb-0 text-[22px] text-[#262162] md:text-[30px]">
              Ranked results, verified sources.
            </TypographyH2>
            <p className="text-sm text-[#8f8faa]">
            </p>
          </div>

          {isLoading ? (
            <Card className="border-[#e7e5e4] bg-white shadow-sm">
              <CardContent className="flex flex-col items-center justify-center gap-4 py-10 text-sm text-[#78716c]">
                <Spinner className="h-10 w-10 text-[#262162]" />
                <span>Searching, filtering, and ranking results...</span>
              </CardContent>
            </Card>
          ) : (
            <div className="overflow-hidden rounded-lg border border-[#e7e5e4] bg-white">
              <Table>
                <TableHeader className="bg-[#f2f2f7]">
                  <TableRow className="hover:bg-transparent">
                    <TableHead className="px-4 py-3 text-xs uppercase text-[#262162]">
                      Rank
                    </TableHead>
                    <TableHead className="px-4 py-3 text-xs uppercase text-[#262162]">
                      Subreddit
                    </TableHead>
                    <TableHead className="px-4 py-3 text-xs uppercase text-[#262162]">
                      Discussion
                    </TableHead>
                    <TableHead className="px-4 py-3 text-right text-xs uppercase text-[#262162]">
                      Relevance
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {results.length === 0 ? (
                    <TableRow className="hover:bg-transparent">
                      <TableCell
                        colSpan={4}
                        className="px-4 py-8 text-center text-[#a8a29e]"
                      >
                        No results yet.
                      </TableCell>
                    </TableRow>
                  ) : (
                    results.map((result) => (
                      <TableRow
                        key={`${result.rank}-${result.link}`}
                        className="border-[#e7e5e4] hover:bg-[#fafaf9]"
                      >
                        <TableCell className="px-4 py-4 font-semibold text-[#262162]">
                          {result.rank}
                        </TableCell>
                        <TableCell className="px-4 py-4">
                          <span className="inline-flex rounded-full bg-[#eef0fb] px-2 py-1 text-xs text-[#262162]">
                            r/{result.subreddit}
                          </span>
                        </TableCell>
                        <TableCell className="px-4 py-4">
                          <div className="text-base font-semibold text-[#1e1b4b]">
                            {result.title}
                          </div>
                          <a
                            href={result.link}
                            className="text-sm text-[#2f3aa1] hover:text-[#262162] hover:underline"
                            target="_blank"
                            rel="noreferrer"
                          >
                            View discussion on Reddit →
                          </a>
                        </TableCell>
                        <TableCell className="px-4 py-4 text-right font-semibold text-[#f59e0b]">
                          {Number.isFinite(result.relevance)
                            ? result.relevance
                            : "—"}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
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
