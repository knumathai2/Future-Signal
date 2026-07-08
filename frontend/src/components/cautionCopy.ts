import type { CautionLevel } from "../types/issue";

type CautionCopy = {
  label: string;
  detail: string;
  className: string;
};

export const CAUTION_COPY: Record<CautionLevel, CautionCopy> = {
  sufficient: {
    label: "Data sufficient",
    detail:
      "Data points and activity level are above the monitoring threshold. Interpretation still requires caution.",
    className: "border-line bg-line-soft text-ink-soft",
  },
  caution_low_activity: {
    label: "Activity caution",
    detail:
      "Activity level is below the usual threshold, so interpretation requires extra caution.",
    className: "border-accent-soft bg-accent-soft text-[#7a4a2a]",
  },
  caution_high_volatility: {
    label: "Volatility caution",
    detail:
      "A large recent move appears with elevated volatility. Further verification is needed.",
    className: "border-accent bg-accent-soft text-ink",
  },
  insufficient_data: {
    label: "Insufficient data",
    detail:
      "There are not enough time-series points for a complete trend reading.",
    className: "border-dashed border-line bg-transparent text-ink-faint",
  },
};
