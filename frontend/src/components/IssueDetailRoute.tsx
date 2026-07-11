import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Link,
  useLocation,
  useParams,
  useSearchParams,
} from "react-router-dom";
import { SiteHeader } from "./AppShell";
import { IssueDetail } from "./IssueDetail";
import { staleDummyIssues } from "../data/dummyIssues";
import { getDevelopmentReportFixture } from "../data/reportFixtures";
import type { DataStatus, Issue, IssueReportLoadState } from "../types/issue";
import {
  fetchJson,
  HttpError,
  loadGenerationRequestStatus,
  loadIssueReport,
  requestIssueReport,
} from "../utils/api";
import { focusRouteHeading } from "../utils/focus";
import {
  type ApiIssueDetail,
  type ApiIssueHistoryResponse,
  mapApiIssueDetailToFrontendIssue,
} from "../utils/format";
import { parseForcedStatus } from "../utils/routeState";
import { parseReportResponse } from "../utils/reportParser";

type HistoryStatus = "loading" | "ready" | "error";

function safeBackPath(value: unknown): string {
  return typeof value === "string" &&
    value.startsWith("/") &&
    !value.startsWith("//")
    ? value
    : "/issues";
}

function DetailRouteState({
  title,
  description,
  backTo,
}: {
  title: string;
  description: string;
  backTo: string;
}) {
  useEffect(() => {
    const frame = window.requestAnimationFrame(focusRouteHeading);
    return () => window.cancelAnimationFrame(frame);
  }, [title]);

  return (
    <div className="mx-auto min-h-screen w-full max-w-[1180px] px-4 py-4 sm:px-8 sm:py-6 lg:px-10 lg:py-8">
      <SiteHeader />
      <main
        id="main-content"
        data-route-main
        tabIndex={-1}
        aria-labelledby="detail-route-state-title"
        className="mt-12 text-center outline-none"
      >
        <h1
          id="detail-route-state-title"
          className="text-xl font-bold text-ink"
        >
          {title}
        </h1>
        <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-ink-soft">
          {description}
        </p>
        <Link
          to={backTo}
          className="mt-5 inline-flex min-h-11 items-center rounded-full border border-line px-4 text-sm font-bold text-accent"
        >
          이전 화면으로 돌아가기
        </Link>
      </main>
    </div>
  );
}

