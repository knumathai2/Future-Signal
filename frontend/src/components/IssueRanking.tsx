import { Link } from "react-router-dom";
import { CautionBadge } from "./CautionBadge";
import { DirectionalChange } from "./DirectionalChange";
import type { Issue } from "../types/issue";
import type { ListWindow } from "../utils/routeState";
import {
  formatCategoryLabel,
  formatCompactDataTimestamp,
  formatExpectationValue,
  issueChangeForWindow,
  windowLabel,
} from "../utils/format";

type IssueRankingProps = {
  issues: Issue[];
  windowKey: ListWindow;
  from: string;
};

function IssueTitleLink({ issue, from }: { issue: Issue; from: string }) {
  return (
    <Link
      to={`/issues/${encodeURIComponent(issue.id)}`}
      state={{ from }}
      className="inline-flex min-h-11 items-center rounded-sm font-bold leading-5 text-ink transition hover:text-accent"
    >
      {issue.title}
    </Link>
  );
}

/** Top-five selected-window ranking with desktop table and mobile cards. */
export function IssueRanking({ issues, windowKey, from }: IssueRankingProps) {
  return (
    <>
      <div className="hidden overflow-hidden rounded-xl border border-line bg-card md:block">
        <table className="w-full table-fixed border-collapse text-left">
          <caption className="sr-only">
            {windowLabel(windowKey)} 관측 변화폭 상위 5개 이슈
          </caption>
          <colgroup>
            <col className="w-[7%]" />
            <col className="w-[35%]" />
            <col className="w-[25%]" />
            <col className="w-[16%]" />
            <col className="w-[17%]" />
          </colgroup>
          <thead className="bg-line-soft text-[11px] font-bold text-ink-soft">
            <tr>
              <th className="px-3 py-3" scope="col">
                순위
              </th>
              <th className="px-3 py-3" scope="col">
                이슈
              </th>
              <th className="px-3 py-3" scope="col">
                카테고리 · 해석 주의
              </th>
              <th className="px-3 py-3 text-right" scope="col">
                현재 기대값
              </th>
              <th className="px-3 py-3 text-right" scope="col">
                {windowLabel(windowKey)} 변화
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line-soft">
            {issues.map((issue, index) => (
              <tr key={issue.id} className="align-top">
                <th
                  scope="row"
                  className="px-3 py-4 text-base font-extrabold text-ink"
                >
                  {index + 1}
                </th>
                <td className="break-words px-3 py-4 text-sm">
                  <IssueTitleLink issue={issue} from={from} />
                  <span className="mt-2 block text-[10px] font-semibold text-ink-faint">
                    기준 {formatCompactDataTimestamp(issue.dataAsOf)}
                  </span>
                </td>
                <td className="px-3 py-4">
                  <span className="mb-2 block break-words text-[11px] font-bold text-ink-soft">
                    {issue.topicLabel ?? formatCategoryLabel(issue.category)}
                  </span>
                  <CautionBadge level={issue.cautionLevel} />
                </td>
                <td className="px-3 py-4 text-right text-sm font-bold text-ink">
                  {formatExpectationValue(issue.currentExpectationValue)}
                </td>
                <td className="px-3 py-4 text-right text-sm font-extrabold">
                  <DirectionalChange
                    value={issueChangeForWindow(issue, windowKey)}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <ol className="space-y-3 md:hidden">
        {issues.map((issue, index) => (
          <li key={issue.id}>
            <article className="rounded-xl border border-line bg-card p-4">
              <div className="flex items-start gap-3">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-line-soft text-sm font-extrabold text-ink">
                  {index + 1}
                </span>
                <div className="min-w-0 flex-1">
                  <IssueTitleLink issue={issue} from={from} />
                  <div className="mt-2 flex flex-wrap items-center gap-2">
                    <span className="text-[11px] font-bold text-ink-soft">
                      {issue.topicLabel ?? formatCategoryLabel(issue.category)}
                    </span>
                    <CautionBadge level={issue.cautionLevel} />
                  </div>
                </div>
              </div>

              <dl className="mt-4 grid grid-cols-2 gap-3 border-t border-line-soft pt-3">
                <div>
                  <dt className="text-[11px] font-semibold text-ink-faint">
                    현재 기대값
                  </dt>
                  <dd className="mt-1 text-base font-bold text-ink">
                    {formatExpectationValue(issue.currentExpectationValue)}
                  </dd>
                </div>
                <div>
                  <dt className="text-[11px] font-semibold text-ink-faint">
                    {windowLabel(windowKey)} 변화
                  </dt>
                  <dd className="mt-1 text-base font-extrabold">
                    <DirectionalChange
                      value={issueChangeForWindow(issue, windowKey)}
                    />
                  </dd>
                </div>
              </dl>
              <p className="mt-3 text-[10px] font-semibold text-ink-faint">
                데이터 기준 시각: {formatCompactDataTimestamp(issue.dataAsOf)}
              </p>
            </article>
          </li>
        ))}
      </ol>
    </>
  );
}
