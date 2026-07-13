type LoadingSpinnerProps = {
  className?: string;
};

/** Neutral progress glyph for bounded loading and generation states. */
export function LoadingSpinner({ className = "" }: LoadingSpinnerProps) {
  return (
    <span
      aria-hidden="true"
      className={`inline-block h-4 w-4 shrink-0 animate-spin rounded-full border-2 border-current border-r-transparent motion-reduce:animate-none ${className}`}
    />
  );
}
