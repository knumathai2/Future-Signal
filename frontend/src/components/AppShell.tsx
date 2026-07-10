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
        <rect x="2" y="10" width="4" height="8" fill="oklch(52% 0.13 45)" />
        <rect x="8" y="5" width="4" height="13" fill="oklch(22% 0.02 55)" />
        <rect x="14" y="1" width="4" height="17" fill="oklch(52% 0.13 45)" />
      </svg>
      <span className="text-base font-extrabold sm:text-xl">
        Outlook Signals
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
  return (
    <header className="border-b border-line pb-3 sm:pb-4">
      <div className="flex flex-nowrap items-center justify-between gap-1 sm:gap-3">
        <Link to="/" className="inline-flex min-h-11 items-center text-ink">
          <BrandMark />
        </Link>
        <nav aria-label="주요 메뉴" className="flex items-center gap-1">
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
        </nav>
      </div>

      {dataAsOf || onRefresh ? (
        <div className="mt-2 flex flex-wrap items-center justify-between gap-2 text-xs">
          {dataAsOf ? (
            <span className="font-semibold text-ink-faint">
              데이터 기준 시각: {formatDataTimestamp(dataAsOf)}
            </span>
          ) : (
            <span />
          )}
          {onRefresh ? (
            <button
              type="button"
              onClick={onRefresh}
              disabled={isRefreshing}
              className="inline-flex min-h-11 items-center rounded-full border border-line px-4 font-bold text-ink-soft transition hover:border-accent hover:text-accent disabled:cursor-wait disabled:opacity-60"
            >
              <span className="sm:hidden">
                {isRefreshing ? "갱신 중" : "새로고침"}
              </span>
              <span className="hidden sm:inline">
                {isRefreshing ? "데이터 갱신 중" : "데이터 새로고침"}
              </span>
            </button>
          ) : null}
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
