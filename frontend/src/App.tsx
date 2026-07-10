import { useEffect, useMemo, useState } from "react";
import { Dashboard } from "./components/Dashboard";
import { InformationNoticeScreen } from "./components/InformationNotice";
import { IssueDetail } from "./components/IssueDetail";
import { staleDummyDataAsOf, staleDummyIssues } from "./data/dummyIssues";
import type {
  DataStatus,
  Issue,
  IssueReportLoadState,
} from "./types/issue";
import { parseReportResponse } from "./utils/reportParser";
import {
  mapApiIssueToFrontendIssue,
  mapApiIssueDetailToFrontendIssue,
  ApiIssueListResponse,
  ApiIssueDetail,
  ApiIssueHistoryResponse,
} from "./utils/format";

type Screen = "dashboard" | "detail" | "notice";

async function fetchJson<T>(url: string, message: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(message);
  }

  return (await res.json()) as T;
}

async function loadIssueReport(issueId: string): Promise<IssueReportLoadState> {
  try {
    const res = await fetch(`/api/issues/${issueId}/report`);
    if (!res.ok) {
      throw new Error("Failed to load issue report");
    }

    const raw: unknown = await res.json();
    return parseReportResponse(raw);
  } catch (err) {
    console.error(err);
    return { status: "error" };
  }
}

function statusFromQuery(): DataStatus | null {
  if (typeof window === "undefined") {
    return null;
  }

  const queryStatus = new URLSearchParams(window.location.search).get("state");

  if (
    queryStatus === "loading" ||
    queryStatus === "empty" ||
    queryStatus === "error"
  ) {
    return queryStatus;
  }

  return null;
}

