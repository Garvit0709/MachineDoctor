
type CreatorCreditProps = {
  compact?: boolean
  className?: string
}

export default function CreatorCredit({
  compact = false,
  className = '',
}: CreatorCreditProps) {
  const monogram = (
    <div
      className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-cyan-400/30 bg-gradient-to-br from-cyan-400/15 to-blue-500/10 shadow-sm shadow-cyan-500/10"
      aria-hidden="true"
    >
      <span className="text-sm font-extrabold tracking-tight text-cyan-300">
        GM
      </span>
    </div>
  )

  if (compact) {
    return (
      <div
        className={`flex justify-center ${className}`}
        title="Created by Garvit Maheshwari"
        aria-label="Created by Garvit Maheshwari"
      >
        {monogram}
      </div>
    )
  }

  return (
    <div
      className={`flex items-center gap-3 ${className}`}
    >
      {monogram}

      <div className="min-w-0">
        <p className="text-[9px] font-semibold uppercase tracking-[0.15em] text-slate-500">
          Created & Developed By
        </p>

        <p className="mt-0.5 text-xs font-semibold tracking-wide text-slate-200">
          Garvit Maheshwari
        </p>

        <p className="mt-0.5 text-[10px] text-cyan-400/80">
          MachineDoctor · AURA Research
        </p>
      </div>
    </div>
  )
}
