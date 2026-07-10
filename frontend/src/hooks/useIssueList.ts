import { useCallback, useEffect, useRef, useState } from "react";
import { staleDummyDataAsOf, staleDummyIssues } from "../data/dummyIssues";
import type {
  ChartWindow,
  DataStatus,
  Issue,
  IssueListSort,
} from "../types/issue";
import { fetchJson } from "../utils/api";
import {
  type ApiIssueListResponse,
  formatCategoryLabel,
  mapApiIssueToFrontendIssue,
} from "../utils/format";

type UseIssueListOptions = {
  windowKey: Extract<ChartWindow, "24h" | "7d">;
  sort: IssueListSort;
  category?: string;
  forcedStatus?: DataStatus | null;
};

type IssueListState = {
  issues: Issue[];
  status: DataStatus;
  isRefreshing: boolean;
  dataAsOf: string;
  staleDataAsOf: string;
  refresh: () => void;
};

function fallbackIssues(category?: string): Issue[] {
  if (!category) {
    return staleDummyIssues;
  }

  return staleDummyIssues.filter(
    (issue) => formatCategoryLabel(issue.category) === category,
  );
}

/** Load up to the complete MVP issue set while retaining visible rows on refresh. */
export function useIssueList({
  windowKey,
  sort,
  category,
  forcedStatus = null,
}: UseIssueListOptions): IssueListState {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [status, setStatus] = useState<DataStatus>(forcedStatus ?? "loading");
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [dataAsOf, setDataAsOf] = useState(staleDummyDataAsOf);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const hasVisibleIssues = useRef(false);

  const refresh = useCallback(() => {
    setRefreshTrigger((value) => value + 1);
  }, []);

  useEffect(() => {
    if (forcedStatus) {
      if (forcedStatus === "empty") {
        hasVisibleIssues.current = false;
        setIssues([]);
      } else if (forcedStatus === "error") {
        const fallback = fallbackIssues(category);
        hasVisibleIssues.current = fallback.length > 0;
        setIssues(fallback);
        setDataAsOf(staleDummyDataAsOf);
      } else {
        hasVisibleIssues.current = false;
        setIssues([]);
      }
      setStatus(forcedStatus);
      setIsRefreshing(false);
      return;
    }

    const controller = new AbortController();
    let isMounted = true;

    async function loadIssues() {
      if (hasVisibleIssues.current) {
        setIsRefreshing(true);
      } else {
        setStatus("loading");
      }

      try {
        const params = new URLSearchParams({
          window: windowKey,
          sort,
          limit: "100",
        });
        if (category) {
          params.set("category", category);
        }

        const data = await fetchJson<ApiIssueListResponse>(
          `/api/issues?${params.toString()}`,
          "Failed to load issues",
          controller.signal,
        );
        if (!isMounted) {
          return;
        }

        const mapped = data.issues.map((issue) =>
          mapApiIssueToFrontendIssue(issue, data.data_as_of),
        );
        hasVisibleIssues.current = mapped.length > 0;
        setIssues(mapped);
        setDataAsOf(data.data_as_of);
        setStatus(mapped.length > 0 ? "ready" : "empty");
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        console.error(error);
        if (!isMounted) {
          return;
        }

        if (!hasVisibleIssues.current) {
          const fallback = fallbackIssues(category);
          hasVisibleIssues.current = fallback.length > 0;
          setIssues(fallback);
          setDataAsOf(staleDummyDataAsOf);
        }
        setStatus("error");
      } finally {
        if (isMounted) {
          setIsRefreshing(false);
        }
      }
    }

    void loadIssues();
    return () => {
      isMounted = false;
      controller.abort();
    };
  }, [category, forcedStatus, refreshTrigger, sort, windowKey]);

  return {
    issues,
    status,
    isRefreshing,
    dataAsOf,
    staleDataAsOf: staleDummyDataAsOf,
    refresh,
  };
}
