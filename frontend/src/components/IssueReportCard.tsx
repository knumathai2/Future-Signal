import { useEffect, useMemo, useState } from "react";
import { ShortCautionNotice } from "./InformationNotice";
import type {
  IssueReportContent,
  IssueReportLoadState,
} from "../types/issue";
import { formatDataTimestamp } from "../utils/format";
import {
  getVisibleSections,
} from "../utils/reportParser";

type IssueReportCardProps = {
  issueId: string;
  reportState: IssueReportLoadState;
  fallbackSummary: string;
  issueDataAsOf: string;
};

/**
 * Report reference time: for a successful report, use its own data_as_of.
 */
function reportDataAsOf(
  reportState: IssueReportLoadState,
  fallbackDataAsOf: string,
): string {
  return reportState.status === "success"
    ? reportState.report.data_as_of
    : fallbackDataAsOf;
}

// ---------------------------------------------------------------------------
// Non-success states
// ---------------------------------------------------------------------------

function LoadingBody() {
  return (
    <div className="mt-4 rounded-lg border border-line-soft px-4 py-4">
      <div className="h-3 w-40 animate-pulse rounded-full bg-line" />
      <div className="mt-3 h-3 w-full max-w-3xl animate-pulse rounded-full bg-line-soft" />
      <div className="mt-2 h-3 w-2/3 animate-pulse rounded-full bg-line-soft" />
    </div>
  );
}

function NotYetGeneratedBody() {
  return (
    <div className="mt-4 rounded-lg border border-dashed border-line px-4 py-4">
      <h3 className="text-sm font-bold text-ink">
        저장된 템플릿 요약이 아직 없습니다
      </h3>
      <p className="mt-2 max-w-3xl text-sm leading-6 text-ink-soft">
        이슈 정보와 차트는 계속 확인할 수 있습니다. 요약이 생성되면 이슈
        설명과 조건부 전개를 고정된 섹션 형식으로 표시합니다.
      </p>
    </div>
  );
}

