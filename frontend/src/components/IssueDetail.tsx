import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";
import { Link, useSearchParams } from "react-router-dom";
import { SiteHeader } from "./AppShell";
import { CautionBadge } from "./CautionBadge";
import { GlobalFooter, ShortCautionNotice } from "./InformationNotice";
import { IssueReportCard } from "./IssueReportCard";
import { IssueTrendChart } from "./IssueTrendChart";
import { MetricTile } from "./MetricTile";
import { ScenarioConversation } from "./ScenarioConversation";
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
  IssueReportContextCandidate,
  IssueReportLoadState,
  StreamingBriefingState,
  V8IssueReportResponse,
  V8ReportSource,
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
  streamedBriefing: StreamingBriefingState | null;
};

type DetailTab = "overview" | "briefing" | "materials" | "scenario" | "guide";

const CHART_WINDOWS: ChartWindow[] = ["24h", "7d", "30d"];
const DETAIL_TABS: Array<{ id: DetailTab; label: string }> = [
  { id: "overview", label: "개요" },
  { id: "briefing", label: "AI 이슈 브리핑" },
  { id: "materials", label: "관련 자료" },
  { id: "scenario", label: "시나리오 대화" },
  { id: "guide", label: "해석 안내" },
];

const GUIDE_ITEMS = [
  {
    title: "반영 기대값의 의미",
    body: "공개 데이터에 반영된 관측값입니다. 실제 사건의 확률이나 전체 대중의 판단으로 단정할 수 없습니다.",
  },
  {
    title: "%와 %p의 차이",
    body: "%는 현재 반영 기대값이고, %p는 서로 다른 시점의 기대값 차이를 나타냅니다.",
  },
  {
    title: "활동 수준과 유동성",
    body: "참여 활동이 낮거나 유동성이 제한된 경우 같은 변화 폭도 더 크게 나타날 수 있습니다.",
  },
  {
    title: "변곡점 표시",
    body: "5%p 기준선을 넘은 관측 구간을 표시합니다. 함께 표시된 자료와의 관계를 뜻하지 않습니다.",
  },
  {
    title: "데이터 갱신 주기",
    body: "데이터는 실시간 수치가 아니며, 화면에 표시된 기준 시각을 중심으로 읽어야 합니다.",
  },
  {
    title: "해석 시 확인사항",
    body: "이 수치는 실제 결과를 보장하지 않습니다. 중요한 판단에는 별도 자료를 함께 확인해야 합니다.",
  },
] as const;

function isDetailTab(value: string | null): value is DetailTab {
  return DETAIL_TABS.some((tab) => tab.id === value);
}

function isFullReport(reportState: IssueReportLoadState): reportState is {
  status: "ready";
  response: V8IssueReportResponse;
} {
  return (
    reportState.status === "ready" && "report_version" in reportState.response
  );
}

function sourceLevelLabel(level: V8ReportSource["source_level"]): string {
  if (level === "A") return "A · 공식·1차 자료";
  if (level === "B") return "B · 주요 기관·보도 자료";
  return "C · 보조 공개 자료";
}

