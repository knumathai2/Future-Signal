import { ShortCautionNotice } from "./InformationNotice";
import { LoadingSpinner } from "./LoadingSpinner";
import type {
  IssueReportLoadState,
  IssueReportResponse,
  V8IssueReportResponse,
  V8ReportSource,
  StreamingBriefingState,
} from "../types/issue";
import { formatDataTimestamp } from "../utils/format";

type IssueReportCardProps = {
  issueId: string;
  reportState: IssueReportLoadState;
  issueDataAsOf: string;
  onGenerate: (refreshContext: boolean) => Promise<void>;
  generationPending: boolean;
  generationActionError: boolean;
  streamedBriefing: StreamingBriefingState | null;
  className?: string;
};

function isFullReport(
  response: IssueReportResponse | undefined,
): response is V8IssueReportResponse {
  return response !== undefined && "report_version" in response;
}

function sourceLevelLabel(level: V8ReportSource["source_level"]) {
  if (level === "A") return "A · 공식·1차 자료";
  if (level === "B") return "B · 주요 기관·보도 자료";
  return "C · 보조 공개 자료";
}

function statusLabel(response: IssueReportResponse | undefined) {
  if (!response) return "불러오는 중";
  if (response.status === "idle") return "생성 전";
  if (response.status === "generating") return "생성 중";
  if (response.status === "fresh") return "최신 근거 반영";
  if (response.status === "stale") return "새 데이터 있음";
  if (response.status === "failed_with_last_good") return "이전 브리핑 유지";
  return "생성 미완료";
}

function ActionButton({
  label,
  pending,
  onGenerate,
}: {
  label: string;
  pending: boolean;
  onGenerate: () => void;
}) {
  return (
    <button
      type="button"
      disabled={pending}
      aria-busy={pending}
      onClick={onGenerate}
      className="inline-flex min-h-11 items-center justify-center gap-2 rounded-full border border-accent bg-accent px-5 text-sm font-bold text-card transition hover:brightness-95 disabled:cursor-wait disabled:opacity-60"
    >
      {pending ? (
        <>
          <LoadingSpinner />
          <span>요청을 기록하는 중</span>
        </>
      ) : (
        label
      )}
    </button>
  );
}

function SourceCard({ source }: { source: V8ReportSource }) {
  return (
    <article className="rounded-lg border border-line-soft bg-paper px-4 py-4">
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
        <h4 className="text-xs font-bold text-ink">이 자료가 지원하는 문장</h4>
        <ul className="mt-2 list-disc space-y-1.5 pl-5 text-sm leading-6 text-ink-soft">
          {source.supported_claims.map((claim) => (
            <li key={claim.ref}>{claim.text}</li>
          ))}
        </ul>
      </div>
    </article>
  );
}

