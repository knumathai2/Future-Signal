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

function historyFromValues(values: number[], dataAsOf: string): IssueHistoryPoint[] {
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

      const change = Number((point.value - history[index - 1].value).toFixed(1));

      if (Math.abs(change) < 5) {
        return null;
      }

      return {
        timestamp: point.timestamp,
        change,
        label: "Observed change exceeded the 5pp threshold",
      };
    })
    .filter((point): point is Issue["inflectionPoints"][number] => point !== null);

  return {
    ...seed,
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
    title: "Ceasefire framework discussions",
    description:
      "Tracks how public data reflects reassessment around a possible ceasefire framework in an ongoing regional conflict.",
    category: "Global Affairs",
    cautionLevel: "caution_high_volatility",
    values: generateHistory(54, -0.45, 22, -7, 1),
    relatedEventCandidates: [
      {
        title: "Multilateral talks resumed among involved parties",
        date: "2026-07-02T09:00:00.000Z",
        note: "Candidate context entered manually for review alongside the observed change; not presented as a cause.",
      },
      {
        title: "Regional envoy issued a public statement",
        date: "2026-06-29T09:00:00.000Z",
        note: "Candidate context entered manually for review alongside the observed change; not presented as a cause.",
      },
    ],
  },
  {
    id: "policy-rate-path",
    title: "Central bank policy-rate path this quarter",
    description:
      "Tracks how public data reflects reassessment around the policy-rate path before the quarter ends.",
    category: "Economy",
    cautionLevel: "sufficient",
    values: generateHistory(40, 0.6, -1, 0, 1.1),
    relatedEventCandidates: [],
  },
  {
    id: "legislative-majority",
    title: "Incumbent party legislative majority",
    description:
      "Tracks how public data reflects reassessment around the governing party's legislative majority question.",
    category: "Politics",
    cautionLevel: "caution_low_activity",
    values: generateHistory(52, -0.22, -1, 0, 0.8),
    relatedEventCandidates: [
      {
        title: "Opposition campaign announcement received broad coverage",
        date: "2026-06-26T09:00:00.000Z",
        note: "Candidate context entered manually for review alongside the observed change; not presented as a cause.",
      },
    ],
  },
  {
    id: "ai-oversight-bill",
    title: "AI oversight bill this session",
    description:
      "Tracks how public data reflects reassessment around the proposed AI oversight bill during the current session.",
    category: "Technology",
    cautionLevel: "caution_high_volatility",
    values: generateHistory(13, 0.35, 25, 9, 1),
    relatedEventCandidates: [
      {
        title: "Committee advanced amended bill text",
        date: "2026-07-03T09:00:00.000Z",
        note: "Candidate context entered manually for review alongside the observed change; not presented as a cause.",
      },
    ],
  },
  {
    id: "cross-border-agreement",
    title: "Cross-border agreement negotiations",
    description:
      "Tracks how public data reflects reassessment around negotiations between two governments before year-end.",
    category: "Economy",
    cautionLevel: "sufficient",
    values: generateHistory(56, 0.18, -1, 0, 0.6),
    relatedEventCandidates: [],
  },
  {
    id: "launch-schedule",
    title: "Flagship product launch schedule",
    description:
      "Tracks how public data reflects reassessment around whether an announced product launch remains on schedule.",
    category: "Technology",
    cautionLevel: "caution_low_activity",
    values: generateHistory(58, 0.4, -1, 0, 1.6),
    relatedEventCandidates: [],
  },
  {
    id: "constitutional-reform",
    title: "Constitutional reform referendum",
    description:
      "Tracks how public data reflects reassessment around the proposed constitutional reform referendum.",
    category: "Politics",
    cautionLevel: "insufficient_data",
    values: generateHistory(50, 0.05, -1, 0, 0.3, 9),
    relatedEventCandidates: [],
  },
  {
    id: "climate-accord",
    title: "Climate accord ratification",
    description:
      "Tracks how public data reflects reassessment around ratification of a proposed climate accord by major emitters.",
    category: "Global Affairs",
    cautionLevel: "sufficient",
    values: generateHistory(53, -0.05, 15, -4, 1),
    relatedEventCandidates: [
      {
        title: "Preparatory ministerial session concluded",
        date: "2026-06-24T09:00:00.000Z",
        note: "Candidate context entered manually for review alongside the observed change; not presented as a cause.",
      },
    ],
  },
];

function buildIssues(dataAsOf: string): Issue[] {
  return issueSeeds.map((seed) => buildIssue(seed, dataAsOf));
}

export const dummyIssues: Issue[] = buildIssues(dummyDataAsOf);
export const staleDummyIssues: Issue[] = buildIssues(staleDummyDataAsOf);
