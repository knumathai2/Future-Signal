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

type CautionBadgeProps = {
  level: CautionLevel;
  withDetail?: boolean;
};

export function CautionBadge({ level, withDetail = false }: CautionBadgeProps) {
  const copy = CAUTION_COPY[level];

  return (
    <div className={withDetail ? "space-y-2" : undefined}>
      <span
        className={`inline-flex w-fit items-center rounded-full border px-3 py-1 text-[11px] font-bold leading-none ${copy.className}`}
      >
        {copy.label}
      </span>
      {withDetail ? (
        <p className="m-0 text-sm leading-6 text-ink-soft">{copy.detail}</p>
      ) : null}
    </div>
  );
}
