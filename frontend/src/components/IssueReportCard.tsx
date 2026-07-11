import { useState } from "react";
import { ShortCautionNotice } from "./InformationNotice";
import type {
  GeneralScenario,
  IssueReportContextCandidate,
  IssueReportLoadState,
  IssueReportResolutionReference,
  IssueReportSuccessResponse,
  MaterialToCheck,
  ReportBasis,
} from "../types/issue";
import { formatDataTimestamp, formatShortDate } from "../utils/format";

type IssueReportCardProps = {
  issueId: string;
  reportState: IssueReportLoadState;
  issueDataAsOf: string;
};

const GENERAL_SCENARIO_NOTICE =
  "현재 상황을 입증하는 검증 자료가 아니라 일반적인 시나리오 설명입니다.";

function reportDataAsOf(
  reportState: IssueReportLoadState,
  fallbackDataAsOf: string,
) {
  return reportState.status === "success"
    ? reportState.report.data_as_of
    : fallbackDataAsOf;
}

function LoadingBody() {
  return (
    <div
      className="mt-4 rounded-lg border border-line-soft px-4 py-5"
      aria-label="브리핑 불러오는 중"
    >
      <div className="h-3 w-40 animate-pulse rounded-full bg-line" />
      <div className="mt-4 h-3 w-full max-w-3xl animate-pulse rounded-full bg-line-soft" />
      <div className="mt-2 h-3 w-2/3 animate-pulse rounded-full bg-line-soft" />
    </div>
  );
}

function NotYetGeneratedBody() {
  return (
    <div className="mt-4 rounded-lg border border-dashed border-line px-4 py-5">
      <h3 className="text-sm font-bold text-ink">
        새 브리핑 계약에 맞는 저장 결과가 없습니다
      </h3>
      <p className="mt-2 max-w-3xl text-sm leading-6 text-ink-soft">
        이전 형식의 결과는 대신 표시하지 않습니다. 이슈 정보와 차트는 계속
        확인할 수 있습니다.
      </p>
    </div>
  );
}

function ErrorBody() {
  return (
    <div className="mt-4 rounded-lg border border-line px-4 py-5">
      <h3 className="text-sm font-bold text-ink">
        저장된 브리핑을 불러오지 못했습니다
      </h3>
      <p className="mt-2 max-w-3xl text-sm leading-6 text-ink-soft">
        계약에 맞지 않는 이전 요약이나 임시 문장을 대신 표시하지 않습니다.
      </p>
    </div>
  );
}

function sourceTypeLabel(sourceType: "official" | "independent_secondary") {
  return sourceType === "official" ? "공식 출처" : "독립 보조 출처";
}

function sourceActionLabel(sourceType: "official" | "independent_secondary") {
  return sourceType === "official" ? "공식 자료 확인" : "기사 원문 확인";
}

function ContextCandidateCard({
  candidate,
}: {
  candidate: IssueReportContextCandidate;
}) {
  return (
    <article
      id={`context-candidate-${candidate.id}`}
      data-candidate-id={candidate.id}
      className="scroll-mt-24 rounded-lg border border-line-soft bg-card px-4 py-4"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-xs font-semibold text-ink-faint">
          {formatShortDate(candidate.event_at)}
        </span>
        <a
          href={`#candidate-marker-${candidate.id}`}
          className="inline-flex min-h-11 items-center text-xs font-bold text-accent hover:underline"
        >
          차트 위치 보기
        </a>
      </div>
      <h4 className="mt-1 break-words text-sm font-bold text-ink">
        {candidate.title}
      </h4>
      <p className="mt-2 break-words text-sm leading-6 text-ink-soft">
        {candidate.summary}
      </p>
      <ul className="mt-3 space-y-2" aria-label={`${candidate.title} 출처`}>
        {candidate.sources.map((source) => (
          <li
            key={`${source.url}-${source.title}`}
            className="rounded-md bg-paper px-3 py-3"
          >
            <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-[11px] font-semibold text-ink-faint">
              <span>{sourceTypeLabel(source.source_type)}</span>
              <span aria-hidden="true">·</span>
              <span className="break-all">{source.domain}</span>
              <span aria-hidden="true">·</span>
              <span>
                {source.published_at
                  ? formatShortDate(source.published_at)
                  : "발행 시각 미제공"}
              </span>
            </div>
            <a
              href={source.url}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-1 inline-flex min-h-11 max-w-full items-center break-words text-sm font-bold leading-5 text-accent hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2"
            >
              {sourceActionLabel(source.source_type)} · {source.title}
              <span className="ml-1" aria-hidden="true">
                ↗
              </span>
              <span className="sr-only">새 창에서 열기</span>
            </a>
          </li>
        ))}
      </ul>
    </article>
  );
}

function EvidenceSection({
  label,
  children,
  tone = "plain",
}: {
  label: string;
  children: React.ReactNode;
  tone?: "plain" | "soft";
}) {
  return (
    <section
      className={
        tone === "soft"
          ? "rounded-lg bg-paper px-4 py-4"
          : "border-t border-line-soft pt-5"
      }
    >
      <h3 className="text-xs font-bold uppercase tracking-[0.08em] text-ink-faint">
        {label}
      </h3>
      <div className="mt-2 break-words text-sm leading-7 text-ink-soft">
        {children}
      </div>
    </section>
  );
}

