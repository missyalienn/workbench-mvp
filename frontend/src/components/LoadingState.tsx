import { useEffect, useState } from "react";
import { Progress } from "@/components/ui/progress";

const STAGES = [
  { delay: 0, message: "Planning your search..." },
  { delay: 2000, message: "Fetching community discussions..." },
  { delay: 5000, message: "Filtering and ranking results..." },
  { delay: 8000, message: "Synthesizing results..." },
  { delay: 11000, message: "Wrapping up..." },
];

export function LoadingState() {
  const [stageIndex, setStageIndex] = useState(0);

  useEffect(() => {
    const timers = STAGES.slice(1).map((stage, i) =>
      setTimeout(() => setStageIndex(i + 1), stage.delay)
    );
    return () => timers.forEach(clearTimeout);
  }, []);

  return (
    <div className="flex flex-col gap-3 py-8">
      <Progress
        indeterminate
        className="bg-[#e7e5e4] [&>div]:bg-[#b9b9da]"
      />
      <p className="text-center text-sm text-[#8f8faa]">
        {STAGES[stageIndex].message}
      </p>
    </div>
  );
}
