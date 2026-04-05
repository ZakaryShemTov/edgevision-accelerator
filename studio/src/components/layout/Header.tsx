import type { KernelName, RunStatus } from '../../types'

interface HeaderProps {
  runStatus: RunStatus
  kernel: KernelName
  filterLoading: boolean
  presentationMode: boolean
  onTogglePresentation: () => void
}

const STATUS_CONFIG: Record<RunStatus, { dot: string; label: string }> = {
  idle:    { dot: 'bg-zinc-600',          label: 'IDLE'    },
  running: { dot: 'bg-warn animate-pulse', label: 'RUNNING' },
  pass:    { dot: 'bg-pass',              label: 'PASS'    },
  fail:    { dot: 'bg-fail',              label: 'FAIL'    },
}

// Minimalist "expand" / "contract" icons using unicode box-drawing
function FocusIcon({ active }: { active: boolean }) {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" className="flex-shrink-0">
      {active ? (
        // Contract — arrows pointing inward
        <>
          <path d="M5 1v4H1" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
          <path d="M9 1v4h4" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
          <path d="M5 13v-4H1" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
          <path d="M9 13v-4h4" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
        </>
      ) : (
        // Expand — arrows pointing outward
        <>
          <path d="M1 5V1h4" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
          <path d="M13 5V1H9" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
          <path d="M1 9v4h4" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
          <path d="M13 9v4H9" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
        </>
      )}
    </svg>
  )
}

export default function Header({
  runStatus, kernel, filterLoading, presentationMode, onTogglePresentation,
}: HeaderProps) {
  const { dot, label } = STATUS_CONFIG[runStatus]

  return (
    <header className="h-10 flex-shrink-0 flex items-center justify-between px-4
                       border-b border-zinc-800 bg-surface-0">
      {/* Identity */}
      <div className="flex items-center gap-3">
        <span className="text-accent font-mono text-xs font-medium tracking-widest select-none">EV</span>
        <span className="w-px h-3 bg-zinc-700" />
        <span className="text-zinc-100 text-sm font-medium tracking-wide">EdgeVision Studio</span>
        <span className="text-zinc-700 text-xs font-mono">v5</span>
      </div>

      {/* Right cluster */}
      <div className="flex items-center gap-4">
        {filterLoading && (
          <span className="text-[10px] font-mono text-zinc-600 animate-pulse">preview…</span>
        )}

        <span className="text-zinc-600 text-[11px] font-mono hidden lg:block">
          INT8 · 3×3 · no-pad · stride-1
        </span>

        <span className="text-zinc-600 text-[11px] font-mono hidden md:block">
          <span className="text-zinc-700">kernel </span>
          <span className="text-zinc-400">{kernel}</span>
        </span>

        {/* RTL status */}
        <div className="flex items-center gap-1.5">
          <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${dot}`} />
          <span className="text-[10px] font-mono text-zinc-500 tracking-wider">{label}</span>
        </div>

        {/* Divider */}
        <span className="w-px h-3 bg-zinc-800" />

        {/* Presentation mode toggle */}
        <button
          onClick={onTogglePresentation}
          title={presentationMode ? 'Exit presentation mode (P)' : 'Presentation mode (P)'}
          className={`flex items-center gap-1.5 px-2 py-1 rounded text-[10px] font-mono
                      transition-colors border
            ${presentationMode
              ? 'text-accent border-accent/30 bg-accent/10 hover:bg-accent/15'
              : 'text-zinc-500 border-zinc-800 hover:text-zinc-300 hover:border-zinc-700'
            }`}
        >
          <FocusIcon active={presentationMode} />
          <span className="hidden sm:inline">{presentationMode ? 'EXIT' : 'PRESENT'}</span>
        </button>
      </div>
    </header>
  )
}