/** Route loader that progressively combines core detail, history, and report data. */
export function IssueDetailRoute() {
  const { issueId = "" } = useParams();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const forcedStatus = parseForcedStatus(searchParams);
  const reportFixtureName = searchParams.get("report");
  const developmentReportState = useMemo<IssueReportLoadState | null>(() => {
    if (reportFixtureName === "loading") return { status: "loading" };
    if (reportFixtureName === "empty")
      return { status: "ready", response: { status: "idle" } };
    if (reportFixtureName === "error") return { status: "error" };
    const fixture = getDevelopmentReportFixture(reportFixtureName);
    return fixture ? parseReportResponse(fixture) : null;
  }, [reportFixtureName]);
  const backTo = safeBackPath(
    (location.state as { from?: unknown } | null)?.from,
  );

  const [detailStatus, setDetailStatus] = useState<DataStatus>("loading");
  const [historyStatus, setHistoryStatus] = useState<HistoryStatus>("loading");
  const [apiDetail, setApiDetail] = useState<ApiIssueDetail | null>(null);
  const [apiHistory, setApiHistory] = useState<ApiIssueHistoryResponse | null>(
    null,
  );
  const [fallbackIssue, setFallbackIssue] = useState<Issue | null>(null);
  const [reportState, setReportState] = useState<IssueReportLoadState>({
    status: "loading",
  });
  const [generationPending, setGenerationPending] = useState(false);
  const [generationActionError, setGenerationActionError] = useState(false);

  useEffect(() => {
    setApiDetail(null);
    setApiHistory(null);
    setFallbackIssue(null);
    setHistoryStatus("loading");
    setReportState({ status: "loading" });
    setGenerationPending(false);
    setGenerationActionError(false);

    if (!issueId) {
      setDetailStatus("empty");
      setHistoryStatus("error");
      setReportState({ status: "ready", response: { status: "idle" } });
      return;
    }

    if (forcedStatus) {
      if (forcedStatus === "error") {
        setFallbackIssue(
          staleDummyIssues.find((issue) => issue.id === issueId) ??
            staleDummyIssues[0],
        );
        setHistoryStatus("ready");
        setReportState(developmentReportState ?? { status: "error" });
      } else if (forcedStatus === "empty") {
        setHistoryStatus("error");
        setReportState({ status: "ready", response: { status: "idle" } });
      }
      setDetailStatus(forcedStatus);
      return;
    }

    const controller = new AbortController();
    setDetailStatus("loading");

    fetchJson<ApiIssueDetail>(
      `/api/issues/${encodeURIComponent(issueId)}`,
      "Failed to load issue details",
      controller.signal,
    )
      .then((detail) => {
        setApiDetail(detail);
        setDetailStatus("ready");
      })
      .catch((error) => {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        console.error(error);
        if (error instanceof HttpError && error.status === 404) {
          setDetailStatus("empty");
          return;
        }
        const fallback =
          staleDummyIssues.find((issue) => issue.id === issueId) ?? null;
        setFallbackIssue(fallback);
        setDetailStatus("error");
      });

    fetchJson<ApiIssueHistoryResponse>(
      `/api/issues/${encodeURIComponent(issueId)}/history?window=30d`,
      "Failed to load issue history",
      controller.signal,
    )
      .then((history) => {
        setApiHistory(history);
        setHistoryStatus("ready");
      })
      .catch((error) => {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        console.error(error);
        setHistoryStatus("error");
      });

    if (developmentReportState) {
      setReportState(developmentReportState);
    } else {
      loadIssueReport(issueId, controller.signal)
        .then(setReportState)
        .catch((error) => {
          if (error instanceof DOMException && error.name === "AbortError") {
            return;
          }
          setReportState({ status: "error" });
        });
    }

    return () => controller.abort();
  }, [developmentReportState, forcedStatus, issueId]);

  const activeRequestId =
    reportState.status === "ready" &&
    reportState.response.status === "generating"
      ? reportState.response.request_id
      : null;

  useEffect(() => {
    if (!activeRequestId || developmentReportState) return;
    const controller = new AbortController();
    let checking = false;
    const check = async () => {
      if (checking) return;
      checking = true;
      try {
        const request = await loadGenerationRequestStatus(
          issueId,
          activeRequestId,
          controller.signal,
        );
        if (request.state === "succeeded" || request.state === "failed") {
          const next = await loadIssueReport(issueId, controller.signal);
          setReportState(next);
          setGenerationPending(false);
        }
      } catch (error) {
        if (!(error instanceof DOMException && error.name === "AbortError"))
          console.error(error);
      } finally {
        checking = false;
      }
    };
    void check();
    const interval = window.setInterval(check, 1500);
    return () => {
      controller.abort();
      window.clearInterval(interval);
    };
  }, [activeRequestId, developmentReportState, issueId]);

  const handleGenerate = useCallback(
    async (refreshContext: boolean) => {
      setGenerationPending(true);
      setGenerationActionError(false);
      try {
        await requestIssueReport(issueId, refreshContext);
        setReportState(await loadIssueReport(issueId));
      } catch (error) {
        console.error(error);
        setGenerationActionError(true);
      } finally {
        setGenerationPending(false);
      }
    },
    [issueId],
  );

  const issue = useMemo(() => {
    if (fallbackIssue) {
      return fallbackIssue;
    }
    if (!apiDetail) {
      return null;
    }

    return mapApiIssueDetailToFrontendIssue(
      apiDetail,
      apiHistory ?? {
        data_as_of: apiDetail.data_as_of,
        window: "30d",
        points: [],
      },
    );
  }, [apiDetail, apiHistory, fallbackIssue]);

  if (detailStatus === "loading") {
    return (
      <DetailRouteState
        title="이슈 상세 정보를 불러오는 중입니다"
        description="기본 정보가 준비되는 즉시 표시하고 차트와 이슈 요약은 이어서 불러옵니다."
        backTo={backTo}
      />
    );
  }

  if (detailStatus === "empty") {
    return (
      <DetailRouteState
        title="이슈 상세 정보를 찾을 수 없습니다"
        description="주소가 올바른지 확인하거나 전체 이슈 목록에서 다시 선택해 주세요."
        backTo="/issues"
      />
    );
  }

  if (!issue) {
    return (
      <DetailRouteState
        title="이슈 상세 정보를 불러오지 못했습니다"
        description="잠시 후 목록에서 다시 선택해 주세요."
        backTo={backTo}
      />
    );
  }

  return (
    <IssueDetail
      issue={issue}
      dataStatus={detailStatus}
      reportState={reportState}
      historyStatus={historyStatus}
      backTo={backTo}
      onGenerateReport={handleGenerate}
      generationPending={generationPending}
      generationActionError={generationActionError}
    />
  );
}
