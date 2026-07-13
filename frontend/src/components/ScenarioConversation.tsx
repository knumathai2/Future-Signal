import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { CautionBadge } from "./CautionBadge";
import { LoadingSpinner } from "./LoadingSpinner";
import type {
  Issue,
  ScenarioContentBlock,
  ScenarioPremiseClass,
  ScenarioSession,
  ScenarioTurn,
  ScenarioTurnCreated,
} from "../types/issue";
import {
  createScenarioSession,
  createScenarioTurn,
  deleteScenarioSession,
  HttpError,
  loadScenarioSession,
  loadScenarioTurnStatus,
  subscribeToScenarioStream,
} from "../utils/api";
import { formatDataTimestamp } from "../utils/format";
import { parseScenarioMarkdown } from "../utils/scenarioParser";

type SessionCredential = { sessionId: string; capability: string };
type ViewState =
  "idle" | "loading" | "ready" | "unavailable" | "expired" | "error";

const NOTICE =
  "이 대화는 이슈의 조건부 전개를 살펴봅니다. 시나리오는 현재 사실이나 실제 결과에 대한 단정이 아닙니다.";

function storageKey(issueId: string): string {
  return `outlook-signals:scenario:${issueId}`;
}

function readCredential(issueId: string): SessionCredential | null {
  try {
    const raw = window.sessionStorage.getItem(storageKey(issueId));
    if (!raw) return null;
    const value: unknown = JSON.parse(raw);
    if (
      typeof value !== "object" ||
      value === null ||
      !("sessionId" in value) ||
      !("capability" in value) ||
      typeof value.sessionId !== "string" ||
      typeof value.capability !== "string" ||
      value.capability.length < 40 ||
      value.capability.length > 80
    ) {
      window.sessionStorage.removeItem(storageKey(issueId));
      return null;
    }
    return { sessionId: value.sessionId, capability: value.capability };
  } catch {
    window.sessionStorage.removeItem(storageKey(issueId));
    return null;
  }
}

function saveCredential(issueId: string, credential: SessionCredential): void {
  window.sessionStorage.setItem(
    storageKey(issueId),
    JSON.stringify(credential),
  );
}

function clearCredential(issueId: string): void {
  window.sessionStorage.removeItem(storageKey(issueId));
}

function errorMessage(error: unknown): string {
  if (!(error instanceof HttpError))
    return "대화 상태를 불러오지 못했습니다. 잠시 후 다시 확인해 주세요.";
  if (error.code === "message_too_large")
    return "메시지는 1,000자 이내로 입력해 주세요.";
  if (error.code === "turn_in_progress")
    return "이전 응답이 끝난 뒤 다음 메시지를 보낼 수 있습니다.";
  if (error.code === "session_limit_reached")
    return "이 세션에서 사용할 수 있는 대화 횟수를 모두 사용했습니다.";
  if (error.code === "session_stale")
    return "이슈 데이터가 갱신되어 새 대화를 시작해야 합니다.";
  if (error.code === "rate_limited")
    return "잠시 동안 요청이 많았습니다. 조금 뒤 다시 확인해 주세요.";
  if (error.status === 503)
    return "현재 응답을 준비할 수 없습니다. 기존 대화 내용은 그대로 유지됩니다.";
  return "요청을 처리하지 못했습니다. 기존 대화 내용은 그대로 유지됩니다.";
}

function premiseLabel(value: ScenarioPremiseClass): string {
  if (value === "confirmed_fact") return "현재 확인된 정보";
  if (value === "stored_observation") return "저장된 관측";
  if (value === "user_assumption") return "사용자가 제시한 가정";
  if (value === "model_scenario") return "조건부 시나리오";
  return "추가 확인이 필요한 정보";
}

function RestrictedBlocks({ blocks }: { blocks: ScenarioContentBlock[] }) {
  return (
    <div className="space-y-3 text-sm leading-7 text-ink">
      {blocks.map((block) => {
        if (block.block_type === "paragraph") {
          return (
            <p key={block.sequence} className="whitespace-pre-line">
              {block.text}
            </p>
          );
        }
        const List = block.ordered ? "ol" : "ul";
        return (
          <List
            key={block.sequence}
            className={`${block.ordered ? "list-decimal" : "list-disc"} space-y-1 pl-5`}
          >
            {block.items.map((item, index) => (
              <li key={`${block.sequence}-${index}`}>{item}</li>
            ))}
          </List>
        );
      })}
    </div>
  );
}

