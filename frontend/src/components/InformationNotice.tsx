import { Link } from "react-router-dom";
import { SiteHeader } from "./AppShell";
import { CautionBadge } from "./CautionBadge";
import type { CautionLevel } from "../types/issue";
import { formatDataTimestamp } from "../utils/format";

type NoticeContext = "dashboard" | "detail" | "summary";

type ShortCautionNoticeProps = {
  context: NoticeContext;
  cautionLevel?: CautionLevel;
  dataAsOf?: string;
  className?: string;
  surface?: "card" | "plain";
  showMethodologyLink?: boolean;
};

type GlobalFooterProps = { className?: string };

const SHORT_NOTICE_COPY: Record<NoticeContext, string> = {
  dashboard:
    "공개 데이터에 반영된 기대값의 변화이며, 전체 대중의 판단을 대표하지 않아 " +
    "해석에 주의가 필요합니다.",
  detail:
    "표시된 값과 차트는 공개 데이터에 반영된 기대값의 관측 흐름입니다. " +
    "실제 사건에 대한 검증된 사실이나 원인 설명으로 읽지 말아야 합니다. " +
    "데이터 기준 시각과 해석 주의 상태를 함께 확인하세요.",
  summary:
    "템플릿 기반 요약은 시장 질문의 의미, 현재 데이터 흐름, 조건부 전개를 " +
    "정해진 틀 안에서 정리한 것입니다. 맥락이 불완전할 수 있으므로 독립 확인이 필요합니다.",
};

const FOOTER_COPY = [
  "Outlook Signals는 공개 데이터 기반의 정보 분석 및 이슈 관찰 서비스입니다. " +
    "금융, 법률, 정치 또는 그 밖의 전문적 조언을 제공하지 않습니다.",
  "이 지표는 Polymarket 공개 데이터에 반영된 기대값의 변화를 보여줍니다. " +
    "전체 대중의 판단을 대표하지 않으며, 데이터 활동 수준과 변동성에 따라 " +
    "해석에 주의가 필요합니다.",
];

const POLICY_SECTIONS = [
  {
    title: "무엇을 보여주는가",
    body:
      "Outlook Signals는 Polymarket 공개 데이터에 반영된 기대값의 변화, " +
      "관측 변화 폭, 기준선 통과 표시, 해석 주의 상태를 이슈 단위로 정리합니다.",
  },
  {
    title: "어떻게 읽어야 하는가",
    body:
      "화면의 수치는 Polymarket 참여자 데이터에서 관측된 흐름입니다. " +
      "전체 대중의 판단을 대표하지 않으며, 데이터가 부족하거나 변동성이 큰 경우 " +
      "해석에는 제한이 있습니다.",
  },
  {
    title: "관련 사건 후보",
    body:
      "관련 사건 후보는 수동으로 정리한 맥락 후보입니다. " +
      "관측 변화와 함께 확인할 수 있는 자료일 뿐, 변화의 원인으로 제시하지 않습니다.",
  },
  {
    title: "요약 문장",
    body:
      "이슈 요약은 이슈 개요, 현재 데이터 읽기, 외부 맥락, " +
      "변화와 함께 확인할 요인, 조건부 전개, 추가 확인 사항, " +
      "데이터 한계와 해석 주의를 정해진 문장 틀에 맞춰 " +
      "정리합니다. 자유 형식 분석이나 단정적 설명으로 제공하지 않습니다.",
  },
  {
    title: "확인 원칙",
    body:
      "중요한 판단에는 이 화면만 사용하지 말고 별도 자료를 함께 확인해야 합니다. " +
      "이 서비스는 읽기와 관찰을 위한 보조 도구로만 사용해야 합니다.",
  },
];

