type MetricTileProps = {
  label: string;
  value: string;
  primary?: boolean;
};

export function MetricTile({ label, value, primary = false }: MetricTileProps) {
  return (
    <div
      className={
        primary
          ? "min-w-32 rounded-lg border border-ink bg-ink px-4 py-3 text-card"
          : "min-w-32 rounded-lg border border-line bg-card px-4 py-3 text-ink"
      }
    >
      <div className={primary ? "text-2xl font-bold" : "text-base font-bold"}>
        {value}
      </div>
      <div
        className={
          primary
            ? "mt-1 text-[11px] font-semibold leading-snug text-[#d8d2c4]"
            : "mt-1 text-[11px] font-semibold leading-snug text-ink-faint"
        }
      >
        {label}
      </div>
    </div>
  );
}