function TurnCard({ turn }: { turn: ScenarioTurn }) {
  const assistantBlocks =
    turn.role === "assistant" ? parseScenarioMarkdown(turn.content) : null;
  const isAssistant = turn.role === "assistant";
  return (
    <article
      className={[
        "max-w-[92%] rounded-xl border px-4 py-3 sm:max-w-[78%]",
        isAssistant
          ? "mr-auto border-line bg-card"
          : "ml-auto border-comparison/25 bg-comparison-soft",
      ].join(" ")}
    >
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <span
          className={`text-[11px] font-bold ${isAssistant ? "text-accent" : "text-comparison"}`}
        >
          {isAssistant ? "조건부 시나리오" : "사용자가 제시한 가정"}
        </span>
        <time className="text-[11px] text-ink-faint" dateTime={turn.created_at}>
          {formatDataTimestamp(turn.created_at)}
        </time>
      </div>
      {isAssistant && assistantBlocks ? (
        <RestrictedBlocks blocks={assistantBlocks} />
      ) : (
        <p className="whitespace-pre-wrap break-words text-sm leading-7 text-ink">
          {turn.content}
        </p>
      )}
    </article>
  );
}

function PendingResponse({ blocks }: { blocks: ScenarioContentBlock[] }) {
  return (
    <article className="mr-auto max-w-[92%] rounded-xl border border-line bg-card px-4 py-3 sm:max-w-[78%]">
      <span className="inline-flex items-center gap-2 text-[11px] font-bold text-accent">
        <LoadingSpinner className="h-3.5 w-3.5" />
        조건부 시나리오 · 작성 중
      </span>
      {blocks.length ? (
        <div className="mt-2">
          <RestrictedBlocks blocks={blocks} />
        </div>
      ) : (
        <p className="mt-2 text-sm leading-6 text-ink-soft">
          저장된 정보와 가정을 구분해 응답을 준비하고 있습니다.
        </p>
      )}
    </article>
  );
}

function PendingTurnSubmission() {
  return (
    <div className="mx-auto flex max-w-xl items-center justify-center gap-2 py-8 text-accent">
      <LoadingSpinner />
      <p className="text-sm font-semibold text-ink-soft">
        질문을 보내는 중입니다.
      </p>
    </div>
  );
}

