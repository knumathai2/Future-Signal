import { useMemo, useState } from "react";
import { CautionBadge } from "./CautionBadge";
import { CAUTION_COPY } from "./cautionCopy";
import { IssueTrendChart } from "./IssueTrendChart";
import { MetricTile } from "./MetricTile";
import {
  formatCategoryLabel,
  formatDataTimestamp,
  formatExpectationValue,
  formatPercentagePointChange,
  formatShortDate,
  windowLabel,
} from "../utils/format";
import type { ChartWindow, DataStatus, Issue } from "../types/issue";

type IssueDetailProps = {
  issue: Issue;
  dataStatus?: DataStatus;
  onBack: () => void;
};

const CHART_WINDOWS: ChartWindow[] = ["24h", "7d", "30d"];

function changeForWindow(
  issue: Issue,
  chartWindow: ChartWindow,
): number | null | undefined {
  if (chartWindow === "24h") {
    return issue.change24h;
  }

  if (chartWindow === "7d") {
    return issue.change7d;
  }

  return issue.change30d ?? issue.change7d;
}

function buildSummary(issue: Issue, chartWindow: ChartWindow): string {
  const change = changeForWindow(issue, chartWindow);
  const movementSentence =
    change === null || change === undefined || Number.isNaN(change)
      ? `공개 데이터에 반영된 기대값은 ${windowLabel(
          chartWindow,
        )} 변화 계산에 필요한 기준 데이터가 충분하지 않습니다`
      : `${
          Math.abs(change) < 0.05
            ? "공개 데이터에 반영된 기대값은 이전 관측값과 비슷한 수준으로 관측되었습니다"
            : change > 0
              ? "공개 데이터에 반영된 기대값은 상승 방향으로 관측되었습니다"
              : "공개 데이터에 반영된 기대값은 하락 방향으로 관측되었습니다"
        } (${formatPercentagePointChange(change)})`;
  const marker = issue.inflectionPoints[0];
  const markerSentence = marker
    ? `저장된 이력의 기준선 통과 표시는 ${formatShortDate(
        marker.timestamp,
      )}에 있으며, 관측된 변화는 ${formatPercentagePointChange(marker.change)}입니다.`
    : "저장된 이력에는 기준선 통과 표시가 없습니다.";
  const relatedSentence = issue.relatedEventCandidates?.length
    ? "관련 사건 후보는 맥락 확인용이며 원인으로 제시하지 않습니다."
    : "이 이슈에는 관련 사건 후보가 등록되어 있지 않습니다.";

  return `최근 ${windowLabel(
    chartWindow,
  )} 동안 ${movementSentence}. ${markerSentence} ${relatedSentence} ${
    CAUTION_COPY[issue.cautionLevel].detail
  }`;
}

