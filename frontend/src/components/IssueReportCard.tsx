import { CautionBadge } from "./CautionBadge";
import { ShortCautionNotice } from "./InformationNotice";
import type {
  Issue,
  IssueReportContent,
  IssueReportLoadState,
} from "../types/issue";
import { formatDataTimestamp } from "../utils/format";

type IssueReportCardProps = {
  issue: Issue;
  reportState: IssueReportLoadState;
  fallbackSummary: string;
};

const REPORT_SECTIONS: Array<{
  key: keyof IssueReportContent;
  label: string;
}> = [
  { key: "issue_summary", label: "이슈 개요" },
  { key: "movement_explanation", label: "관측 변화 설명" },
  { key: "key_change_context", label: "주요 변화 맥락" },
  { key: "uncertainty_summary", label: "불확실성 요약" },
  { key: "neutral_conclusion", label: "중립 결론" },
];

function reportDataAsOf(
  reportState: IssueReportLoadState,
  fallbackDataAsOf: string,
): string {
  return reportState.status === "success"
    ? reportState.report.data_as_of
    : fallbackDataAsOf;
}

function ReportBody({
  reportState,
  fallbackSummary,
}: {
  reportState: IssueReportLoadState;
  fallbackSummary: string;
}) {
  if (reportState.status === "loading") {
    return (
      <div className="mt-4 rounded-lg border border-line-soft px-4 py-4">
        <div className="h-3 w-40 animate-pulse rounded-full bg-line" />
        <div className="mt-3 h-3 w-full max-w-3xl animate-pulse rounded-full bg-line-soft" />
        <div className="mt-2 h-3 w-2/3 animate-pulse rounded-full bg-line-soft" />
      </div>
    );
  }

  if (reportState.status === "success") {
    return (
      <div className="mt-4 divide-y divide-line-soft">
        {REPORT_SECTIONS.map((section) => (
          <section key={section.key} className="py-4 first:pt-0 last:pb-0">
            <h3 className="text-sm font-bold text-ink">{section.label}</h3>
            <p className="mt-2 max-w-4xl text-sm leading-7 text-ink-soft">
              {reportState.report.content[section.key]}
            </p>
          </section>
        ))}
      </div>
    );
  }

  if (reportState.status === "not_yet_generated") {
    return (
      <div className="mt-4 rounded-lg border border-dashed border-line px-4 py-4">
        <h3 className="text-sm font-bold text-ink">
          저장된 템플릿 요약이 아직 없습니다
        </h3>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-ink-soft">
          이슈 정보와 차트는 계속 확인할 수 있습니다. 요약이 생성되면 이 영역에
          고정된 섹션 형식으로 표시됩니다.
        </p>
      </div>
    );
  }

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

export function IssueReportCard({
  issue,
  reportState,
  fallbackSummary,
}: IssueReportCardProps) {
  const dataAsOf = reportDataAsOf(reportState, issue.dataAsOf);

  return (
    <section className="mt-10 rounded-lg border border-line bg-card p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-ink">이슈 요약</h2>
          <p className="mt-1 text-[11px] font-semibold text-ink-faint">
            템플릿 기반 데이터 요약
          </p>
        </div>
        <div className="flex flex-col items-start gap-2 sm:items-end">
          <CautionBadge level={issue.cautionLevel} />
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

      <ReportBody reportState={reportState} fallbackSummary={fallbackSummary} />

      <ShortCautionNotice
        context="summary"
        cautionLevel={issue.cautionLevel}
        dataAsOf={dataAsOf}
        className="mt-4"
        surface="plain"
      />
    </section>
  );
}
