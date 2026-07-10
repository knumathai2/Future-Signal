import type { CategorySummary, DirectionSummary, Issue } from "../types/issue";
import { issueChangeForWindow } from "./format";
import type { ListWindow } from "./routeState";

function validChange(value: number | null | undefined): value is number {
  return value !== null && value !== undefined && Number.isFinite(value);
}

/** Sort by absolute selected-window change while keeping insufficient rows last. */
export function rankIssuesByChange(
  issues: Issue[],
  windowKey: ListWindow,
): Issue[] {
  return issues
    .map((issue, index) => ({ issue, index }))
    .sort((left, right) => {
      const leftChange = issueChangeForWindow(left.issue, windowKey);
      const rightChange = issueChangeForWindow(right.issue, windowKey);
      const leftValid = validChange(leftChange);
      const rightValid = validChange(rightChange);

      if (leftValid && rightValid) {
        return (
          Math.abs(rightChange) - Math.abs(leftChange) ||
          left.index - right.index
        );
      }
      if (leftValid) {
        return -1;
      }
      if (rightValid) {
        return 1;
      }
      return left.index - right.index;
    })
    .map(({ issue }) => issue);
}

/** Count direction states and calculate ratios over upward plus downward issues. */
export function buildDirectionSummary(
  issues: Issue[],
  windowKey: ListWindow,
): DirectionSummary {
  let upwardCount = 0;
  let downwardCount = 0;
  let unchangedCount = 0;
  let insufficientCount = 0;

  issues.forEach((issue) => {
    const change = issueChangeForWindow(issue, windowKey);
    if (!validChange(change)) {
      insufficientCount += 1;
    } else if (change > 0) {
      upwardCount += 1;
    } else if (change < 0) {
      downwardCount += 1;
    } else {
      unchangedCount += 1;
    }
  });

  const directionalCount = upwardCount + downwardCount;
  const upwardRatio = directionalCount
    ? (upwardCount / directionalCount) * 100
    : 0;
  const downwardRatio = directionalCount
    ? (downwardCount / directionalCount) * 100
    : 0;

  return {
    upwardCount,
    downwardCount,
    unchangedCount,
    insufficientCount,
    directionalCount,
    upwardRatio,
    downwardRatio,
  };
}

/** Calculate the simple mean of valid selected-window changes for a category. */
export function buildCategorySummary(
  label: string,
  issues: Issue[],
  windowKey: ListWindow,
): CategorySummary {
  const validChanges = issues
    .map((issue) => issueChangeForWindow(issue, windowKey))
    .filter(validChange);
  const averageChange = validChanges.length
    ? Number(
        (
          validChanges.reduce((sum, change) => sum + change, 0) /
          validChanges.length
        ).toFixed(1),
      )
    : null;

  return {
    label,
    totalCount: issues.length,
    validCount: validChanges.length,
    averageChange,
  };
}