export function ShortCautionNotice({
  context,
  cautionLevel = "sufficient",
  dataAsOf,
  className = "",
  surface = "card",
  showMethodologyLink = false,
}: ShortCautionNoticeProps) {
  const surfaceClassName =
    surface === "card"
      ? "rounded-lg border border-line bg-card px-4 py-3"
      : "border-t border-line-soft pt-3";

  return (
    <section className={`${surfaceClassName} ${className}`}>
      <div className="flex items-start gap-3">
        <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-accent text-xs font-bold text-accent">
          i
        </div>
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <CautionBadge level={cautionLevel} />
            {dataAsOf ? (
              <span className="text-xs font-semibold text-ink-faint">
                데이터 기준 시각: {formatDataTimestamp(dataAsOf)}
              </span>
            ) : null}
          </div>
          <p className="mt-2 text-sm leading-6 text-ink-soft">
            {SHORT_NOTICE_COPY[context]}
          </p>
          {showMethodologyLink ? (
            <Link
              to="/methodology"
              className="mt-1 inline-flex min-h-11 items-center text-xs font-bold text-accent"
            >
              해석 기준 자세히 보기 →
            </Link>
          ) : null}
        </div>
      </div>
    </section>
  );
}

export function GlobalFooter({ className = "" }: GlobalFooterProps) {
  return (
    <footer
      id="information-note"
      className={`border-t border-line pt-5 text-xs leading-6 text-ink-faint ${className}`}
    >
      <p className="max-w-3xl">{FOOTER_COPY[0]}</p>
      <p className="mt-2 max-w-3xl">{FOOTER_COPY[1]}</p>
      <Link
        to="/methodology"
        className="mt-2 inline-flex min-h-11 items-center text-xs font-bold text-ink-soft transition hover:text-accent"
      >
        해석 기준 자세히 보기
      </Link>
    </footer>
  );
}

export function InformationNoticeScreen() {
  return (
    <div className="mx-auto min-h-screen w-full max-w-[1180px] px-4 py-6 sm:px-8 lg:px-10 lg:py-10">
      <SiteHeader />

      <main
        id="main-content"
        data-route-main
        tabIndex={-1}
        aria-labelledby="methodology-title"
        className="mt-8 outline-none"
      >
        <div className="flex items-start gap-3">
          <span
            aria-hidden="true"
            className="mt-1 h-16 w-1 shrink-0 rounded-full bg-accent"
          />
          <div>
            <span className="text-xs font-bold text-accent">
              정보 해석 안내
            </span>
            <h1
              id="methodology-title"
              className="mt-2 max-w-3xl text-3xl font-bold text-ink"
            >
              공개 데이터 기반 이슈 관찰을 위한 안내
            </h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-ink-soft">
              이 화면은 Outlook Signals가 보여주는 수치와 요약을 어떤 범위
              안에서 읽어야 하는지 정리합니다. 모든 데이터 화면의 짧은 안내와
              같은 정책을 따릅니다.
            </p>
          </div>
        </div>

        <ShortCautionNotice context="dashboard" className="mt-6" />

        <Link
          to="/"
          className="mt-5 inline-flex min-h-11 items-center rounded-full border border-accent bg-accent-soft px-4 text-sm font-bold text-accent transition hover:brightness-95"
        >
          ← 메인으로 돌아가기
        </Link>

        <div className="mt-8 grid gap-3 md:grid-cols-2">
          {POLICY_SECTIONS.map((section, index) => (
            <section
              key={section.title}
              className={`rounded-xl border border-line bg-card px-5 py-5 transition hover:border-accent ${index === POLICY_SECTIONS.length - 1 ? "md:col-span-2" : ""}`}
            >
              <div className="flex items-center gap-3">
                <span
                  aria-hidden="true"
                  className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-accent-soft text-xs font-extrabold text-accent"
                >
                  {index + 1}
                </span>
                <h2 className="text-base font-bold text-ink">
                  {section.title}
                </h2>
              </div>
              <p className="mt-2 max-w-3xl text-sm leading-7 text-ink-soft">
                {section.body}
              </p>
            </section>
          ))}
        </div>
      </main>

      <GlobalFooter className="mt-10" />
    </div>
  );
}