function BasisLabel({ basis }: { basis: ReportBasis }) {
  const labels: Record<ReportBasis, string> = {
    market_definition: "시장 정의",
    observed_data: "관측 데이터",
    verified_context: "검증된 공개 자료",
    general_scenario: "일반 시나리오",
    data_limitation: "데이터 한계",
  };
  return (
    <span className="mt-1 inline-flex rounded-full border border-line px-2 py-0.5 text-[10px] font-semibold text-ink-faint">
      근거 범위 · {labels[basis]}
    </span>
  );
}

function GeneralNotice() {
  return (
    <p className="rounded-md border border-dashed border-line bg-paper px-3 py-2 text-xs font-semibold leading-5 text-ink-soft">
      {GENERAL_SCENARIO_NOTICE}
    </p>
  );
}

function ScenarioList({ scenarios }: { scenarios: GeneralScenario[] }) {
  return (
    <ol className="space-y-3">
      {scenarios.map((scenario, index) => (
        <li
          key={`${scenario.title}-${scenario.text}`}
          className="rounded-md bg-paper px-3 py-3"
        >
          <h4 className="font-bold text-ink">
            {index + 1}. {scenario.title}
          </h4>
          <BasisLabel basis={scenario.basis} />
          <p className="mt-1">{scenario.text}</p>
        </li>
      ))}
    </ol>
  );
}

function MaterialsList({ items }: { items: MaterialToCheck[] }) {
  return (
    <ul className="space-y-3">
      {items.map((item) => (
        <li
          key={`${item.scenario_index}-${item.title}-${item.text}`}
          className="rounded-md bg-paper px-3 py-3"
        >
          <span className="text-[10px] font-bold text-ink-faint">
            시나리오 {item.scenario_index} 확인 항목
          </span>
          <h4 className="mt-1 font-bold text-ink">{item.title}</h4>
          <BasisLabel basis={item.basis} />
          <p className="mt-1">{item.text}</p>
        </li>
      ))}
    </ul>
  );
}

function VerifiedSources({
  report,
  background,
}: {
  report: IssueReportSuccessResponse;
  background: string;
}) {
  return (
    <EvidenceSection label="검증된 공개 배경">
      <p>{background}</p>
      <BasisLabel basis="verified_context" />
      <div className="mt-4 space-y-3">
        {report.context_candidates.map((candidate) => (
          <ContextCandidateCard key={candidate.id} candidate={candidate} />
        ))}
      </div>
    </EvidenceSection>
  );
}

