import { useEffect, useMemo, useState } from "react";
import { Dashboard } from "./components/Dashboard";
import { IssueDetail } from "./components/IssueDetail";
import {
  dummyDataAsOf,
  dummyIssues,
  staleDummyDataAsOf,
  staleDummyIssues,
} from "./data/dummyIssues";
import type { DataStatus } from "./types/issue";

type Screen = "dashboard" | "detail";

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
  const initialIssues = forcedStatus === "error" ? staleDummyIssues : dummyIssues;
  const [selectedIssueId, setSelectedIssueId] = useState(initialIssues[0]?.id ?? "");
  const [status, setStatus] = useState<DataStatus>(forcedStatus ?? "loading");
  const [issues, setIssues] = useState(() =>
    forcedStatus === "empty" ? [] : initialIssues,
  );
  const activeDataAsOf = status === "error" ? staleDummyDataAsOf : dummyDataAsOf;

  useEffect(() => {
    if (forcedStatus) {
      return undefined;
    }

    const timer = window.setTimeout(() => {
      setIssues(dummyIssues);
      setStatus(dummyIssues.length ? "ready" : "empty");
    }, 320);

    return () => window.clearTimeout(timer);
  }, [forcedStatus]);

  const selectedIssue = useMemo(
    () => issues.find((issue) => issue.id === selectedIssueId) ?? issues[0],
    [issues, selectedIssueId],
  );

  function handleIssueSelect(issueId: string) {
    setSelectedIssueId(issueId);
    setScreen("detail");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function handleRefresh() {
    if (forcedStatus) {
      setStatus(forcedStatus);
      return;
    }

    setStatus("loading");
    window.setTimeout(() => {
      setIssues(dummyIssues);
      setStatus(dummyIssues.length ? "ready" : "empty");
    }, 420);
  }

  if (screen === "detail" && selectedIssue) {
    return (
      <IssueDetail
        issue={selectedIssue}
        dataStatus={status}
        onBack={() => setScreen("dashboard")}
      />
    );
  }

  return (
    <Dashboard
      issues={issues}
      status={status}
      dataAsOf={activeDataAsOf}
      staleDataAsOf={staleDummyDataAsOf}
      onIssueSelect={handleIssueSelect}
      onRefresh={handleRefresh}
    />
  );
}
