import type { ThreadEvidence } from "./types/api";
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

  return (
    <WorkbenchLanding
      results={sampleThreads.map((thread) => ({
        rank: thread.rank,
        subreddit: thread.subreddit,
        title: thread.title,
        link: thread.url,
        comments: 0,
        upvotes: 0,
        relevance: Math.round(thread.relevance_score * 100),
      }))}
      isLoading={false}
      onSearch={() => {}}
      onHowItWorksClick={() => {}}
    />
  );
}

export default App;
