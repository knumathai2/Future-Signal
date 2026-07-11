type MetricTileProps = {
  label: string;
  value: string;
  primary?: boolean;
  tone?: "default" | "accent" | "comparison";
};

export function MetricTile({
  label,
  value,
  primary = false,
  tone = "default",
}: MetricTileProps) {
  const tileClassName = primary
    ? "min-w-32 rounded-lg border border-ink bg-ink px-4 py-3 text-card"
    : tone === "accent"
      ? "min-w-32 rounded-lg border border-accent bg-accent-soft px-4 py-3 text-accent"
      : tone === "comparison"
        ? "min-w-32 rounded-lg border border-comparison bg-comparison-soft px-4 py-3 text-comparison"
        : "min-w-32 rounded-lg border border-line bg-card px-4 py-3 text-ink";

  return (
    <div className={tileClassName}>
      <div
        className={
          primary || tone !== "default"
            ? "text-2xl font-extrabold"
            : "text-base font-bold"
        }
      >
        {value}
      </div>
      <div
        className={
          primary
            ? "mt-1 text-[11px] font-semibold leading-snug text-[#d8d2c4]"
            : tone === "accent"
              ? "mt-1 text-[11px] font-semibold leading-snug text-ink-soft"
              : tone === "comparison"
                ? "mt-1 text-[11px] font-semibold leading-snug text-ink-soft"
                : "mt-1 text-[11px] font-semibold leading-snug text-ink-faint"
        }
      >
        {label}
      </div>
    </div>
  );
}