function DetailTabs({
  activeTab,
  onChange,
}: {
  activeTab: DetailTab;
  onChange: (tab: DetailTab) => void;
}) {
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([]);

  useEffect(() => {
    const activeIndex = DETAIL_TABS.findIndex((tab) => tab.id === activeTab);
    tabRefs.current[activeIndex]?.scrollIntoView({
      behavior: "auto",
      block: "nearest",
      inline: "nearest",
    });
  }, [activeTab]);

  const handleKeyDown = (event: KeyboardEvent<HTMLButtonElement>) => {
    const currentIndex = DETAIL_TABS.findIndex((tab) => tab.id === activeTab);
    let nextIndex = currentIndex;

    if (event.key === "ArrowRight") {
      nextIndex = (currentIndex + 1) % DETAIL_TABS.length;
    } else if (event.key === "ArrowLeft") {
      nextIndex = (currentIndex - 1 + DETAIL_TABS.length) % DETAIL_TABS.length;
    } else if (event.key === "Home") {
      nextIndex = 0;
    } else if (event.key === "End") {
      nextIndex = DETAIL_TABS.length - 1;
    } else {
      return;
    }

    event.preventDefault();
    const nextTab = DETAIL_TABS[nextIndex];
    onChange(nextTab.id);
    window.requestAnimationFrame(() => tabRefs.current[nextIndex]?.focus());
  };

  return (
    <nav
      className="mt-2 overflow-x-auto border-b border-line"
      aria-label="이슈 상세 메뉴"
    >
      <div
        role="tablist"
        aria-label="이슈 상세 보기"
        className="flex min-w-max gap-1"
      >
        {DETAIL_TABS.map((tab, index) => {
          const isActive = activeTab === tab.id;

          return (
            <button
              key={tab.id}
              ref={(node) => {
                tabRefs.current[index] = node;
              }}
              id={`detail-tab-${tab.id}`}
              type="button"
              role="tab"
              aria-selected={isActive}
              aria-controls={`detail-panel-${tab.id}`}
              tabIndex={isActive ? 0 : -1}
              onClick={() => onChange(tab.id)}
              onKeyDown={handleKeyDown}
              className={[
                "inline-flex min-h-11 shrink-0 items-center border-b-2 px-4 text-xs font-bold transition sm:px-6",
                isActive
                  ? "border-accent text-accent"
                  : "border-transparent text-ink-soft hover:border-line hover:text-ink",
              ].join(" ")}
            >
              {tab.label}
            </button>
          );
        })}
      </div>
    </nav>
  );
}

function IssueIdentity({ issue }: { issue: Issue }) {
  return (
    <header>
      <span className="text-[11px] font-bold text-ink-faint">
        {issue.topicLabel ?? formatCategoryLabel(issue.category)}
      </span>
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
    </header>
  );
}

function IssueContextBar({ issue }: { issue: Issue }) {
  return (
    <section className="mt-4 rounded-lg border border-line bg-card px-4 py-4 sm:px-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 id="issue-detail-title" className="text-base font-bold text-ink">
            {issue.title}
          </h1>
          <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs font-semibold text-ink-soft">
            <span>
              반영 기대값{" "}
              {formatExpectationValue(issue.currentExpectationValue)}
            </span>
            <span>
              7일 관측 변화 {formatPercentagePointChange(issue.change7d)}
            </span>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <CautionBadge level={issue.cautionLevel} />
          <span className="text-xs font-semibold text-ink-faint">
            데이터 기준 시각: {formatDataTimestamp(issue.dataAsOf)}
          </span>
        </div>
      </div>
    </section>
  );
}

