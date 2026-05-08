import { useState } from "react";
import type { WorkbenchResult } from "./components/landing/types";
import { submitDemoQuery } from "./services/api";
import { WorkbenchLanding } from "./components/WorkbenchLanding";

function App() {
  const [results, setResults] = useState<WorkbenchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [summary, setSummary] = useState<string | null>(null);
  const [limitations, setLimitations] = useState<string[]>([]);

  const handleSearch = async (query: string) => {
    setIsLoading(true);
    setErrorMessage(null);
    setResults([]);
    setSummary(null);
    setLimitations([]);

    const { response, error } = await submitDemoQuery(query);
    if (error) {
      setResults([]);
      setSummary(null);
      setLimitations([]);
      setErrorMessage(error.message);
      setIsLoading(false);
      return;
    }

    if (!response) {
      setResults([]);
      setSummary(null);
      setLimitations([]);
      setErrorMessage("No response received.");
      setIsLoading(false);
      return;
    }

    const threads = response.threads ?? [];
    const mappedResults: WorkbenchResult[] = threads.map((thread) => ({
      rank: thread.rank,
      subreddit: thread.subreddit,
      title: thread.title,
      link: thread.url,
      comments: thread.num_comments,
      upvotes: thread.post_karma,
      relevance: Math.round(thread.relevance_score * 100),
    }));

    setResults(mappedResults);
    setSummary(response.summary ?? null);
    setLimitations(response.limitations ?? []);
    setIsLoading(false);
  };

  return (
    <WorkbenchLanding
      results={results}
      isLoading={isLoading}
      errorMessage={errorMessage}
      summary={summary}
      limitations={limitations}
      onSearch={handleSearch}
      onHowItWorksClick={() => {}}
    />
  );
}

export default App;
