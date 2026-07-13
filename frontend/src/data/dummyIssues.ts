import type { Issue, IssueHistoryPoint } from "../types/issue";

export const dummyDataAsOf = "2026-07-08T09:00:00.000Z";
export const staleDummyDataAsOf = "2026-07-07T23:00:00.000Z";

const DAY_MS = 24 * 60 * 60 * 1000;

type IssueSeed = Omit<
  Issue,
  | "currentExpectationValue"
  | "change24h"
  | "change7d"
  | "change30d"
  | "dataAsOf"
  | "history"
  | "inflectionPoints"
> & {
  values: number[];
};

function generateHistory(
  base: number,
  drift: number,
  jumpAt: number,
  jumpMagnitude: number,
  wiggle: number,
  days = 31,
): number[] {
  const values: number[] = [];
  let current = base;

  for (let day = 0; day < days; day += 1) {
    if (day > 0) {
      current += drift + Math.sin(day / 3) * wiggle * 0.35;
    }

    if (day === jumpAt) {
      current += jumpMagnitude;
    }

    values.push(Math.max(3, Math.min(97, Number(current.toFixed(1)))));
  }

  return values;
}

function historyFromValues(
  values: number[],
  dataAsOf: string,
): IssueHistoryPoint[] {
  const dataAsOfTime = new Date(dataAsOf).getTime();
  const startTime = dataAsOfTime - (values.length - 1) * DAY_MS;

  return values.map((value, index) => ({
    timestamp: new Date(startTime + index * DAY_MS).toISOString(),
    value,
  }));
}

function buildIssue(seed: IssueSeed, dataAsOf: string): Issue {
  const history = historyFromValues(seed.values, dataAsOf);
  const currentIndex = seed.values.length - 1;
  const currentExpectationValue = seed.values[currentIndex];
  const value24hAgo = seed.values[Math.max(0, currentIndex - 1)];
  const value7dAgo = seed.values[Math.max(0, currentIndex - 7)];
  const value30dAgo = seed.values[0];

  const inflectionPoints = history
    .map((point, index) => {
      if (index === 0) {
        return null;
      }

      const change = Number(
        (point.value - history[index - 1].value).toFixed(1),
      );

      if (Math.abs(change) < 5) {
        return null;
      }

      return {
        timestamp: point.timestamp,
        change,
        label: "관측된 변화가 5%p 기준선을 넘었습니다",
      };
    })
    .filter(
      (point): point is Issue["inflectionPoints"][number] => point !== null,
    );

  return {
    ...seed,
    sourceTitle: seed.sourceTitle ?? seed.title,
    displaySubtitle: seed.displaySubtitle ?? seed.description,
    topicLabel: seed.topicLabel ?? seed.category,
    resolutionCondition: seed.resolutionCondition ?? seed.description,
    currentExpectationValue,
    change24h: Number((currentExpectationValue - value24hAgo).toFixed(1)),
    change7d: Number((currentExpectationValue - value7dAgo).toFixed(1)),
    change30d: Number((currentExpectationValue - value30dAgo).toFixed(1)),
    dataAsOf,
    history,
    inflectionPoints,
  };
}

