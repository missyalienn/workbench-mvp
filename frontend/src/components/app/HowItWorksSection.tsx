/**
 * Collapsible "How it works" section for the app surface.
 *
 * Usage:
 * <HowItWorksSection isOpen={isOpen} animationKey={animationKey} onToggle={toggle} onImpression={track} />
 */
import { ChevronUp } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { TypographyH2 } from "@/components/ui/typography";

interface HowItWorksSectionProps {
  isOpen: boolean;
  animationKey: number;
  onToggle: () => void;
  onImpression: () => void;
}

const HOW_IT_WORKS_STEPS = [
  { title: "Planner Agent", description: "Decomposes your question into targeted search queries" },
  { title: "Retriever Agent", description: "Retrieves relevant threads and top comments" },
  { title: "Ranker Agent", description: "Ranks results by semantic relevance to your question" },
  { title: "Synthesizer Agent", description: "Synthesizes key findings and surfaces original sources" },
];

export function HowItWorksSection({
  isOpen,
  animationKey,
  onToggle,
  onImpression,
}: HowItWorksSectionProps) {
  return (
    <section onMouseEnter={onImpression}>
      <div className="mb-4 flex items-center justify-center gap-2">
        <TypographyH2 className="border-b-0 pb-0 text-[24px] text-[#262162] md:text-[28px]">
          How it works
        </TypographyH2>
        <button
          onClick={onToggle}
          aria-label={isOpen ? "Collapse how it works" : "Expand how it works"}
          className="mt-0.5 flex h-7 w-7 items-center justify-center rounded-full text-[#8f8faa] transition-colors hover:bg-[#ebebf4] hover:text-[#262162]"
        >
          <ChevronUp
            className="h-4 w-4 transition-transform duration-300"
            style={{ transform: isOpen ? "rotate(0deg)" : "rotate(180deg)" }}
          />
        </button>
      </div>

      <div
        className="overflow-hidden transition-all duration-300 ease-in-out"
        style={{ maxHeight: isOpen ? "600px" : "0px", opacity: isOpen ? 1 : 0 }}
      >
        <Card className="mx-auto max-w-2xl border-[#e7e5e4] bg-white shadow-sm">
          <CardContent className="p-0">
            <div className="divide-y divide-[#e7e5e4]">
              {HOW_IT_WORKS_STEPS.map((step, index) => (
                <div
                  key={`${step.title}-${animationKey}`}
                  className="relative flex items-start gap-4 px-5 py-4 md:px-6"
                  style={{
                    animation: isOpen ? "fadeSlideIn 400ms ease-out both" : "none",
                    animationDelay: `${index * 150}ms`,
                  }}
                >
                  <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#262162] text-[11px] font-semibold text-white">
                    {index + 1}
                  </span>
                  <div>
                    <p className="text-base font-semibold text-[#262162]">{step.title}</p>
                    <p className="mt-0.5 text-[15px] leading-6 text-[#5b5b73]">{step.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </section>
  );
}
