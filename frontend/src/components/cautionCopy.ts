import type { CautionLevel } from "../types/issue";

type CautionCopy = {
  label: string;
  detail: string;
  className: string;
  dotClassName: string;
};

export const CAUTION_COPY: Record<CautionLevel, CautionCopy> = {
  sufficient: {
    label: "해석 기준 충족",
    detail:
      "필요한 이력과 활동 기준을 충족했습니다. 그래도 이 수치는 " +
      "Polymarket 참여자 데이터에 반영된 기대값의 관측 흐름으로만 읽어야 합니다.",
    className: "border-line bg-line-soft text-ink-soft",
    dotClassName: "bg-ink-faint",
  },
  caution_low_activity: {
    label: "낮은 활동 주의",
    detail:
      "최근 활동 기준이 낮아 관측 변화가 크게 보일 수 있습니다. " +
      "다른 맥락과 함께 신중하게 확인해야 합니다.",
    className: "border-dashed border-line bg-card text-ink-soft",
    dotClassName: "bg-line",
  },
  caution_high_volatility: {
    label: "높은 변동성 주의",
    detail:
      "짧은 기간의 큰 움직임이 관측되어 흐름이 일시적으로 흔들릴 수 있습니다. " +
      "단일 구간만으로 해석을 확정하지 않아야 합니다.",
    className: "border-accent bg-accent-soft text-ink",
    dotClassName: "bg-accent",
  },
  insufficient_data: {
    label: "데이터 이력 부족",
    detail:
      "선택한 기간의 시작 기준점이나 비교 지점이 부족합니다. " +
      "변화 방향과 크기 해석에는 제한이 있습니다.",
    className: "border-dashed border-line bg-transparent text-ink-faint",
    dotClassName: "border border-line bg-transparent",
  },
};
