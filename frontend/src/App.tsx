import { useState } from "react";
import type { WorkbenchResult } from "./components/app/types";
import { submitDemoQuery } from "./services/api";
import { WorkbenchApp } from "./components/WorkbenchApp";

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
      relevance: Math.round(thread.relevance_score * 100),
    }));

    setResults(mappedResults);
    setSummary(response.summary ?? null);
    setLimitations(response.limitations ?? []);
    setIsLoading(false);
  };

  return (
    <WorkbenchApp
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
