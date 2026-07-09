import type { CautionLevel } from "../types/issue";

type CautionCopy = {
  label: string;
  detail: string;
  className: string;
};

export const CAUTION_COPY: Record<CautionLevel, CautionCopy> = {
  sufficient: {
    label: "기본 해석 주의",
    detail:
      "현재 데이터 지점과 활동 수준이 기준을 충족하지만, 공개 데이터에 반영된 기대값으로만 신중하게 읽어야 합니다.",
    className: "border-line bg-line-soft text-ink-soft",
  },
  caution_low_activity: {
    label: "활동 수준 주의",
    detail:
      "최근 활동 수준이 낮게 관측되어 같은 폭의 변화도 더 크게 보일 수 있습니다. 추가 맥락과 함께 확인해야 합니다.",
    className: "border-line bg-line-soft text-ink-soft",
  },
  caution_high_volatility: {
    label: "변동성 해석 주의",
    detail:
      "짧은 기간의 큰 움직임과 잦은 변동이 함께 관측되었습니다. 흐름을 단정하지 말고 추가 확인이 필요합니다.",
    className: "border-accent-soft bg-accent-soft text-ink-soft",
  },
  insufficient_data: {
    label: "이력 부족",
    detail:
      "선택한 기간의 흐름을 읽기에 필요한 시계열 지점이 충분하지 않습니다.",
    className: "border-dashed border-line bg-transparent text-ink-faint",
  },
};
