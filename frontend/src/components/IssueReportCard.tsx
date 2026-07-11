import { ShortCautionNotice } from "./InformationNotice";
import type {
  IssueReportContextCandidate,
  IssueReportLoadState,
  IssueReportSuccessResponse,
  ReportBasis,
} from "../types/issue";
import { formatDataTimestamp, formatShortDate } from "../utils/format";

type IssueReportCardProps = {
  issueId: string;
  reportState: IssueReportLoadState;
  fallbackSummary: string;
  issueDataAsOf: string;
};

function reportDataAsOf(
  reportState: IssueReportLoadState,
  fallbackDataAsOf: string,
): string {
  return reportState.status === "success"
    ? reportState.report.data_as_of
    : fallbackDataAsOf;
}

function LoadingBody() {
  return (
    <div className="mt-4 rounded-lg border border-line-soft px-4 py-5">
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
        검증된 변화 에피소드가 아직 없습니다
      </h3>
      <p className="mt-2 max-w-3xl text-sm leading-6 text-ink-soft">
        이슈 정보와 차트는 계속 확인할 수 있습니다. 저장된 수치와 검증된 공개
        정보가 연결되면 이 영역에 함께 표시합니다.
      </p>
    </div>
  );
}

function ErrorBody({ fallbackSummary }: { fallbackSummary: string }) {
  return (
    <div className="mt-4 rounded-lg border border-line px-4 py-5">
      <h3 className="text-sm font-bold text-ink">
        저장된 변화 에피소드를 불러오지 못했습니다
      </h3>
      <p className="mt-2 max-w-3xl text-sm leading-6 text-ink-soft">
        아래 문장은 현재 화면 데이터로 만든 임시 요약입니다. 검증된 공개 정보가
        연결된 저장 결과가 아니므로 데이터 기준 시각과 해석 주의를 함께 확인해야
        합니다.
      </p>
      <p className="mt-4 max-w-4xl rounded-lg bg-accent-soft px-4 py-3 text-sm leading-7 text-ink break-words">
        {fallbackSummary}
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
              className="mt-1 inline-flex min-h-11 max-w-full items-center break-words text-sm font-bold leading-5 text-accent hover:underline"
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

function BriefingList({
  items,
}: {
  items: Array<{ title: string; explanation: string; basis: ReportBasis }>;
}) {
  return (
    <ul className="space-y-3">
      {items.map((item) => (
        <li key={`${item.title}-${item.explanation}`} className="rounded-md bg-paper px-3 py-3">
          <h4 className="font-bold text-ink">{item.title}</h4>
          <BasisLabel basis={item.basis} />
          <p className="mt-1">{item.explanation}</p>
        </li>
      ))}
    </ul>
  );
}

function BasisLabel({ basis }: { basis: ReportBasis }) {
  const labels: Record<ReportBasis, string> = {
    market_definition: "시장 판정 정의",
    observed_data: "관측 데이터",
    verified_context: "검증된 공개 자료",
    data_limitation: "데이터 한계",
  };
  return (
    <span className="mt-1 inline-flex rounded-full border border-line px-2 py-0.5 text-[10px] font-semibold text-ink-faint">
      근거 범위 · {labels[basis]}
    </span>
  );
}

function AiIssueBriefing({ report }: { report: IssueReportSuccessResponse }) {
  const { content, context_candidates: candidates } = report;
  return (
    <div className="mt-5 space-y-5" data-episode-at={report.episode_at}>
      <EvidenceSection label="핵심 요약" tone="soft">
        <p>{content.executive_summary}</p>
      </EvidenceSection>

      <EvidenceSection label="현재 데이터 해석">
        <p className="font-semibold text-ink">{content.current_data_interpretation}</p>
      </EvidenceSection>

      <EvidenceSection label="가능한 조건부 시나리오">
        <ol className="space-y-3">
          {content.conditional_scenarios.map((scenario, index) => (
            <li key={`${scenario.title}-${scenario.narrative}`} className="rounded-md bg-paper px-3 py-3">
              <h4 className="font-bold text-ink">{index + 1}. {scenario.title}</h4>
              <BasisLabel basis={scenario.basis} />
              <p className="mt-1">{scenario.narrative}</p>
            </li>
          ))}
        </ol>
      </EvidenceSection>

      <div className="grid gap-5 md:grid-cols-2">
        <EvidenceSection label="기대값과 함께 확인할 주요 요인">
          <BriefingList items={content.factors_to_check} />
        </EvidenceSection>
        <EvidenceSection label="앞으로 확인할 자료와 변화">
          <BriefingList items={content.signals_to_watch} />
        </EvidenceSection>
      </div>

      {candidates.length > 0 && content.evidence_synthesis !== null ? (
        <EvidenceSection label="검증된 기사·공식자료">
          <p>{content.evidence_synthesis}</p>
          <div className="mt-4 space-y-3">
            {candidates.map((candidate) => (
              <ContextCandidateCard key={candidate.id} candidate={candidate} />
            ))}
          </div>
        </EvidenceSection>
      ) : (
        <EvidenceSection label="검증된 기사·공식자료">
          <div className="rounded-md border border-dashed border-line px-3 py-3">
            이번 검토 구간에는 공개 기준을 통과한 자료가 없습니다. 관찰된 수치
            움직임의 배경은 확인되지 않았습니다.
          </div>
        </EvidenceSection>
      )}

      <EvidenceSection label="관계 해석 범위" tone="soft">
        <p>{content.relationship_boundary}</p>
      </EvidenceSection>

      <EvidenceSection label="데이터 한계">
        <p>{content.data_limitations}</p>
      </EvidenceSection>

      <div className="rounded-lg border border-line bg-accent-soft px-4 py-4">
        <h3 className="text-xs font-bold text-ink">해석상 주의사항</h3>
        <p className="mt-2 break-words text-sm leading-7 text-ink-soft">
          {content.caution_note}
        </p>
      </div>
    </div>
  );
}

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
    return <AiIssueBriefing report={reportState.report} />;
  }
  if (reportState.status === "not_yet_generated") {
    return <NotYetGeneratedBody />;
  }
  return <ErrorBody fallbackSummary={fallbackSummary} />;
}

export function IssueReportCard({
  issueId,
  reportState,
  fallbackSummary,
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
            저장 근거 안에서 현재 데이터, 조건부 시나리오, 확인 자료를 정리합니다
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
          공개 데이터의 관찰 흐름과 검증된 공개 정보를 함께 보여주지만, 두 항목
          사이의 관계나 현실의 결과를 입증하지 않습니다.
        </p>
      </div>

      <div key={reportKey}>
        <ReportBody
          reportState={reportState}
          fallbackSummary={fallbackSummary}
        />
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
