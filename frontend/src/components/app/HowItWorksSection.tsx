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
  "Ask a question.",
  "Get key findings and relevant posts from DIY communities all over Reddit.",
  "Dig in further and get it done.",
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
        <TypographyH2 className="border-b-0 pb-0 text-[24px] text-[#292524] md:text-[28px]">
          How it works
        </TypographyH2>
        <button
          onClick={onToggle}
          aria-label={isOpen ? "Collapse how it works" : "Expand how it works"}
          className="mt-0.5 flex h-7 w-7 items-center justify-center rounded-full text-[#78716c] transition-colors hover:bg-[#f5f5f4] hover:text-[#292524]"
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
        <Card className="mx-auto max-w-2xl border-[#e7e5e4] bg-[#fafaf9] shadow-sm">
          <CardContent className="p-0">
            <div className="divide-y divide-[#e7e5e4]">
              {HOW_IT_WORKS_STEPS.map((step, index) => (
                <div
                  key={`${step}-${animationKey}`}
                  className="relative flex items-start gap-4 px-5 py-4 md:px-6"
                  style={{
                    animation: isOpen ? "fadeSlideIn 400ms ease-out both" : "none",
                    animationDelay: `${index * 150}ms`,
                  }}
                >
                  <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#292524] text-[11px] font-semibold text-white">
                    {index + 1}
                  </span>
                  <p className="text-[15px] leading-6 text-[#57534e]">{step}</p>
                </div>
              ))}
            </div>
            <div className="border-t border-[#e7e5e4] px-5 py-4 md:px-6">
              <a
                href="https://github.com/missyalienn/workbench-mvp"
                target="_blank"
                rel="noreferrer"
                className="text-sm font-medium text-[#57534e] underline-offset-4 transition-colors hover:text-[#292524] hover:underline"
              >
                View the architecture →
              </a>
            </div>
          </CardContent>
        </Card>
      </div>
    </section>
  );
}
