import { formatPercentagePointChange } from "../utils/format";

type DirectionalChangeProps = {
  value: number | null | undefined;
  className?: string;
};

export function DirectionalChange({
  value,
  className = "",
}: DirectionalChangeProps) {
  const isValid =
    value !== null && value !== undefined && Number.isFinite(value);
  let direction: "up" | "down" | "flat" | "unknown" = "unknown";
  if (isValid) {
    direction = value > 0 ? "up" : value < 0 ? "down" : "flat";
  }
  const symbol =
    direction === "up"
      ? "↑"
      : direction === "down"
        ? "↓"
        : direction === "flat"
          ? "→"
          : "";
  const directionClass =
    direction === "up"
      ? "text-accent"
      : direction === "down"
        ? "text-decline"
        : direction === "flat"
          ? "text-ink-soft"
          : "text-ink-faint";

  return (
    <span className={`${directionClass} ${className}`.trim()}>
      {symbol ? <span aria-hidden="true">{symbol} </span> : null}
      {formatPercentagePointChange(value)}
    </span>
  );
}