function ErrorBody({ fallbackSummary }: { fallbackSummary: string }) {
  return (
    <div className="mt-4 rounded-lg border border-line px-4 py-4">
      <h3 className="text-sm font-bold text-ink">
        저장된 요약을 불러오지 못했습니다
      </h3>
      <p className="mt-2 max-w-3xl text-sm leading-6 text-ink-soft">
        아래 문장은 현재 화면 데이터로 만든 임시 요약입니다. 저장된 템플릿
        요약이 아니며, 데이터 기준 시각과 해석 주의 상태를 함께 확인해야 합니다.
      </p>
      <p className="mt-4 max-w-4xl rounded-lg bg-accent-soft px-4 py-3 text-sm leading-7 text-ink">
        {fallbackSummary}
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// One-section-at-a-time card navigation
// ---------------------------------------------------------------------------

function SectionNavigator({
  content,
}: {
  content: IssueReportContent;
}) {
  const visibleSections = useMemo(
    () => getVisibleSections(content),
    [content],
  );

  const [activeIndex, setActiveIndex] = useState(0);

  // Reset/clamp when visible sections change
  useEffect(() => {
    setActiveIndex((prev) => {
      if (prev >= visibleSections.length) {
        return 0;
      }
      return prev;
    });
  }, [visibleSections]);

  const currentSection = visibleSections[activeIndex];
  const sectionValue = content[currentSection.key];
  const isFirst = activeIndex === 0;
  const isLast = activeIndex === visibleSections.length - 1;

  return (
    <div className="mt-4">
      {/* Section content area — aria-live for screen readers */}
      <div
        aria-live="polite"
        aria-atomic="true"
        className="rounded-lg border border-line-soft bg-card px-4 py-4"
        style={{ minHeight: "7rem" }}
      >
        <h3 className="text-sm font-bold text-ink">
          {currentSection.label}
        </h3>
        <p className="mt-3 max-w-4xl text-sm leading-7 text-ink-soft whitespace-pre-wrap break-words">
          {sectionValue}
        </p>
      </div>

      {/* Navigation controls — stable footer position */}
      <nav
        className="mt-3 flex items-center justify-between gap-3"
        aria-label="요약 섹션 탐색"
      >
        <button
          type="button"
          onClick={() => setActiveIndex((i) => Math.max(0, i - 1))}
          disabled={isFirst}
          aria-label="이전 섹션"
          className={
            "rounded-full border px-4 py-2 text-xs font-bold transition " +
            (isFirst
              ? "cursor-not-allowed border-line-soft text-ink-faint"
              : "border-line text-ink hover:border-accent hover:text-accent")
          }
        >
          ← 이전
        </button>

        <span
          className="text-xs font-semibold text-ink-faint tabular-nums"
          aria-label={`${activeIndex + 1} / ${visibleSections.length} 섹션`}
        >
          {activeIndex + 1} / {visibleSections.length}
        </span>

        <button
          type="button"
          onClick={() =>
            setActiveIndex((i) => Math.min(visibleSections.length - 1, i + 1))
          }
          disabled={isLast}
          aria-label="다음 섹션"
          className={
            "rounded-full border px-4 py-2 text-xs font-bold transition " +
            (isLast
              ? "cursor-not-allowed border-line-soft text-ink-faint"
              : "border-line text-ink hover:border-accent hover:text-accent")
          }
        >
          다음 →
        </button>
      </nav>

      {/* Compact section indicators */}
      <div
        className="mt-3 flex flex-wrap gap-1 justify-center"
      >
        {visibleSections.map((section, idx) => (
          <button
            key={section.key}
            type="button"
            onClick={() => setActiveIndex(idx)}
            aria-label={`${section.label} 섹션으로 이동`}
            aria-current={idx === activeIndex ? "step" : undefined}
            className={
              "rounded-full px-2.5 py-1 text-[10px] font-bold transition " +
              (idx === activeIndex
                ? "bg-ink text-card"
                : "bg-line-soft text-ink-faint hover:bg-line hover:text-ink-soft")
            }
          >
            {section.label}
          </button>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Report body dispatcher
// ---------------------------------------------------------------------------

function ReportBody({
  reportState,
  fallbackSummary,
}: {
  reportState: IssueReportLoadState;
  fallbackSummary: string;
}) {
  if (reportState.status === "loading") {
    return <LoadingBody />;
  }

  if (reportState.status === "success") {
    return <SectionNavigator content={reportState.report.content} />;
  }

  if (reportState.status === "not_yet_generated") {
    return <NotYetGeneratedBody />;
  }

  return <ErrorBody fallbackSummary={fallbackSummary} />;
}

// ---------------------------------------------------------------------------
// Main report card
// ---------------------------------------------------------------------------

export function IssueReportCard({
  issueId,
  reportState,
  fallbackSummary,
  issueDataAsOf,
}: IssueReportCardProps) {
  const dataAsOf = reportDataAsOf(reportState, issueDataAsOf);

  // Reset state when the issue changes — using key on the child ensures
  // React remounts the SectionNavigator and resets activeIndex.
  const reportKey =
    reportState.status === "success"
      ? `${issueId}-${reportState.report.id}`
      : `${issueId}-${reportState.status}`;

  return (
    <section className="mt-10 rounded-lg border border-line bg-card p-5">
      {/* Header: title, report timing, and report-caution strip */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-ink">이슈 요약</h2>
          <p className="mt-1 text-[11px] font-semibold text-ink-faint">
            템플릿 기반 이슈 이해 요약
          </p>
        </div>
        <div className="flex flex-col items-start gap-1.5 sm:items-end">
          <span className="text-xs font-semibold text-ink-faint">
            데이터 기준 시각: {formatDataTimestamp(dataAsOf)}
          </span>
          {reportState.status === "success" ? (
            <span className="text-xs font-semibold text-ink-faint">
              요약 생성 시각:{" "}
              {formatDataTimestamp(reportState.report.generated_at)}
            </span>
          ) : null}
        </div>
      </div>

      {/* Compact report-caution strip — adjacent to the report header */}
      {reportState.status === "success" ? (
        <div className="mt-3 flex items-center gap-2 rounded-md border border-line-soft px-3 py-2">
          <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-accent text-[10px] font-bold text-accent">
            i
          </div>
          <p className="text-xs leading-5 text-ink-soft">
            이 요약은 저장된 시점의 데이터 흐름을 정리한 것이며, 현재 이슈의
            해석 주의 상태와 다를 수 있습니다. 마지막 섹션에서 전체 해석 주의
            내용을 확인하세요.
          </p>
        </div>
      ) : null}

      {/* Report body — key ensures remount on issue/report change */}
      <div key={reportKey}>
        <ReportBody
          reportState={reportState}
          fallbackSummary={fallbackSummary}
        />
      </div>

      {/* Existing short caution notice for non-success states */}
      {reportState.status !== "success" ? (
        <ShortCautionNotice
          context="summary"
          dataAsOf={dataAsOf}
          className="mt-4"
          surface="plain"
        />
      ) : null}
    </section>
  );
}