const issueSeeds: IssueSeed[] = [
  {
    id: "ceasefire-framework",
    title: "휴전 협의 틀 논의",
    description:
      "진행 중인 지역 분쟁에서 가능한 휴전 협의 틀을 둘러싼 재평가가 공개 데이터에 어떻게 반영되는지 관찰합니다.",
    category: "Global Affairs",
    cautionLevel: "caution_high_volatility",
    values: generateHistory(54, -0.45, 22, -7, 1),
    relatedEventCandidates: [
      {
        title: "관련 당사자 간 다자 협의 재개",
        date: "2026-07-02T09:00:00.000Z",
        note: "관측된 변화와 함께 검토할 수 있도록 수동 입력한 후보 맥락입니다. 원인으로 제시하지 않습니다.",
      },
      {
        title: "지역 특사가 공개 성명 발표",
        date: "2026-06-29T09:00:00.000Z",
        note: "관측된 변화와 함께 검토할 수 있도록 수동 입력한 후보 맥락입니다. 원인으로 제시하지 않습니다.",
      },
    ],
  },
  {
    id: "policy-rate-path",
    title: "이번 분기 중앙은행 기준금리 경로",
    description:
      "분기 종료 전 기준금리 경로를 둘러싼 재평가가 공개 데이터에 어떻게 반영되는지 관찰합니다.",
    category: "Economy",
    cautionLevel: "sufficient",
    values: generateHistory(40, 0.6, -1, 0, 1.1),
    relatedEventCandidates: [],
  },
  {
    id: "legislative-majority",
    title: "여당의 의회 과반 유지 여부",
    description:
      "여당의 의회 과반 유지 여부를 둘러싼 재평가가 공개 데이터에 어떻게 반영되는지 관찰합니다.",
    category: "Politics",
    cautionLevel: "caution_low_activity",
    values: generateHistory(52, -0.22, -1, 0, 0.8),
    relatedEventCandidates: [
      {
        title: "야권 캠페인 발표가 폭넓게 보도됨",
        date: "2026-06-26T09:00:00.000Z",
        note: "관측된 변화와 함께 검토할 수 있도록 수동 입력한 후보 맥락입니다. 원인으로 제시하지 않습니다.",
      },
    ],
  },
  {
    id: "ai-oversight-bill",
    title: "이번 회기 AI 감독 법안",
    description:
      "이번 회기 AI 감독 법안 제안을 둘러싼 재평가가 공개 데이터에 어떻게 반영되는지 관찰합니다.",
    category: "Technology",
    cautionLevel: "caution_high_volatility",
    values: generateHistory(13, 0.35, 25, 9, 1),
    relatedEventCandidates: [
      {
        title: "위원회가 수정 법안 문안을 다음 단계로 넘김",
        date: "2026-07-03T09:00:00.000Z",
        note: "관측된 변화와 함께 검토할 수 있도록 수동 입력한 후보 맥락입니다. 원인으로 제시하지 않습니다.",
      },
    ],
  },
  {
    id: "cross-border-agreement",
    title: "국경 간 합의 협상",
    description:
      "연말 전 두 정부 간 협상을 둘러싼 재평가가 공개 데이터에 어떻게 반영되는지 관찰합니다.",
    category: "Economy",
    cautionLevel: "sufficient",
    values: generateHistory(56, 0.18, -1, 0, 0.6),
    relatedEventCandidates: [],
  },
  {
    id: "launch-schedule",
    title: "주요 제품 출시 일정",
    description:
      "발표된 제품 출시 일정에 대한 재평가가 공개 데이터에 어떻게 반영되는지 관찰합니다.",
    category: "Technology",
    cautionLevel: "caution_low_activity",
    values: generateHistory(58, 0.4, -1, 0, 1.6),
    relatedEventCandidates: [],
  },
  {
    id: "constitutional-reform",
    title: "헌법 개정 국민투표",
    description:
      "제안된 헌법 개정 국민투표를 둘러싼 재평가가 공개 데이터에 어떻게 반영되는지 관찰합니다.",
    category: "Politics",
    cautionLevel: "insufficient_data",
    values: generateHistory(50, 0.05, -1, 0, 0.3, 9),
    relatedEventCandidates: [],
  },
  {
    id: "climate-accord",
    title: "기후 협약 비준",
    description:
      "주요 배출국의 기후 협약 비준을 둘러싼 재평가가 공개 데이터에 어떻게 반영되는지 관찰합니다.",
    category: "Global Affairs",
    cautionLevel: "sufficient",
    values: generateHistory(53, -0.05, 15, -4, 1),
    relatedEventCandidates: [
      {
        title: "준비 장관급 회의 종료",
        date: "2026-06-24T09:00:00.000Z",
        note: "관측된 변화와 함께 검토할 수 있도록 수동 입력한 후보 맥락입니다. 원인으로 제시하지 않습니다.",
      },
    ],
  },
];

function buildIssues(dataAsOf: string): Issue[] {
  return issueSeeds.map((seed) => buildIssue(seed, dataAsOf));
}

export const dummyIssues: Issue[] = buildIssues(dummyDataAsOf);
export const staleDummyIssues: Issue[] = buildIssues(staleDummyDataAsOf);
