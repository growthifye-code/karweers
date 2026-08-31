// "Ex-EY" credential badge — simplified EY-style mark (yellow on black), not the trademarked logo.
export default function EYBadge({ className = "" }) {
  return (
    <span
      data-testid="ex-ey-badge"
      className={`inline-flex items-center gap-2 rounded-full border border-border bg-secondary px-3 py-1.5 text-xs font-semibold text-foreground ${className}`}
    >
      <span className="text-muted-foreground">Ex</span>
      <span className="inline-grid h-6 w-9 place-items-center rounded-[5px] bg-black">
        <span className="font-display text-[15px] font-black italic leading-none text-[#FFE600]">EY</span>
      </span>
      <span className="text-muted-foreground">Advisory · Big 4</span>
    </span>
  );
}
