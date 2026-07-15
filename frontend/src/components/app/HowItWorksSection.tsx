/**
 * Static "How it works" section for the app surface.
 *
 * Usage:
 * <HowItWorksSection onImpression={track} />
 */
import { TypographyH2 } from "@/components/ui/typography";

interface HowItWorksSectionProps {
  onImpression: () => void;
}

const HOW_IT_WORKS_STEPS = [
  {
    title: "Ask a question.",
    detail: "Describe what you're working on.",
  },
  {
    title: "Get posts and key findings.",
    detail: "Real discussions from DIY communities.",
  },
  {
    title: "Dig in further and start doing.",
    detail: "Read what's useful and get started.",
  },
];

export function HowItWorksSection({
  onImpression,
}: HowItWorksSectionProps) {
  return (
    <section onMouseEnter={onImpression}>
      <div className="mb-10 text-center">
        <TypographyH2 className="border-b-0 pb-0 text-[24px] text-[#292524] md:text-[28px]">
          How it works
        </TypographyH2>
      </div>
      <div className="mx-auto grid w-full max-w-5xl grid-cols-1 gap-10 md:grid-cols-[repeat(3,1fr)] md:gap-[48px]">
        {HOW_IT_WORKS_STEPS.map((step, index) => (
          <div key={step.title}>
            <span className="mb-6 flex h-10 w-10 items-center justify-center rounded-full bg-[#292524] text-[15px] font-semibold text-white">
              {index + 1}
            </span>
            <h3 className="mb-2 text-[18px] font-semibold leading-[1.4] tracking-[-0.01em] text-[#292524]">
              {step.title}
            </h3>
            <p className="min-h-[44px] text-[14px] leading-[1.6] text-[#6b6b6b]">
              {step.detail}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
