/** Focus the current route heading without moving the restored scroll position. */
export function focusRouteHeading() {
  const heading = document.querySelector<HTMLElement>(
    "main[data-route-main] h1",
  );
  if (!heading) {
    return;
  }

  heading.tabIndex = -1;
  heading.focus({ preventScroll: true });
}
