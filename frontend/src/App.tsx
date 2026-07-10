import { useEffect, useState } from "react";
import { Link, Route, Routes } from "react-router-dom";
import { RouteFocus, SiteHeader } from "./components/AppShell";
import { Dashboard } from "./components/Dashboard";
import { InformationNoticeScreen } from "./components/InformationNotice";
import { IssueDetailRoute } from "./components/IssueDetailRoute";
import { IssueListPage } from "./components/IssueListPage";
import { fetchJson } from "./utils/api";
import type { ApiCategoriesResponse } from "./utils/format";

function NotFoundPage() {
  return (
    <div className="mx-auto min-h-screen w-full max-w-[1180px] px-4 py-4 sm:px-8 sm:py-6 lg:px-10 lg:py-8">
      <SiteHeader />
      <main
        id="main-content"
        data-route-main
        tabIndex={-1}
        aria-labelledby="not-found-title"
        className="mt-12 text-center outline-none"
      >
        <h1 id="not-found-title" className="text-2xl font-bold text-ink">
          요청한 화면을 찾을 수 없습니다
        </h1>
        <p className="mt-2 text-sm leading-6 text-ink-soft">
          주소를 다시 확인하거나 메인 화면에서 이슈를 살펴보세요.
        </p>
        <Link
          to="/"
          className="mt-5 inline-flex min-h-11 items-center rounded-full bg-ink px-5 text-sm font-bold text-card"
        >
          메인으로 이동
        </Link>
      </main>
    </div>
  );
}

export default function App() {
  const [categories, setCategories] = useState<string[]>([]);
  const [categoriesStatus, setCategoriesStatus] = useState<
    "loading" | "ready" | "error"
  >("loading");

  useEffect(() => {
    const controller = new AbortController();
    fetchJson<ApiCategoriesResponse>(
      "/api/categories",
      "Failed to load categories",
      controller.signal,
    )
      .then((data) => {
        setCategories(data.categories ?? []);
        setCategoriesStatus("ready");
      })
      .catch((error) => {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        console.error(error);
        setCategoriesStatus("error");
      });

    return () => controller.abort();
  }, []);

  return (
    <>
      <a
        href="#main-content"
        className="fixed left-4 top-4 z-50 -translate-y-24 rounded-full bg-ink px-4 py-3 text-sm font-bold text-card transition focus:translate-y-0"
      >
        본문으로 건너뛰기
      </a>
      <RouteFocus />
      <Routes>
        <Route
          path="/"
          element={
            <Dashboard
              categories={categories}
              categoriesStatus={categoriesStatus}
            />
          }
        />
        <Route
          path="/issues"
          element={<IssueListPage categories={categories} />}
        />
        <Route path="/issues/:issueId" element={<IssueDetailRoute />} />
        <Route path="/methodology" element={<InformationNoticeScreen />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </>
  );
}