/** Capability-scoped, ephemeral scenario conversation with restricted rendering. */
export function ScenarioConversation({ issue }: { issue: Issue }) {
  const [viewState, setViewState] = useState<ViewState>("loading");
  const [credential, setCredential] = useState<SessionCredential | null>(null);
  const [session, setSession] = useState<ScenarioSession | null>(null);
  const [message, setMessage] = useState("");
  const [pendingTurn, setPendingTurn] = useState<ScenarioTurnCreated | null>(
    null,
  );
  const [pendingBlocks, setPendingBlocks] = useState<ScenarioContentBlock[]>(
    [],
  );
  const [failedTurnId, setFailedTurnId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [submittingTurn, setSubmittingTurn] = useState(false);
  const submittingTurnRef = useRef(false);
  const streamCleanup = useRef<() => void>(() => undefined);
  const pollTimer = useRef<number | null>(null);
  const watchVersion = useRef(0);
  const transcriptEnd = useRef<HTMLDivElement | null>(null);

  const stopWatching = useCallback(() => {
    watchVersion.current += 1;
    streamCleanup.current();
    streamCleanup.current = () => undefined;
    if (pollTimer.current !== null) window.clearTimeout(pollTimer.current);
    pollTimer.current = null;
  }, []);

  const refreshSession = useCallback(
    async (activeCredential: SessionCredential, signal?: AbortSignal) => {
      const loaded = await loadScenarioSession(
        issue.id,
        activeCredential.sessionId,
        activeCredential.capability,
        signal,
      );
      setSession(loaded);
      setViewState("ready");
      return loaded;
    },
    [issue.id],
  );

  const finishTurn = useCallback(
    async (
      activeCredential: SessionCredential,
      failedTurn: string | null = null,
    ) => {
      stopWatching();
      if (failedTurn) setFailedTurnId(failedTurn);
      setPendingBlocks([]);
      setPendingTurn(null);
      try {
        await refreshSession(activeCredential);
      } catch (error) {
        if (error instanceof HttpError && error.status === 404) {
          clearCredential(issue.id);
          setCredential(null);
          setSession(null);
          setViewState("expired");
        } else {
          setActionError(errorMessage(error));
        }
      }
    },
    [issue.id, refreshSession, stopWatching],
  );

  const watchTurn = useCallback(
    (activeCredential: SessionCredential, turn: ScenarioTurnCreated) => {
      stopWatching();
      const version = watchVersion.current;
      setPendingTurn(turn);
      setPendingBlocks([]);

      const poll = async () => {
        if (version !== watchVersion.current) return;
        try {
          const status = await loadScenarioTurnStatus(
            issue.id,
            activeCredential.sessionId,
            turn.turn_id,
            activeCredential.capability,
          );
          if (version !== watchVersion.current) return;
          if (status.state === "succeeded")
            return void finishTurn(activeCredential);
          if (status.state === "failed") {
            setActionError(
              "이번 응답을 표시할 수 없습니다. 이전 대화 내용은 그대로 유지됩니다.",
            );
            return void finishTurn(activeCredential, turn.turn_id);
          }
          pollTimer.current = window.setTimeout(poll, 1500);
        } catch (error) {
          if (version !== watchVersion.current) return;
          if (error instanceof HttpError && error.status === 404) {
            return void finishTurn(activeCredential, turn.turn_id);
          }
          setActionError(errorMessage(error));
          pollTimer.current = window.setTimeout(poll, 3000);
        }
      };

      streamCleanup.current = subscribeToScenarioStream(
        turn.stream_path,
        activeCredential.capability,
        {
          onSnapshot: () => undefined,
          onBlock: (block) => {
            if (version !== watchVersion.current) return;
            setPendingBlocks((current) => {
              if (current.some((item) => item.sequence === block.sequence))
                return current;
              if (block.sequence !== current.length) return current;
              return [...current, block];
            });
          },
          onComplete: () => {
            if (version === watchVersion.current)
              void finishTurn(activeCredential);
          },
          onFailed: () => {
            if (version === watchVersion.current) {
              setActionError(
                "이번 응답을 표시할 수 없습니다. 이전 대화 내용은 그대로 유지됩니다.",
              );
              void finishTurn(activeCredential, turn.turn_id);
            }
          },
          onTransportError: () => {
            if (version === watchVersion.current) void poll();
          },
        },
      );
    },
    [finishTurn, issue.id, stopWatching],
  );

  useEffect(() => {
    const controller = new AbortController();
    stopWatching();
    setActionError(null);
    setSession(null);
    setPendingTurn(null);
    setPendingBlocks([]);
    setFailedTurnId(null);
    submittingTurnRef.current = false;
    setSubmittingTurn(false);
    const stored = readCredential(issue.id);
    if (!stored) {
      setCredential(null);
      setViewState("idle");
      return () => controller.abort();
    }
    setCredential(stored);
    setViewState("loading");
    refreshSession(stored, controller.signal)
      .then((loaded) => {
        const trailing = loaded.turns[loaded.turns.length - 1];
        if (!trailing || trailing.role !== "user") return;
        return loadScenarioTurnStatus(
          issue.id,
          stored.sessionId,
          trailing.turn_id,
          stored.capability,
          controller.signal,
        ).then((status) => {
          if (status.state === "failed") {
            setFailedTurnId(trailing.turn_id);
            setActionError(
              "이번 응답을 표시할 수 없습니다. 이전 대화 내용은 그대로 유지됩니다.",
            );
          } else if (status.state === "queued" || status.state === "running") {
            watchTurn(stored, {
              turn_id: trailing.turn_id,
              sequence: trailing.sequence,
              status: "queued",
              created: false,
              requested_at: status.requested_at,
              stream_path: `/api/issues/${encodeURIComponent(issue.id)}/scenario-sessions/${encodeURIComponent(stored.sessionId)}/turns/${encodeURIComponent(trailing.turn_id)}/stream`,
            });
          }
        });
      })
      .catch((error) => {
        if (error instanceof DOMException && error.name === "AbortError")
          return;
        if (error instanceof HttpError && error.status === 404) {
          clearCredential(issue.id);
          setCredential(null);
          setViewState("expired");
        } else {
          setViewState("error");
          setActionError(errorMessage(error));
        }
      });
    return () => {
      controller.abort();
      stopWatching();
    };
  }, [issue.id, refreshSession, stopWatching, watchTurn]);

  useEffect(() => {
    transcriptEnd.current?.scrollIntoView({
      behavior: "smooth",
      block: "nearest",
    });
  }, [pendingBlocks, pendingTurn, session?.turns.length]);

  const visibleTurns = useMemo(
    () => session?.turns.filter((turn) => turn.turn_id !== failedTurnId) ?? [],
    [failedTurnId, session?.turns],
  );

  const startSession = async () => {
    setViewState("loading");
    setActionError(null);
    try {
      const created = await createScenarioSession(issue.id);
      const nextCredential = {
        sessionId: created.session_id,
        capability: created.session_capability,
      };
      saveCredential(issue.id, nextCredential);
      setCredential(nextCredential);
      await refreshSession(nextCredential);
    } catch (error) {
      if (error instanceof HttpError && error.status === 404)
        setViewState("unavailable");
      else setViewState("error");
      setActionError(errorMessage(error));
    }
  };

  const submitTurn = async () => {
    const normalized = message.trim();
    if (
      !credential ||
      !session ||
      !normalized ||
      pendingTurn ||
      submittingTurnRef.current
    )
      return;
    submittingTurnRef.current = true;
    setSubmittingTurn(true);
    setActionError(null);
    try {
      const created = await createScenarioTurn(
        issue.id,
        credential.sessionId,
        credential.capability,
        normalized,
        window.crypto.randomUUID(),
      );
      setMessage("");
      setFailedTurnId(null);
      setSession({
        ...session,
        remaining_turns: Math.max(
          0,
          session.remaining_turns - (created.created ? 1 : 0),
        ),
        turns: created.created
          ? [
              ...session.turns,
              {
                turn_id: created.turn_id,
                sequence: created.sequence,
                role: "user",
                content: normalized,
                created_at: created.requested_at,
              },
            ]
          : session.turns,
      });
      watchTurn(credential, created);
    } catch (error) {
      setActionError(errorMessage(error));
      if (error instanceof HttpError && error.code === "session_stale") {
        clearCredential(issue.id);
        setCredential(null);
        setSession(null);
        setViewState("expired");
      }
    } finally {
      submittingTurnRef.current = false;
      setSubmittingTurn(false);
    }
  };

  const removeSession = async () => {
    if (!credential) return;
    setDeleting(true);
    setActionError(null);
    try {
      await deleteScenarioSession(
        issue.id,
        credential.sessionId,
        credential.capability,
      );
      stopWatching();
      clearCredential(issue.id);
      setCredential(null);
      setSession(null);
      setViewState("idle");
    } catch (error) {
      setActionError(errorMessage(error));
    } finally {
      setDeleting(false);
    }
  };

  if (viewState === "loading") {
    return (
      <section
        className="mt-6 flex items-center justify-center gap-2 rounded-xl border border-line bg-card px-4 py-8 text-center text-accent"
        role="status"
        aria-live="polite"
      >
        <LoadingSpinner />
        <p className="text-sm font-semibold text-ink-soft">
          시나리오 대화 상태를 불러오는 중입니다.
        </p>
      </section>
    );
  }

  if (viewState !== "ready" || !session || !credential) {
    return (
      <section className="mt-6 rounded-xl border border-line bg-card px-5 py-6">
        <span className="text-xs font-bold text-accent">시나리오 대화</span>
        <h2 className="mt-2 text-xl font-bold text-ink">
          {viewState === "expired"
            ? "새 대화가 필요합니다"
            : "조건을 나누어 살펴보기"}
        </h2>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-ink-soft">
          {NOTICE}
        </p>
        {viewState === "unavailable" ? (
          <p className="mt-4 rounded-lg bg-line-soft px-4 py-3 text-sm leading-6 text-ink-soft">
            현재 이 환경에서는 시나리오 대화를 사용할 수 없습니다. 기존 이슈
            정보와 브리핑은 계속 확인할 수 있습니다.
          </p>
        ) : (
          <button
            type="button"
            onClick={() => void startSession()}
            className="mt-5 inline-flex min-h-11 items-center rounded-full bg-accent px-5 text-sm font-bold text-card"
          >
            {viewState === "expired"
              ? "새 대화 시작하기"
              : "시나리오 대화 시작하기"}
          </button>
        )}
        {actionError && viewState === "error" ? (
          <p className="mt-3 text-sm leading-6 text-ink-soft" role="alert">
            {actionError}
          </p>
        ) : null}
      </section>
    );
  }

  return (
    <section
      className="mt-6 overflow-hidden rounded-xl border border-line bg-card"
      aria-labelledby="scenario-title"
    >
      <header className="border-b border-line bg-accent-soft px-4 py-4 sm:px-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <span className="text-xs font-bold text-accent">시나리오 대화</span>
            <h2 id="scenario-title" className="mt-1 text-lg font-bold text-ink">
              조건을 나누어 살펴보기
            </h2>
          </div>
          <button
            type="button"
            disabled={deleting}
            onClick={() => void removeSession()}
            className="inline-flex min-h-11 items-center rounded-full border border-line bg-card px-4 text-xs font-bold text-ink-soft disabled:opacity-50"
          >
            대화 삭제
          </button>
        </div>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-ink-soft">
          {NOTICE}
        </p>
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <CautionBadge level={issue.cautionLevel} />
          <span className="text-xs font-semibold text-ink-faint">
            데이터 기준 시각: {formatDataTimestamp(session.data_as_of)}
          </span>
          <span className="text-xs font-semibold text-ink-faint">
            남은 대화 {session.remaining_turns}회 ·{" "}
            {formatDataTimestamp(session.expires_at)}까지
          </span>
        </div>
      </header>

      <div
        className="max-h-[620px] min-h-[280px] space-y-4 overflow-y-auto bg-paper/70 px-4 py-5 sm:px-5"
        aria-live="polite"
        aria-label="시나리오 대화 내용"
      >
        {visibleTurns.length ? (
          visibleTurns.map((turn) => (
            <TurnCard key={turn.turn_id} turn={turn} />
          ))
        ) : !submittingTurn ? (
          <div className="mx-auto max-w-xl py-8 text-center">
            <h3 className="text-sm font-bold text-ink">
              확인하고 싶은 조건을 입력해 주세요
            </h3>
            <p className="mt-2 text-sm leading-6 text-ink-soft">
              현재 정보와 사용자가 제시한 가정을 분리해 조건부 경로를
              살펴봅니다.
            </p>
          </div>
        ) : null}
        {submittingTurn ? <PendingTurnSubmission /> : null}
        {pendingTurn ? <PendingResponse blocks={pendingBlocks} /> : null}
        <div ref={transcriptEnd} />
      </div>

      {session.premises.length ? (
        <details className="border-t border-line px-4 py-3 sm:px-5">
          <summary className="min-h-11 cursor-pointer py-3 text-sm font-bold text-ink">
            대화에서 구분한 조건
          </summary>
          <div className="grid gap-2 pb-3 md:grid-cols-2">
            {session.premises.map((premise) => (
              <div
                key={premise.premise_id}
                className="rounded-lg border border-line px-3 py-3"
              >
                <span className="text-[11px] font-bold text-comparison">
                  {premiseLabel(premise.premise_class)}
                </span>
                <p className="mt-1 text-sm leading-6 text-ink-soft">
                  {premise.text}
                </p>
              </div>
            ))}
          </div>
        </details>
      ) : null}

      <div className="border-t border-line px-4 py-4 sm:px-5">
        <label
          htmlFor="scenario-message"
          className="text-sm font-bold text-ink"
        >
          조건 또는 확인할 점
        </label>
        <textarea
          id="scenario-message"
          value={message}
          maxLength={1000}
          rows={3}
          disabled={
            submittingTurn ||
            Boolean(pendingTurn) ||
            session.remaining_turns === 0
          }
          onChange={(event) => setMessage(event.target.value)}
          onKeyDown={(event) => {
            if (
              event.key === "Enter" &&
              !event.shiftKey &&
              !event.nativeEvent.isComposing
            ) {
              event.preventDefault();
              void submitTurn();
            }
          }}
          className="mt-2 w-full resize-y rounded-lg border border-line bg-paper px-3 py-3 text-sm leading-6 text-ink outline-none focus:border-accent disabled:opacity-60"
          placeholder="예: 공식 일정이 달라지는 경우 어떤 정보를 다시 확인해야 하나요?"
        />
        <div className="mt-2 flex flex-wrap items-center justify-between gap-3">
          <span className="text-xs text-ink-faint">
            {message.length}/1,000 · Enter로 보내기, Shift+Enter로 줄바꿈
          </span>
          <button
            type="button"
            disabled={
              !message.trim() ||
              submittingTurn ||
              Boolean(pendingTurn) ||
              session.remaining_turns === 0
            }
            onClick={() => void submitTurn()}
            aria-busy={submittingTurn}
            className="inline-flex min-h-11 items-center gap-2 rounded-full bg-accent px-5 text-sm font-bold text-card disabled:cursor-not-allowed disabled:opacity-45"
          >
            {submittingTurn ? (
              <>
                <LoadingSpinner />
                <span>질문을 보내는 중</span>
              </>
            ) : (
              "질문 보내기"
            )}
          </button>
        </div>
        {actionError ? (
          <p className="mt-3 text-sm leading-6 text-ink-soft" role="alert">
            {actionError}
          </p>
        ) : null}
        <p className="mt-3 text-xs leading-5 text-ink-faint">
          {session.caution_note}
        </p>
      </div>
    </section>
  );
}
