import { useState } from "react";
import type { ThreadEvidence } from "./types/api";
import { submitDemoQuery } from "./services/api";
import type { WorkbenchResult } from "./components/WorkbenchLanding";
import { WorkbenchLanding } from "./components/WorkbenchLanding";

function App() {
  const sampleThreads: ThreadEvidence[] = [
    {
      rank: 1,
      post_id: "abc123",
      title: "Best caulk for a bathtub and tips to avoid mold?",
      subreddit: "homeimprovement",
      url: "https://www.reddit.com/r/homeimprovement/",
      relevance_score: 0.92,
    },
    {
      rank: 2,
      post_id: "def456",
      title: "How to remove old caulk cleanly before re-caulking",
      subreddit: "diy",
      url: "https://www.reddit.com/r/diy/",
      relevance_score: 0.84,
    },
  ];
  const initialResults: WorkbenchResult[] = sampleThreads.map((thread) => ({
    rank: thread.rank,
    subreddit: thread.subreddit,
    title: thread.title,
    link: thread.url,
    comments: 0,
    upvotes: 0,
    relevance: Number.isFinite(thread.relevance_score)
      ? Math.round(thread.relevance_score * 100)
      : 0,
  }));

  const [results, setResults] = useState<WorkbenchResult[]>(initialResults);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSearch = async (query: string) => {
    setIsLoading(true);
    setErrorMessage(null);

    const { response, error } = await submitDemoQuery(query);
    if (error) {
      setResults([]);
      setErrorMessage(error.message);
      setIsLoading(false);
      return;
    }

    if (!response) {
      setResults([]);
      setErrorMessage("No response received.");
      setIsLoading(false);
      return;
    }

    const threads = response.evidence_result?.threads ?? [];
    const mappedResults: WorkbenchResult[] = threads.map((thread) => ({
      rank: thread.rank,
      subreddit: thread.subreddit,
      title: thread.title,
      link: thread.url,
      comments: 0,
      upvotes: 0,
      relevance: Number.isFinite(thread.relevance_score)
        ? Math.round(thread.relevance_score * 100)
        : 0,
    }));

    setResults(mappedResults);
    setIsLoading(false);
  };

  return (
    <WorkbenchLanding
      results={results}
      isLoading={isLoading}
      errorMessage={errorMessage}
      onSearch={handleSearch}
      onHowItWorksClick={() => {}}
    />
  );
}

export default App;
