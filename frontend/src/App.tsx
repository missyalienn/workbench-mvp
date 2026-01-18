import type { ThreadEvidence } from "./types/api";
import { Footer } from "./components/Footer";
import { Header } from "./components/Header";
import { LoadingState } from "./components/LoadingState";
import { QueryBox } from "./components/QueryBox";
import { ResultsList } from "./components/ResultsList";

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
    <main className="min-h-screen bg-white text-black">
      <div className="max-w-5xl mx-auto px-6 py-14 space-y-16">
        <Header />

        <section className="space-y-8">
          <div className="text-center space-y-3">
            <h2 className="text-[40px] font-semibold tracking-[-0.04em] leading-none">
              Ask a question.
            </h2>
            <p className="text-xl text-[#999999]">
              How do I hang floating shelves?
            </p>
          </div>
          <QueryBox onSubmit={() => {}} />
        </section>

        <section className="space-y-4">
          <h3 className="text-center text-[40px] font-semibold tracking-[-0.04em] text-[#999999]">
            Ranked results, verified sources.
          </h3>
          <ResultsList threads={sampleThreads} />
        </section>

        <Footer />
      </div>
    </main>
  );
}

export default App;