function ChartSection({
  issue,
  historyStatus,
  chartWindow,
  onWindowChange,
  contextCandidates = [],
  compact = false,
}: {
  issue: Issue;
  historyStatus: "loading" | "ready" | "error";
  chartWindow: ChartWindow;
  onWindowChange: (window: ChartWindow) => void;
  contextCandidates?: IssueReportContextCandidate[];
  compact?: boolean;
}) {
  return (
    <section className={compact ? "" : "mt-8"}>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h2 className="text-lg font-bold text-ink">
          {compact
            ? "공개 데이터에 반영된 기대값 추이 · 7일"
            : "공개 데이터에 반영된 기대값 추이"}
        </h2>
        {!compact ? (
          <div className="flex gap-2" role="group" aria-label="차트 기간">
            {CHART_WINDOWS.map((windowOption) => (
              <button
                key={windowOption}
                type="button"
                onClick={() => onWindowChange(windowOption)}
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
        ) : null}
      </div>
      <p className="mt-2 text-xs leading-5 text-ink-faint">
        차트는 관측 흐름과 5%p 기준선 통과 여부를 보여줍니다. 함께 표시된
        자료와의 관계를 뜻하지 않습니다.
      </p>
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
          <IssueTrendChart
            issue={issue}
            windowKey={chartWindow}
            contextCandidates={contextCandidates}
          />
        )}
      </div>
    </section>
  );
}

function OverviewPanel({
  issue,
  historyStatus,
  chartWindow,
  onWindowChange,
}: {
  issue: Issue;
  historyStatus: "loading" | "ready" | "error";
  chartWindow: ChartWindow;
  onWindowChange: (window: ChartWindow) => void;
}) {
  const firstInflection = issue.inflectionPoints[0];

  return (
    <>
      <div className="mt-6 grid gap-5 lg:grid-cols-[1fr_1.05fr] lg:items-end">
        <IssueIdentity issue={issue} />
        <div className="grid grid-cols-2 gap-3">
          <MetricTile
            label="공개 데이터에 반영된 기대값"
            value={formatExpectationValue(issue.currentExpectationValue)}
            tone="accent"
          />
          <MetricTile
            label="7일 관측 변화"
            value={formatPercentagePointChange(issue.change7d)}
            tone="comparison"
          />
          <div className="col-span-2 rounded-lg border border-line bg-card px-4 py-3">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <CautionBadge level={issue.cautionLevel} />
              <span className="text-xs font-semibold text-ink-faint">
                데이터 기준 시각: {formatDataTimestamp(issue.dataAsOf)}
              </span>
            </div>
          </div>
        </div>
      </div>

      <ShortCautionNotice
        context="detail"
        cautionLevel={issue.cautionLevel}
        dataAsOf={issue.dataAsOf}
        className="mt-5"
      />

      <ChartSection
        issue={issue}
        historyStatus={historyStatus}
        chartWindow={chartWindow}
        onWindowChange={onWindowChange}
      />

      <section className="mt-7">
        <h2 className="text-lg font-bold text-ink">함께 확인할 요소</h2>
        <div className="mt-3 grid gap-3 md:grid-cols-3">
          <article className="rounded-lg border border-line bg-card px-4 py-4">
            <h3 className="text-sm font-bold text-ink">판정 기준</h3>
            <p className="mt-2 text-sm leading-6 text-ink-soft">
              {issue.resolutionCondition ??
                "원문 시장 질문과 판정 조건을 함께 확인해야 합니다."}
            </p>
          </article>
          <article className="rounded-lg border border-line bg-card px-4 py-4">
            <h3 className="text-sm font-bold text-ink">주요 관측 구간</h3>
            <p className="mt-2 text-sm leading-6 text-ink-soft">
              {firstInflection
                ? `${formatShortDate(firstInflection.timestamp)}에 ${formatPercentagePointChange(firstInflection.change)}의 기준선 통과가 관측되었습니다.`
                : "선택한 이력에서 5%p 기준선을 넘는 구간이 확인되지 않았습니다."}
            </p>
          </article>
          <article className="rounded-lg border border-line bg-card px-4 py-4">
            <h3 className="text-sm font-bold text-ink">관련 자료</h3>
            <p className="mt-2 text-sm leading-6 text-ink-soft">
              {issue.relatedEventCandidates?.length
                ? `${issue.relatedEventCandidates.length}건의 후보 자료를 시간 순서로 확인할 수 있습니다.`
                : "현재 이슈에 등록된 후보 자료가 없습니다."}
            </p>
          </article>
        </div>
      </section>
    </>
  );
}

function PublicSourceCard({ source }: { source: V8ReportSource }) {
  return (
    <article className="rounded-lg border border-line bg-card px-4 py-4">
      <div className="flex flex-wrap items-center gap-2 text-[11px] font-semibold text-ink-faint">
        <span className="rounded-full border border-line px-2 py-1">
          출처 수준 {sourceLevelLabel(source.source_level)}
        </span>
        <span className="break-all">{source.domain}</span>
        <span aria-hidden="true">·</span>
        <span>확인 시각 {formatDataTimestamp(source.retrieved_at)}</span>
      </div>
      <a
        href={source.url}
        target="_blank"
        rel="noopener noreferrer"
        className="mt-2 inline-flex min-h-11 max-w-full items-center break-words text-sm font-bold leading-5 text-accent hover:underline"
      >
        {source.title}
        <span className="ml-1" aria-hidden="true">
          ↗
        </span>
        <span className="sr-only">새 창에서 원문 열기</span>
      </a>
      <div className="mt-3">
        <h3 className="text-xs font-bold text-ink">이 자료가 지원하는 문장</h3>
        <ul className="mt-2 list-disc space-y-1.5 pl-5 text-sm leading-6 text-ink-soft">
          {source.supported_claims.map((claim) => (
            <li key={claim.ref}>{claim.text}</li>
          ))}
        </ul>
      </div>
    </article>
  );
}

function MaterialsPanel({
  issue,
  historyStatus,
  reportState,
}: {
  issue: Issue;
  historyStatus: "loading" | "ready" | "error";
  reportState: IssueReportLoadState;
}) {
  const candidates = useMemo<IssueReportContextCandidate[]>(
    () =>
      (issue.relatedEventCandidates ?? []).map((event, index) => ({
        id: `related-${index + 1}`,
        title: event.title,
        event_at: event.date,
        summary: event.note,
        sources: [],
      })),
    [issue.relatedEventCandidates],
  );
  const sources = isFullReport(reportState) ? reportState.response.sources : [];
  const sourceStatus =
    reportState.status === "loading"
      ? "loading"
      : reportState.status === "error"
        ? "error"
        : "ready";

  return (
    <>
      <section className="mt-6">
        <h2 className="text-lg font-bold text-ink">관련 공개자료 타임라인</h2>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-ink-soft">
          관측 변화와 비슷한 시기에 확인된 후보 자료를 시간 순서로 정리했습니다.
          수치 변화와의 관계를 의미하지 않습니다.
        </p>

        <div className="mt-4 grid gap-5 lg:grid-cols-[1.15fr_0.85fr]">
          <div>
            {candidates.length ? (
              <ol className="space-y-3">
                {candidates.map((candidate, index) => (
                  <li key={candidate.id}>
                    <article
                      id={`context-candidate-${candidate.id}`}
                      className="rounded-lg border border-line bg-card px-4 py-4"
                    >
                      <div className="flex items-start gap-3">
                        <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent text-xs font-extrabold text-card shadow-sm">
                          {index + 1}
                        </span>
                        <div>
                          <p className="text-xs font-semibold text-ink-faint">
                            {formatShortDate(candidate.event_at)} · 후보 자료
                          </p>
                          <h3 className="mt-1 text-sm font-bold text-ink">
                            {candidate.title}
                          </h3>
                          <p className="mt-1 text-sm leading-6 text-ink-soft">
                            {candidate.summary}
                          </p>
                        </div>
                      </div>
                    </article>
                  </li>
                ))}
              </ol>
            ) : (
              <p className="rounded-lg border border-dashed border-line px-4 py-5 text-sm leading-6 text-ink-soft">
                현재 이슈에는 등록된 후보 자료가 없습니다. 자료가 없다는 사실이
                관측 변화의 배경이 없음을 의미하지는 않습니다.
              </p>
            )}
          </div>
          <ChartSection
            issue={issue}
            historyStatus={historyStatus}
            chartWindow="7d"
            onWindowChange={() => undefined}
            contextCandidates={candidates}
            compact
          />
        </div>
      </section>

      <section className="mt-8">
        <h2 className="text-lg font-bold text-ink">
          브리핑에서 확인한 공개 자료
        </h2>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-ink-soft">
          아래 자료는 저장된 지원 문장과 출처 수준을 함께 표시합니다. 자료의
          존재만으로 관측 변화와의 관계가 성립하지 않습니다.
        </p>
        {sourceStatus === "loading" ? (
          <p className="mt-4 rounded-lg border border-line bg-card px-4 py-4 text-sm leading-6 text-ink-soft">
            공개 자료를 불러오는 중입니다.
          </p>
        ) : sourceStatus === "error" ? (
          <p className="mt-4 rounded-lg border border-line bg-card px-4 py-4 text-sm leading-6 text-ink-soft">
            공개 자료 상태를 불러오지 못했습니다. 이슈 정보와 차트는 계속 확인할
            수 있습니다.
          </p>
        ) : sources.length ? (
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            {sources.map((source) => (
              <PublicSourceCard key={source.id} source={source} />
            ))}
          </div>
        ) : (
          <p className="mt-4 rounded-lg border border-dashed border-line px-4 py-4 text-sm leading-6 text-ink-soft">
            현재 표시할 수 있는 검증된 공개 자료가 없습니다. 확인 기준을
            통과하지 않은 자료는 표시하지 않습니다.
          </p>
        )}
      </section>

      <ShortCautionNotice
        context="detail"
        cautionLevel={issue.cautionLevel}
        dataAsOf={issue.dataAsOf}
        className="mt-6"
      />
    </>
  );
}

function GuidePanel({ issue }: { issue: Issue }) {
  return (
    <>
      <section className="mt-6">
        <span className="text-xs font-bold text-ink-faint">
          데이터 해석 안내
        </span>
        <h2 className="mt-2 text-xl font-bold text-ink">
          이 화면의 수치를 읽는 기준
        </h2>
        <div className="mt-4 grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {GUIDE_ITEMS.map((item) => (
            <article
              key={item.title}
              className="rounded-lg border border-line bg-card px-4 py-4"
            >
              <h3 className="text-sm font-bold text-ink">{item.title}</h3>
              <p className="mt-2 text-sm leading-6 text-ink-soft">
                {item.body}
              </p>
            </article>
          ))}
        </div>
      </section>

      <ShortCautionNotice
        context="detail"
        cautionLevel={issue.cautionLevel}
        dataAsOf={issue.dataAsOf}
        className="mt-6"
      />

      <Link
        to="/methodology"
        className="mt-4 inline-flex min-h-11 items-center text-sm font-bold text-accent"
      >
        전체 해석 기준 자세히 보기 →
      </Link>
    </>
  );
}