export function IssueDetail({ issue, dataStatus = "ready", onBack }: IssueDetailProps) {
  const [chartWindow, setChartWindow] = useState<ChartWindow>("7d");

  const summary = useMemo(
    () => buildSummary(issue, chartWindow),
    [issue, chartWindow],
  );

  return (
    <div className="mx-auto min-h-screen w-full max-w-[1180px] px-4 py-6 sm:px-8 lg:px-10 lg:py-10">
      <button
        type="button"
        onClick={onBack}
        className="text-sm font-semibold text-ink-soft transition hover:text-accent"
      >
        대시보드로 돌아가기
      </button>

      <header className="mt-5">
        {dataStatus === "error" ? (
          <div className="mb-4 rounded-lg border border-line bg-card px-4 py-3">
            <h2 className="text-sm font-bold text-ink">
              마지막으로 확인 가능한 데이터를 표시합니다
            </h2>
            <p className="mt-1 text-sm leading-6 text-ink-soft">
              최신 새로고침이 완료되지 않아 대시보드와 같은 백업 이슈 목록을
              기준으로 상세 화면을 표시합니다.
            </p>
          </div>
        ) : null}

        <div className="flex flex-wrap items-center gap-3">
          <span className="text-[11px] font-bold text-ink-faint">
            {formatCategoryLabel(issue.category)}
          </span>
          <CautionBadge level={issue.cautionLevel} />
        </div>
        <h1 className="mt-3 max-w-4xl text-3xl font-bold text-ink">
          {issue.title}
        </h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-ink-soft">
          {issue.description}
        </p>
        <p className="mt-2 text-xs text-ink-faint">
          데이터 기준 시각: {formatDataTimestamp(issue.dataAsOf)}
        </p>
      </header>

      <section className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-4">
        <MetricTile
          primary
          label="공개 데이터에 반영된 기대값"
          value={formatExpectationValue(issue.currentExpectationValue)}
        />
        <MetricTile
          label="24시간 관측 변화"
          value={formatPercentagePointChange(issue.change24h)}
        />
        <MetricTile
          label="7일 관측 변화"
          value={formatPercentagePointChange(issue.change7d)}
        />
        <MetricTile
          label="30일 관측 변화"
          value={formatPercentagePointChange(issue.change30d ?? issue.change7d)}
        />
      </section>

      <section className="mt-4 rounded-lg border border-line bg-card px-4 py-3">
        <CautionBadge level={issue.cautionLevel} withDetail />
        <p className="mt-2 text-sm leading-6 text-ink-soft">
          이 값은 공개 데이터에 반영된 기대값이며 실제 사건에 대한 확정 사실이
          아닙니다. 데이터가 불완전하거나 변동성이 클 수 있습니다.
        </p>
      </section>

      <section className="mt-8">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <h2 className="text-lg font-bold text-ink">
            공개 데이터에 반영된 기대값 추이
          </h2>
          <div className="flex gap-2" aria-label="차트 기간">
            {CHART_WINDOWS.map((windowOption) => (
              <button
                key={windowOption}
                type="button"
                onClick={() => setChartWindow(windowOption)}
                className={
                  chartWindow === windowOption
                    ? "rounded-full border border-ink bg-ink px-3 py-1.5 text-xs font-bold text-card"
                    : "rounded-full border border-line px-3 py-1.5 text-xs font-bold text-ink-soft transition hover:border-accent hover:text-accent"
                }
              >
                {windowLabel(windowOption)}
              </button>
            ))}
          </div>
        </div>
        <div className="mt-3">
          <IssueTrendChart issue={issue} windowKey={chartWindow} />
        </div>
      </section>

      <section className="mt-10">
        <h2 className="text-lg font-bold text-ink">관련 사건 후보</h2>
        <p className="mt-1 text-sm leading-6 text-ink-faint">
          관측된 변화와 함께 확인할 수 있도록 수동으로 정리한 후보 맥락입니다.
          원인으로 제시하지 않습니다.
        </p>

        {issue.relatedEventCandidates?.length ? (
          <div className="mt-4 space-y-3">
            {issue.relatedEventCandidates.map((event) => (
              <article
                key={`${event.date}-${event.title}`}
                className="rounded-lg border border-line bg-card px-4 py-3"
              >
                <div className="text-xs font-semibold text-ink-faint">
                  {formatShortDate(event.date)}
                </div>
                <h3 className="mt-1 text-sm font-bold text-ink">{event.title}</h3>
                <p className="mt-1 text-sm leading-6 text-ink-soft">{event.note}</p>
              </article>
            ))}
          </div>
        ) : (
          <p className="mt-4 rounded-lg border border-dashed border-line px-4 py-4 text-sm text-ink-faint">
            이 이슈에는 등록된 관련 사건 후보가 없습니다.
          </p>
        )}
      </section>

      <section className="mt-10 rounded-lg border border-line bg-card p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-lg font-bold text-ink">이슈 요약</h2>
          <span className="text-[11px] font-semibold text-ink-faint">
            템플릿 기반 데이터 요약
          </span>
        </div>
        <p className="mt-4 max-w-4xl text-sm leading-7 text-ink">{summary}</p>
        <p className="mt-4 border-t border-line-soft pt-3 text-xs leading-6 text-ink-faint">
          이 요약은 현재 데이터 계약에 맞춘 템플릿으로 생성되며, 맥락이
          불완전할 수 있습니다. 어떤 종류의 조언도 아닙니다.
        </p>
      </section>

      <footer className="mt-10 border-t border-line pt-5 text-xs leading-6 text-ink-faint">
        <p className="max-w-3xl">
          Outlook Signals는 공개 데이터 기반의 정보 분석 및 이슈 관찰 서비스입니다.
          금융, 법률, 정치 또는 그 밖의 전문적 조언을 제공하지 않습니다.
        </p>
        <p className="mt-2 max-w-3xl">
          이 지표는 Polymarket 공개 데이터에 반영된 기대값의 변화를 보여줍니다.
          전체 대중의 판단을 대표하지 않으며, 데이터 활동 수준과 변동성에 따라
          해석에 주의가 필요합니다.
        </p>
      </footer>
    </div>
  );
}
