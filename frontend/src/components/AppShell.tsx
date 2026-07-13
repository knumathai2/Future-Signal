import { useEffect } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { focusRouteHeading } from "../utils/focus";
import { formatDataTimestamp } from "../utils/format";

type SiteHeaderProps = {
  dataAsOf?: string;
  onRefresh?: () => void;
  isRefreshing?: boolean;
};

export function BrandMark() {
  return (
    <span className="inline-flex items-center gap-2">
      <svg aria-hidden="true" viewBox="0 0 20 20" className="h-5 w-5">
        <rect x="2" y="10" width="4" height="8" fill="#b84416" />
        <rect x="8" y="5" width="4" height="13" fill="#241c18" />
        <rect x="14" y="1" width="4" height="17" fill="#b84416" />
      </svg>
      <span className="text-base font-extrabold sm:text-xl">
        Outlook AI Signals
      </span>
    </span>
  );
}

function navigationClass(isActive: boolean): string {
  return [
    "inline-flex min-h-11 items-center rounded-full px-2 text-[11px] font-bold transition sm:px-3 sm:text-xs",
    isActive
      ? "bg-line-soft text-ink"
      : "text-ink-soft hover:bg-line-soft hover:text-accent",
  ].join(" ");
}

/** Shared, compact navigation for every browser route. */
export function SiteHeader({
  dataAsOf,
  onRefresh,
  isRefreshing = false,
}: SiteHeaderProps) {
  const navigation = (
    <>
      <NavLink
        to="/"
        end
        className={({ isActive }) => navigationClass(isActive)}
      >
        메인
      </NavLink>
      <NavLink
        to="/issues"
        className={({ isActive }) => navigationClass(isActive)}
      >
        전체 이슈
      </NavLink>
      <NavLink
        to="/methodology"
        className={({ isActive }) => navigationClass(isActive)}
      >
        해석 기준
      </NavLink>
    </>
  );

  return (
    <header className="border-b border-line pb-3 sm:pb-4">
      <div className="flex flex-nowrap items-center justify-between gap-3">
        <Link to="/" className="inline-flex min-h-11 items-center text-ink">
          <BrandMark />
        </Link>
        <div className="flex shrink-0 items-center gap-2">
          <nav
            aria-label="주요 메뉴"
            className="hidden items-center gap-1 md:flex"
          >
            {navigation}
          </nav>
          {onRefresh ? (
            <button
              type="button"
              onClick={onRefresh}
              disabled={isRefreshing}
              className="inline-flex min-h-11 min-w-11 shrink-0 items-center justify-center rounded-full border border-line px-0 font-bold text-ink-soft transition hover:border-accent hover:text-accent disabled:cursor-wait disabled:opacity-60 md:min-w-0 md:px-4 md:text-xs"
              aria-label={isRefreshing ? "데이터 갱신 중" : "데이터 새로고침"}
            >
              <svg
                aria-hidden="true"
                viewBox="0 0 24 24"
                className={`h-5 w-5 ${isRefreshing ? "animate-spin" : ""}`}
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M20 7v5h-5" />
                <path d="M4 17v-5h5" />
                <path d="M6.1 8.5A7 7 0 0 1 18.7 7L20 12" />
                <path d="M17.9 15.5A7 7 0 0 1 5.3 17L4 12" />
              </svg>
              <span className="ml-2 hidden md:inline">
                {isRefreshing ? "데이터 갱신 중" : "데이터 새로고침"}
              </span>
            </button>
          ) : null}
        </div>
      </div>

      <nav
        aria-label="주요 메뉴"
        className="mt-2 grid grid-cols-3 items-center gap-1 md:hidden"
      >
        {navigation}
      </nav>

      {dataAsOf ? (
        <div className="mt-2 text-[11px] font-semibold text-ink-faint sm:text-xs">
          데이터 기준 시각: {formatDataTimestamp(dataAsOf)}
        </div>
      ) : null}
    </header>
  );
}

/** Move keyboard focus to the new page heading after path navigation. */
export function RouteFocus() {
  const { pathname } = useLocation();

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      focusRouteHeading();
      window.scrollTo({ top: 0, behavior: "auto" });
    });

    return () => window.cancelAnimationFrame(frame);
  }, [pathname]);

  return null;
}