export default function App() {
  const forcedStatus = useMemo(() => statusFromQuery(), []);
  const [screen, setScreen] = useState<Screen>("dashboard");
  const [previousScreen, setPreviousScreen] = useState<Screen>("dashboard");
  const [selectedIssueId, setSelectedIssueId] = useState("");

  // Dashboard states
  const [status, setStatus] = useState<DataStatus>(forcedStatus ?? "loading");
  const [issues, setIssues] = useState<Issue[]>([]);
  const [apiDataAsOf, setApiDataAsOf] = useState(staleDummyDataAsOf);
  const [categories, setCategories] = useState<string[]>([]);

  // Filter/Query states
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [activeWindow, setActiveWindow] = useState<"24h" | "7d">("24h");
  const [activeSort, setActiveSort] = useState<"heat" | "change" | "recent">(
    "heat",
  );

  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Detail states
  const [detailIssue, setDetailIssue] = useState<Issue | null>(null);
  const [detailStatus, setDetailStatus] = useState<DataStatus>("loading");
  const [detailReportState, setDetailReportState] =
    useState<IssueReportLoadState>({ status: "loading" });

  // Load categories list
  useEffect(() => {
    async function loadCategories() {
      try {
        const res = await fetch("/api/categories");
        if (!res.ok) throw new Error("Failed to load categories");
        const data = await res.json();
        setCategories(data.categories || []);
      } catch (err) {
        console.error(err);
      }
    }
    loadCategories();
  }, []);

  // Fetch dashboard issues
  useEffect(() => {
    if (forcedStatus) {
      if (forcedStatus === "empty") {
        setIssues([]);
        setStatus("empty");
      } else if (forcedStatus === "error") {
        setIssues(staleDummyIssues);
        setStatus("error");
        setApiDataAsOf(staleDummyDataAsOf);
      } else {
        setIssues([]);
        setStatus("loading");
      }
      return;
    }

    let isMounted = true;
    async function loadIssues() {
      setStatus("loading");
      try {
        const params = new URLSearchParams();
        if (activeCategory) {
          params.append("category", activeCategory);
        }
        params.append("window", activeWindow);
        params.append("sort", activeSort);

        const res = await fetch(`/api/issues?${params.toString()}`);
        if (!res.ok) throw new Error("API failed");
        const data = (await res.json()) as ApiIssueListResponse;

        if (isMounted) {
          const mapped = data.issues.map((i) =>
            mapApiIssueToFrontendIssue(i, data.data_as_of),
          );
          setIssues(mapped);
          setApiDataAsOf(data.data_as_of);
          setStatus(mapped.length ? "ready" : "empty");
        }
      } catch (err) {
        console.error(err);
        if (isMounted) {
          setIssues(staleDummyIssues);
          setApiDataAsOf(staleDummyDataAsOf);
          setStatus("error");
        }
      }
    }

    loadIssues();
    return () => {
      isMounted = false;
    };
  }, [activeCategory, activeWindow, activeSort, refreshTrigger, forcedStatus]);

  // Fetch issue detail + history when selected
  useEffect(() => {
    if (screen !== "detail" || !selectedIssueId) {
      return;
    }

    if (forcedStatus) {
      if (forcedStatus === "error") {
        const fallback =
          staleDummyIssues.find((i) => i.id === selectedIssueId) ||
          staleDummyIssues[0];
        setDetailIssue(fallback);
        setDetailStatus("error");
        setDetailReportState({ status: "error" });
      } else if (forcedStatus === "empty") {
        setDetailIssue(null);
        setDetailStatus("empty");
        setDetailReportState({ status: "not_yet_generated" });
      } else {
        setDetailIssue(null);
        setDetailStatus("loading");
        setDetailReportState({ status: "loading" });
      }
      return;
    }

    let isMounted = true;
    let shouldAcceptReport = true;
    async function loadDetail() {
      setDetailStatus("loading");
      setDetailReportState({ status: "loading" });

      loadIssueReport(selectedIssueId).then((reportState) => {
        if (isMounted && shouldAcceptReport) {
          setDetailReportState(reportState);
        }
      });

      try {
        const [apiDetail, apiHistory] = await Promise.all([
          fetchJson<ApiIssueDetail>(
            `/api/issues/${selectedIssueId}`,
            "Failed to load details",
          ),
          fetchJson<ApiIssueHistoryResponse>(
            `/api/issues/${selectedIssueId}/history?window=30d`,
            "Failed to load history",
          ),
        ]);

        if (isMounted) {
          const mapped = mapApiIssueDetailToFrontendIssue(
            apiDetail,
            apiHistory,
          );
          setDetailIssue(mapped);
          setDetailStatus("ready");
        }
      } catch (err) {
        console.error(err);
        shouldAcceptReport = false;
        if (isMounted) {
          const fallback =
            staleDummyIssues.find((i) => i.id === selectedIssueId) ||
            staleDummyIssues[0];
          setDetailIssue(fallback);
          setDetailStatus("error");
          setDetailReportState({ status: "error" });
        }
      }
    }

    loadDetail();
    return () => {
      isMounted = false;
    };
  }, [screen, selectedIssueId, refreshTrigger, forcedStatus]);

  function handleIssueSelect(issueId: string) {
    setSelectedIssueId(issueId);
    setScreen("detail");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function handleOpenNotice() {
    setPreviousScreen(screen === "notice" ? "dashboard" : screen);
    setScreen("notice");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function handleCloseNotice() {
    setScreen(previousScreen === "notice" ? "dashboard" : previousScreen);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function handleOpenDashboard() {
    setScreen("dashboard");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function handleRefresh() {
    setRefreshTrigger((prev) => prev + 1);
  }

  if (screen === "notice") {
    return (
      <InformationNoticeScreen
        onBack={handleCloseNotice}
        onOpenDashboard={handleOpenDashboard}
      />
    );
  }

  if (screen === "detail") {
    if (detailStatus === "loading") {
      return (
        <div className="mx-auto min-h-screen w-full max-w-[1180px] px-4 py-6 sm:px-8 lg:px-10 lg:py-10 flex flex-col items-center justify-center">
          <div className="text-sm font-semibold text-ink-soft animate-pulse">
            이슈 상세 정보를 불러오는 중입니다...
          </div>
          <button
            type="button"
            onClick={() => setScreen("dashboard")}
            className="mt-4 text-sm font-semibold text-accent hover:underline"
          >
            대시보드로 돌아가기
          </button>
        </div>
      );
    }

    if (detailStatus === "empty" || !detailIssue) {
      return (
        <div className="mx-auto min-h-screen w-full max-w-[1180px] px-4 py-6 sm:px-8 lg:px-10 lg:py-10 text-center">
          <h2 className="text-base font-bold text-ink">
            이슈 상세 정보를 찾을 수 없습니다
          </h2>
          <button
            type="button"
            onClick={() => setScreen("dashboard")}
            className="mt-4 text-sm font-semibold text-accent hover:underline"
          >
            대시보드로 돌아가기
          </button>
        </div>
      );
    }

    return (
      <IssueDetail
        issue={detailIssue}
        dataStatus={detailStatus}
        reportState={detailReportState}
        onBack={() => setScreen("dashboard")}
        onOpenNotice={handleOpenNotice}
      />
    );
  }

  return (
    <Dashboard
      issues={issues}
      status={status}
      dataAsOf={apiDataAsOf}
      staleDataAsOf={staleDummyDataAsOf}
      onIssueSelect={handleIssueSelect}
      onRefresh={handleRefresh}
      onOpenNotice={handleOpenNotice}
      categories={categories}
      activeCategory={activeCategory}
      onCategoryChange={setActiveCategory}
      activeWindow={activeWindow}
      onWindowChange={setActiveWindow}
      activeSort={activeSort}
      onSortChange={setActiveSort}
    />
  );
}