function BriefingContent({ report }: { report: V8IssueReportResponse }) {
  const hasAuthoredLimitations = report.sections.some(
    (section) => section.type === "limitations",
  );
  const citedSourceIds = new Set(
    report.sections.flatMap((section) =>
      section.evidence_refs.filter((ref) => ref.startsWith("source:")),
    ),
  );
  const citedSources = report.sources.filter((source) =>
    citedSourceIds.has(source.id),
  );
  return (
    <div className="mt-5 space-y-5">
      <div className="rounded-lg border-l-4 border-accent bg-accent-soft px-4 py-4 sm:px-5">
        <h3 className="text-xl font-bold leading-8 text-ink">
          {report.headline}
        </h3>
        <p className="mt-2 text-sm leading-7 text-ink-soft">{report.summary}</p>
      </div>

      {report.sections.map((section) => (
        <section
          key={`${section.type}-${section.title}`}
          className="border-t border-line-soft pt-5"
        >
          <h3 className="text-base font-bold text-ink">{section.title}</h3>
          {section.format === "paragraph" ? (
            <p className="mt-2 break-words text-sm leading-7 text-ink-soft">
              {section.content}
            </p>
          ) : (
            <ul className="mt-2 list-disc space-y-2 pl-5 text-sm leading-7 text-ink-soft">
              {section.items.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          )}
        </section>
      ))}

      <section className="border-t border-line-soft pt-5">
        <h3 className="text-base font-bold text-ink">확인한 공개 자료</h3>
        {citedSources.length ? (
          <div className="mt-3 space-y-3">
            {citedSources.map((source) => (
              <SourceCard key={source.id} source={source} />
            ))}
          </div>
        ) : (
          <p className="mt-2 rounded-lg border border-dashed border-line px-4 py-3 text-sm leading-6 text-ink-soft">
            이번 브리핑에는 공개 출처 문장을 인용한 섹션이 없습니다. 이슈 정의와
            저장된 관찰 데이터 범위에서만 정리했습니다.
          </p>
        )}
      </section>

      {!hasAuthoredLimitations ? (
        <section className="rounded-lg bg-paper px-4 py-4">
          <h3 className="text-xs font-bold text-ink">데이터 한계</h3>
          <p className="mt-2 text-sm leading-7 text-ink-soft">
            {report.data_limitations}
          </p>
        </section>
      ) : null}
      <section className="rounded-lg border border-line bg-accent-soft px-4 py-4">
        <h3 className="text-xs font-bold text-ink">해석상 주의사항</h3>
        <p className="mt-2 text-sm leading-7 text-ink-soft">
          {report.caution_note}
        </p>
      </section>
    </div>
  );
}

function StreamingBriefingContent({
  briefing,
}: {
  briefing: StreamingBriefingState;
}) {
  return (
    <div className="mt-5 space-y-5" aria-live="polite">
      <div className="rounded-lg border-l-4 border-accent bg-accent-soft px-4 py-4 sm:px-5">
        <p className="text-[11px] font-bold text-ink-faint">
          검증을 마친 내용부터 표시 중
        </p>
        <h3 className="mt-2 text-xl font-bold leading-8 text-ink">
          {briefing.headline}
        </h3>
        <p className="mt-2 text-sm leading-7 text-ink-soft">
          {briefing.summary}
        </p>
      </div>
      {briefing.sections.map((section) => (
        <section
          key={`${section.type}-${section.title}`}
          className="border-t border-line-soft pt-5"
        >
          <h3 className="text-base font-bold text-ink">{section.title}</h3>
          {section.format === "paragraph" ? (
            <p className="mt-2 break-words text-sm leading-7 text-ink-soft">
              {section.content}
            </p>
          ) : (
            <ul className="mt-2 list-disc space-y-2 pl-5 text-sm leading-7 text-ink-soft">
              {section.items.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          )}
        </section>
      ))}
    </div>
  );
}

export function IssueReportCard({
  issueId,
  reportState,
  issueDataAsOf,
  onGenerate,
  generationPending,
  generationActionError,
  streamedBriefing,
  className = "mt-10",
}: IssueReportCardProps) {
  const response =
    reportState.status === "ready" ? reportState.response : undefined;
  const report = isFullReport(response) ? response : null;
  const isGenerating = response?.status === "generating";
  const dataAsOf = report?.data_as_of ?? issueDataAsOf;
  const canGenerate =
    reportState.status === "error" ||
    response?.status === "idle" ||
    response?.status === "failed" ||
    response?.status === "stale" ||
    response?.status === "failed_with_last_good";
  const retryWithStoredEvidence = response?.status === "failed";
  const actionLabel = retryWithStoredEvidence
    ? "저장된 근거로 다시 생성"
    : report
      ? "브리핑 새로고침"
      : "AI 브리핑 생성";

  return (
    <section
      data-issue-id={issueId}
      className={`${className} rounded-lg border border-line bg-card p-4 sm:p-5`}
      aria-labelledby="ai-briefing-title"
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h2 id="ai-briefing-title" className="text-lg font-bold text-ink">
              AI 이슈 브리핑
            </h2>
            <span className="rounded-full border border-line px-2 py-1 text-[11px] font-bold text-ink-faint">
              {statusLabel(response)}
            </span>
          </div>
          <p className="mt-1 max-w-2xl text-xs leading-5 text-ink-faint">
            요청한 시점의 이슈 정의, 관찰 데이터, 확인 가능한 공개 자료만
            사용합니다.
          </p>
        </div>
        <div className="flex flex-col items-start gap-1 text-xs font-semibold text-ink-faint sm:items-end">
          <span>데이터 기준 시각: {formatDataTimestamp(dataAsOf)}</span>
          {report ? (
            <span>생성 시각: {formatDataTimestamp(report.generated_at)}</span>
          ) : null}
          {report?.context_as_of ? (
            <span>
              자료 확인 시각: {formatDataTimestamp(report.context_as_of)}
            </span>
          ) : null}
        </div>
      </div>

      <ShortCautionNotice
        context="summary"
        dataAsOf={dataAsOf}
        className="mt-4"
        surface="plain"
      />

      {generationActionError ? (
        <p
          role="alert"
          className="mt-4 rounded-lg border border-line bg-paper px-4 py-3 text-sm leading-6 text-ink-soft"
        >
          브리핑 요청 상태를 확인하지 못했습니다. 잠시 후 다시 시도해 주세요.
        </p>
      ) : null}

      {reportState.status === "loading" ? (
        <div
          className="mt-5 rounded-lg border border-line-soft px-4 py-5"
          aria-label="브리핑 상태 불러오는 중"
        >
          <div className="h-3 w-40 animate-pulse rounded-full bg-line motion-reduce:animate-none" />
          <div className="mt-4 h-3 w-full max-w-3xl animate-pulse rounded-full bg-line-soft motion-reduce:animate-none" />
          <div className="mt-2 h-3 w-2/3 animate-pulse rounded-full bg-line-soft motion-reduce:animate-none" />
        </div>
      ) : null}

      {reportState.status === "error" ? (
        <div className="mt-5 rounded-lg border border-line px-4 py-5">
          <h3 className="text-sm font-bold text-ink">
            브리핑 상태를 불러오지 못했습니다
          </h3>
          <p className="mt-2 text-sm leading-6 text-ink-soft">
            이슈 정보와 차트는 계속 확인할 수 있습니다.
          </p>
        </div>
      ) : null}

      {response?.status === "idle" ? (
        <div className="mt-5 rounded-lg border border-dashed border-line px-4 py-5">
          <h3 className="text-sm font-bold text-ink">
            아직 생성된 브리핑이 없습니다
          </h3>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-ink-soft">
            버튼을 누르면 현재 저장된 근거 묶음으로 생성 요청을 기록합니다. 기본
            이슈 수집은 브리핑을 자동 생성하지 않습니다.
          </p>
        </div>
      ) : null}

      {isGenerating ? (
        <div
          role="status"
          aria-live="polite"
          className="mt-5 rounded-lg border border-line bg-paper px-4 py-4"
        >
          <div className="flex items-center gap-2 text-accent">
            <LoadingSpinner />
            <h3 className="text-sm font-bold text-ink">
              브리핑을 생성하고 있습니다
            </h3>
          </div>
          <p className="mt-1 text-sm leading-6 text-ink-soft">
            작성된 단락은 근거와 문구 검증을 통과한 뒤 순서대로 표시됩니다. 이
            화면을 떠나도 요청 기록은 유지됩니다.
          </p>
        </div>
      ) : null}

      {isGenerating && streamedBriefing ? (
        <StreamingBriefingContent briefing={streamedBriefing} />
      ) : null}

      {response?.status === "failed" ? (
        <div className="mt-5 rounded-lg border border-line px-4 py-5">
          <h3 className="text-sm font-bold text-ink">
            브리핑 생성을 완료하지 못했습니다
          </h3>
          <p className="mt-2 text-sm leading-6 text-ink-soft">
            검증되지 않은 임시 내용은 표시하지 않습니다.
          </p>
        </div>
      ) : null}

      {response?.status === "stale" ? (
        <p className="mt-5 rounded-lg border border-line bg-paper px-4 py-3 text-sm leading-6 text-ink-soft">
          이 브리핑 이후 새로운 관찰 데이터가 저장되었습니다. 아래 내용은 마지막
          정상 결과이며 새로고침을 요청할 수 있습니다.
        </p>
      ) : null}
      {response?.status === "failed_with_last_good" ? (
        <p className="mt-5 rounded-lg border border-line bg-paper px-4 py-3 text-sm leading-6 text-ink-soft">
          최근 새로고침은 완료되지 않았습니다. 검증을 통과한 이전 브리핑을 계속
          표시합니다.
        </p>
      ) : null}

      {report ? <BriefingContent report={report} /> : null}

      {canGenerate ? (
        <div className="mt-5 flex flex-wrap items-center gap-3">
          <ActionButton
            label={actionLabel}
            pending={generationPending}
            onGenerate={() => void onGenerate(!retryWithStoredEvidence)}
          />
          <p className="text-xs leading-5 text-ink-faint">
            {retryWithStoredEvidence
              ? "이전 시도는 저장되지 않았습니다. 현재 저장된 근거만 사용해 다시 생성합니다."
              : "확인 가능한 공개 자료를 새로 살핀 뒤 현재 근거 묶음으로 브리핑을 생성합니다."}
          </p>
        </div>
      ) : null}
    </section>
  );
}
