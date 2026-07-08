import type { CautionLevel } from "../types/issue";

type CautionCopy = {
  label: string;
  detail: string;
  className: string;
};

export const CAUTION_COPY: Record<CautionLevel, CautionCopy> = {
  sufficient: {
    label: "해석 주의",
    detail:
      "데이터 지점과 활동 수준이 기준 이상이지만, 공개 데이터에 반영된 기대값은 신중하게 해석해야 합니다.",
    className: "border-line bg-line-soft text-ink-soft",
  },
  caution_low_activity: {
    label: "낮은 활동 주의",
    detail:
      "활동 수준이 기준보다 낮아 관측된 변화를 더 신중하게 해석해야 합니다.",
    className: "border-accent-soft bg-accent-soft text-[#7a4a2a]",
  },
  caution_high_volatility: {
    label: "변동성 주의",
    detail:
      "최근 큰 변화와 높은 변동성이 함께 관측되어 추가 확인이 필요합니다.",
    className: "border-accent bg-accent-soft text-ink",
  },
  insufficient_data: {
    label: "데이터 부족",
    detail:
      "완전한 흐름을 읽기에는 시계열 지점이 충분하지 않습니다.",
    className: "border-dashed border-line bg-transparent text-ink-faint",
  },
};
