import { CAUTION_COPY } from "./cautionCopy";
import type { CautionLevel } from "../types/issue";

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