/** Five-part issue detail view with an isolated, conditional scenario conversation. */
export function IssueDetail({
  issue,
  dataStatus = "ready",
  reportState,
  historyStatus,
  backTo,
  onGenerateReport,
  generationPending,
  generationActionError,
  streamedBriefing,
}: IssueDetailProps) {
  const [searchParams, setSearchParams] = useSearchParams();
  const requestedTab = searchParams.get("tab");
  const activeTab: DetailTab = isDetailTab(requestedTab)
    ? requestedTab
    : "overview";
  const [chartWindow, setChartWindow] = useState<ChartWindow>("7d");

  useEffect(() => {
    if (requestedTab === null || isDetailTab(requestedTab)) {
      return;
    }
    const nextParams = new URLSearchParams(searchParams);
    nextParams.delete("tab");
    setSearchParams(nextParams, { replace: true });
  }, [requestedTab, searchParams, setSearchParams]);

  useEffect(() => {
    const frame = window.requestAnimationFrame(focusRouteHeading);
    return () => window.cancelAnimationFrame(frame);
  }, [issue.id]);

  const changeTab = (tab: DetailTab) => {
    const nextParams = new URLSearchParams(searchParams);
    if (tab === "overview") {
      nextParams.delete("tab");
    } else {
      nextParams.set("tab", tab);
    }
    setSearchParams(nextParams);
  };

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
            {issue.title}
          </span>
        </nav>

        <Link
          to={backTo}
          className="inline-flex min-h-11 items-center text-sm font-semibold text-ink-soft transition hover:text-accent"
        >
          ← 이전 화면으로 돌아가기
        </Link>

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

        <DetailTabs activeTab={activeTab} onChange={changeTab} />

        {activeTab !== "overview" ? <IssueContextBar issue={issue} /> : null}

        <div
          id={`detail-panel-${activeTab}`}
          role="tabpanel"
          aria-labelledby={`detail-tab-${activeTab}`}
          tabIndex={0}
          className="outline-none"
        >
          {activeTab === "overview" ? (
            <OverviewPanel
              issue={issue}
              historyStatus={historyStatus}
              chartWindow={chartWindow}
              onWindowChange={setChartWindow}
            />
          ) : null}

          {activeTab === "briefing" ? (
            <IssueReportCard
              issueId={issue.id}
              reportState={reportState}
              issueDataAsOf={issue.dataAsOf}
              onGenerate={onGenerateReport}
              generationPending={generationPending}
              generationActionError={generationActionError}
              streamedBriefing={streamedBriefing}
              className="mt-6"
            />
          ) : null}

          {activeTab === "materials" ? (
            <MaterialsPanel
              issue={issue}
              historyStatus={historyStatus}
              reportState={reportState}
            />
          ) : null}

          {activeTab === "scenario" ? (
            <ScenarioConversation issue={issue} />
          ) : null}

          {activeTab === "guide" ? <GuidePanel issue={issue} /> : null}
        </div>
      </main>

      <GlobalFooter className="mt-10" />
    </div>
  );
}