function ResolutionReferenceDisclosure({
  reference,
}: {
  reference: IssueReportResolutionReference;
}) {
  const [expanded, setExpanded] = useState(false);
  const panelId = "report-resolution-reference";
  return (
    <section className="border-t border-line-soft pt-5">
      <button
        type="button"
        aria-expanded={expanded}
        aria-controls={panelId}
        onClick={() => setExpanded((value) => !value)}
        className="inline-flex min-h-11 w-full items-center justify-between gap-3 rounded-md border border-line px-3 text-left text-sm font-bold text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2"
      >
        <span>판정 기준 보기</span>
        <span aria-hidden="true">{expanded ? "−" : "+"}</span>
      </button>
      <div
        id={panelId}
        hidden={!expanded}
        className="mt-3 rounded-md bg-paper px-4 py-4 text-sm leading-7 text-ink-soft"
      >
        {reference.status === "available" ? (
          <>
            <p>{reference.condition_text}</p>
            {reference.deadline ? (
              <p className="mt-2 text-xs font-semibold">
                기준 시각: {formatDataTimestamp(reference.deadline)}
              </p>
            ) : null}
            {reference.exclusions.length ? (
              <ul className="mt-2 list-disc space-y-1 pl-5">
                {reference.exclusions.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            ) : null}
            {reference.source_url ? (
              <a
                href={reference.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-2 inline-flex min-h-11 items-center font-bold text-accent hover:underline"
              >
                판정 자료 원문 확인
                <span className="sr-only">새 창에서 열기</span>
              </a>
            ) : null}
          </>
        ) : (
          <p>저장된 상세 판정 기준이 없습니다.</p>
        )}
      </div>
    </section>
  );
}

function AiIssueBriefing({ report }: { report: IssueReportSuccessResponse }) {
  const briefing = report.briefing;
  const changeIntro = report.observed_change.significant
    ? "기존 관찰 기준을 충족한 변화가 기록되었습니다. 수치와 기준 시각은 위 지표 영역에서 한 번만 표시합니다."
    : "기존 관찰 기준을 충족한 변화가 없어 안정 상태로 분류했습니다. 수치와 기준 시각은 위 지표 영역에서 한 번만 표시합니다.";

  return (
    <div
      className="mt-5 space-y-5"
      data-episode-at={report.episode_at}
      data-report-mode={report.report_mode}
    >
      {briefing.mode.startsWith("change_") ? (
        <EvidenceSection label="관찰된 변화" tone="soft">
          <p>{changeIntro}</p>
          <BasisLabel basis="observed_data" />
        </EvidenceSection>
      ) : null}

      {briefing.mode === "stable_with_evidence" ||
      briefing.mode === "stable_without_evidence" ? (
        <EvidenceSection
          label={
            briefing.mode === "stable_without_evidence"
              ? "통상적인 이슈 설명"
              : "이슈 설명"
          }
          tone="soft"
        >
          <p>{briefing.issue_explanation.text}</p>
          <BasisLabel basis={briefing.issue_explanation.basis} />
          {briefing.issue_explanation.basis === "general_scenario" ? (
            <div className="mt-3">
              <GeneralNotice />
            </div>
          ) : null}
        </EvidenceSection>
      ) : null}

      {briefing.mode === "change_with_evidence" ||
      briefing.mode === "stable_with_evidence" ? (
        <VerifiedSources
          report={report}
          background={briefing.verified_background.text}
        />
      ) : null}

      {briefing.mode === "change_without_evidence" ? (
        <div className="rounded-md border border-dashed border-line px-3 py-3 text-sm leading-6 text-ink-soft">
          이번 검토 구간에는 공개 기준을 통과한 배경 자료가 없습니다.
        </div>
      ) : null}

      {briefing.mode === "change_with_evidence" ? (
        <EvidenceSection label="조건부 해석">
          <ol className="space-y-3">
            {briefing.conditional_interpretations.map((item, index) => (
              <li
                key={`${item.title}-${item.text}`}
                className="rounded-md bg-paper px-3 py-3"
              >
                <h4 className="font-bold text-ink">
                  {index + 1}. {item.title}
                </h4>
                <BasisLabel basis={item.basis} />
                <p className="mt-1">{item.text}</p>
              </li>
            ))}
          </ol>
        </EvidenceSection>
      ) : (
        <>
          {briefing.mode !== "stable_without_evidence" ? (
            <GeneralNotice />
          ) : null}
          <EvidenceSection label="조건부 시나리오">
            <ScenarioList scenarios={briefing.conditional_scenarios} />
          </EvidenceSection>
        </>
      )}

      {briefing.mode === "change_without_evidence" ||
      briefing.mode === "stable_without_evidence" ? (
        <EvidenceSection label="시나리오별 확인 항목">
          <MaterialsList items={briefing.materials_to_check} />
        </EvidenceSection>
      ) : null}

      <ResolutionReferenceDisclosure reference={report.resolution_reference} />
      <EvidenceSection label="관계 해석 범위" tone="soft">
        <p>{report.relationship_boundary}</p>
      </EvidenceSection>
      <EvidenceSection label="데이터 한계">
        <p>{report.data_limitations}</p>
      </EvidenceSection>
      <div className="rounded-lg border border-line bg-accent-soft px-4 py-4">
        <h3 className="text-xs font-bold text-ink">해석상 주의사항</h3>
        <p className="mt-2 break-words text-sm leading-7 text-ink-soft">
          {report.caution_note}
        </p>
      </div>
    </div>
  );
}

function ReportBody({ reportState }: { reportState: IssueReportLoadState }) {
  if (reportState.status === "loading") return <LoadingBody />;
  if (reportState.status === "success")
    return <AiIssueBriefing report={reportState.report} />;
  if (reportState.status === "not_yet_generated")
    return <NotYetGeneratedBody />;
  return <ErrorBody />;
}

export function IssueReportCard({
  issueId,
  reportState,
  issueDataAsOf,
}: IssueReportCardProps) {
  const dataAsOf = reportDataAsOf(reportState, issueDataAsOf);
  const reportKey =
    reportState.status === "success"
      ? `${issueId}-${reportState.report.id}`
      : `${issueId}-${reportState.status}`;
  return (
    <section className="mt-10 rounded-lg border border-line bg-card p-4 sm:p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-ink">AI 이슈 브리핑</h2>
          <p className="mt-1 text-[11px] font-semibold text-ink-faint">
            근거 수준에 맞는 섹션만 표시합니다
          </p>
        </div>
        <div className="flex flex-col items-start gap-1.5 sm:items-end">
          <span className="text-xs font-semibold text-ink-faint">
            데이터 기준 시각: {formatDataTimestamp(dataAsOf)}
          </span>
          {reportState.status === "success" ? (
            <>
              <span className="text-xs font-semibold text-ink-faint">
                검토 구간: {formatDataTimestamp(reportState.report.episode_at)}
              </span>
              <span className="text-xs font-semibold text-ink-faint">
                생성 시각:{" "}
                {formatDataTimestamp(reportState.report.generated_at)}
              </span>
            </>
          ) : null}
        </div>
      </div>
      <div className="mt-3 flex items-start gap-2 rounded-md border border-line-soft px-3 py-2">
        <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-accent text-[10px] font-bold text-accent">
          i
        </div>
        <p className="text-xs leading-5 text-ink-soft">
          검증된 공개 자료와 일반 시나리오는 서로 다른 근거 유형으로 표시합니다.
        </p>
      </div>
      <div key={reportKey}>
        <ReportBody reportState={reportState} />
      </div>
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
