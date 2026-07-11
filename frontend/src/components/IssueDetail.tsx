import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { SiteHeader } from "./AppShell";
import { CautionBadge } from "./CautionBadge";
import { GlobalFooter, ShortCautionNotice } from "./InformationNotice";
import { IssueReportCard } from "./IssueReportCard";
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
import type {
  ChartWindow,
  DataStatus,
  Issue,
  IssueReportLoadState,
} from "../types/issue";
import { focusRouteHeading } from "../utils/focus";

type IssueDetailProps = {
  issue: Issue;
  dataStatus?: DataStatus;
  reportState: IssueReportLoadState;
  historyStatus: "loading" | "ready" | "error";
  backTo: string;
  onGenerateReport: (refreshContext: boolean) => Promise<void>;
  generationPending: boolean;
  generationActionError: boolean;
};

const CHART_WINDOWS: ChartWindow[] = ["24h", "7d", "30d"];

export function IssueDetail({
  issue,
  dataStatus = "ready",
  reportState,
  historyStatus,
  backTo,
  onGenerateReport,
  generationPending,
  generationActionError,
}: IssueDetailProps) {
  const [chartWindow, setChartWindow] = useState<ChartWindow>("7d");

  useEffect(() => {
    const frame = window.requestAnimationFrame(focusRouteHeading);
    return () => window.cancelAnimationFrame(frame);
  }, [issue.id]);

  return (
    <div className="mx-auto min-h-screen w-full max-w-[1180px] px-4 py-4 sm:px-8 sm:py-6 lg:px-10 lg:py-8">
      <SiteHeader dataAsOf={issue.dataAsOf} />

      <main
        id="main-content"
        data-route-main
        tabIndex={-1}
        aria-labelledby="issue-detail-title"
        className="outline-none"
      >
        <nav
          aria-label="현재 위치"
          className="mt-5 flex flex-wrap items-center gap-2 text-xs"
        >
          <Link
            to="/"
            className="inline-flex min-h-11 items-center font-semibold text-ink-soft hover:text-accent"
          >
            홈
          </Link>
          <span aria-hidden="true" className="text-ink-faint">
            /
          </span>
          <Link
            to="/issues"
            className="inline-flex min-h-11 items-center font-semibold text-ink-soft hover:text-accent"
          >
            전체 이슈
          </Link>
          <span aria-hidden="true" className="text-ink-faint">
            /
          </span>
          <span aria-current="page" className="font-semibold text-ink-faint">
            현재 이슈
          </span>
        </nav>

        <Link
          to={backTo}
          className="inline-flex min-h-11 items-center text-sm font-semibold text-ink-soft transition hover:text-accent"
        >
          ← 이전 화면으로 돌아가기
        </Link>

        <header className="mt-2">
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
              {issue.topicLabel ?? formatCategoryLabel(issue.category)}
            </span>
            <CautionBadge level={issue.cautionLevel} />
          </div>
          <h1
            id="issue-detail-title"
            className="mt-3 max-w-4xl text-3xl font-bold text-ink"
          >
            {issue.title}
          </h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-ink-soft">
            {issue.displaySubtitle ?? issue.description}
          </p>
          {issue.sourceTitle && issue.sourceTitle !== issue.title ? (
            <p className="mt-1 max-w-3xl text-xs leading-5 text-ink-faint">
              원문 시장 질문: {issue.sourceTitle}
            </p>
          ) : null}
          <p className="mt-2 text-xs text-ink-faint">
            데이터 기준 시각: {formatDataTimestamp(issue.dataAsOf)}
          </p>
        </header>

        <section className="mt-6 grid grid-cols-2 gap-3 md:grid-cols-4">
          <MetricTile
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
            value={formatPercentagePointChange(issue.change30d)}
          />
        </section>

        <ShortCautionNotice
          context="detail"
          cautionLevel={issue.cautionLevel}
          dataAsOf={issue.dataAsOf}
          className="mt-4"
        />

        <section className="mt-4 rounded-lg border border-line bg-card px-4 py-3">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <CautionBadge level={issue.cautionLevel} withDetail />
            <Link
              to="/methodology"
              className="inline-flex min-h-11 items-center text-xs font-bold text-ink-soft transition hover:text-accent"
            >
              해석 기준 자세히 보기
            </Link>
          </div>
        </section>

        <section className="mt-8">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <h2 className="text-lg font-bold text-ink">
              공개 데이터에 반영된 기대값 추이
            </h2>
            <div className="flex gap-2" role="group" aria-label="차트 기간">
              {CHART_WINDOWS.map((windowOption) => (
                <button
                  key={windowOption}
                  type="button"
                  onClick={() => setChartWindow(windowOption)}
                  aria-pressed={chartWindow === windowOption}
                  className={
                    chartWindow === windowOption
                      ? "inline-flex min-h-11 items-center rounded-full border border-ink bg-ink px-4 text-xs font-bold text-card"
                      : "inline-flex min-h-11 items-center rounded-full border border-line px-4 text-xs font-bold text-ink-soft transition hover:border-accent hover:text-accent"
                  }
                >
                  {windowLabel(windowOption)}
                </button>
              ))}
            </div>
          </div>
          <div className="mt-4 rounded-lg border border-line bg-card px-4 py-3">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <CautionBadge level={issue.cautionLevel} />
              <span className="text-xs font-semibold text-ink-faint">
                데이터 기준 시각: {formatDataTimestamp(issue.dataAsOf)}
              </span>
            </div>
            <p className="mt-2 text-xs leading-5 text-ink-faint">
              차트 표시는 공개 데이터의 관측 흐름과 5pp 기준선 통과 여부만
              보여주며, 관련 사건 후보를 원인으로 제시하지 않습니다.
            </p>
          </div>
          <div className="mt-3" aria-live="polite">
            {historyStatus === "loading" ? (
              <div className="rounded-lg border border-line bg-card p-4">
                <div className="h-[260px] animate-pulse rounded-lg bg-line-soft sm:h-[300px]" />
                <p className="mt-3 text-xs font-semibold text-ink-faint">
                  차트 이력을 불러오는 중입니다
                </p>
              </div>
            ) : historyStatus === "error" ? (
              <div className="rounded-lg border border-line bg-card px-5 py-12 text-center">
                <h3 className="text-sm font-bold text-ink">
                  차트 이력을 불러오지 못했습니다
                </h3>
                <p className="mt-2 text-sm leading-6 text-ink-soft">
                  현재 값과 변화 지표는 계속 확인할 수 있습니다.
                </p>
              </div>
            ) : (
              <IssueTrendChart issue={issue} windowKey={chartWindow} />
            )}
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
                  <h3 className="mt-1 text-sm font-bold text-ink">
                    {event.title}
                  </h3>
                  <p className="mt-1 text-sm leading-6 text-ink-soft">
                    {event.note}
                  </p>
                </article>
              ))}
            </div>
          ) : (
            <p className="mt-4 rounded-lg border border-dashed border-line px-4 py-4 text-sm text-ink-faint">
              이 이슈에는 등록된 관련 사건 후보가 없습니다.
            </p>
          )}
        </section>

        <IssueReportCard
          issueId={issue.id}
          reportState={reportState}
          issueDataAsOf={issue.dataAsOf}
          onGenerate={onGenerateReport}
          generationPending={generationPending}
          generationActionError={generationActionError}
        />
      </main>

      <GlobalFooter className="mt-10" />
    </div>
  );
}
