import { CAUTION_COPY } from "./cautionCopy";
import type { CautionLevel } from "../types/issue";

type CautionBadgeProps = {
  level: CautionLevel;
  withDetail?: boolean;
};

export function CautionBadge({ level, withDetail = false }: CautionBadgeProps) {
  const copy = CAUTION_COPY[level];

  return (
    <div className={withDetail ? "max-w-2xl space-y-2 text-left" : "text-left"}>
      <span
        aria-label={`${copy.label}: ${copy.detail}`}
        className={[
          "inline-flex max-w-full items-center gap-1.5 rounded-full border",
          "px-3 py-1 text-[11px] font-bold leading-tight",
          copy.className,
        ].join(" ")}
        title={withDetail ? undefined : copy.detail}
      >
        <span
          aria-hidden="true"
          className={`h-1.5 w-1.5 shrink-0 rounded-full ${copy.dotClassName}`}
        />
        <span className="whitespace-normal">{copy.label}</span>
      </span>
      {withDetail ? (
        <p className="m-0 text-sm leading-6 text-ink-soft">{copy.detail}</p>
      ) : null}
    </div>
  );
}
