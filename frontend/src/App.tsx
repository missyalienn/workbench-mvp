import { useState } from "react";
import type { ClientThread } from "./types/api";
import { submitDemoQuery } from "./services/api";
import type { WorkbenchResult } from "./components/WorkbenchLanding";
import { WorkbenchLanding } from "./components/WorkbenchLanding";

function App() {
  const sampleThreads: ClientThread[] = [
    {
      rank: 1,
      title: "Best anchors for floating shelves on drywall — no stud available?",
      subreddit: "DIY",
      url: "https://www.reddit.com/r/DIY/",
      relevance_score: 0.91,
    },
    {
      rank: 2,
      title: "How do I find studs for shelf mounting without a stud finder?",
      subreddit: "homeimprovement",
      url: "https://www.reddit.com/r/homeimprovement/",
      relevance_score: 0.83,
    },
  ];
  const initialResults: WorkbenchResult[] = sampleThreads.map((thread) => ({
    rank: thread.rank,
    subreddit: thread.subreddit,
    title: thread.title,
    link: thread.url,
    comments: 0,
    upvotes: 0,
    relevance: Math.round(thread.relevance_score * 100),
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

    const threads = response.threads ?? [];
    const mappedResults: WorkbenchResult[] = threads.map((thread) => ({
      rank: thread.rank,
      subreddit: thread.subreddit,
      title: thread.title,
      link: thread.url,
      comments: 0,
      upvotes: 0,
      relevance: Math.round(thread.relevance_score * 100),
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
