import { useEffect, useCallback } from 'react'
import type { RunResult } from '../../types'
import { fetchRuns, artifactUrl } from '../../api/client'

interface RunGalleryProps {
  runs: RunResult[]
  currentRunId: string | null
  onSelectRun: (run: RunResult) => void
  onOpenBoard: (run: RunResult) => void
  onRunsLoaded?: (runs: RunResult[]) => void
}

function formatDate(run_id: string): string {
  const m = run_id.match(/(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})/)
  if (!m) return run_id.slice(-10)
  const [, , mo, dd, hh, mm] = m
  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
  return `${months[parseInt(mo)-1]} ${dd}  ${hh}:${mm}`
}

// ── Empty state ───────────────────────────────────────────────────────────────

function EmptyGallery() {
  return (
    <div className="flex flex-col items-center justify-center h-full py-10 px-6 gap-3">
      <div className="w-10 h-10 rounded border border-zinc-800 flex items-center justify-center opacity-40">
        <span className="text-zinc-600 font-mono text-lg">⊡</span>
      </div>
      <div className="text-center">
        <p className="text-[11px] font-mono text-zinc-600">No validation runs yet.</p>
        <p className="text-[10px] font-mono text-zinc-700 mt-1">
          Click Validate RTL to start.
        </p>
      </div>
    </div>
  )
}

// ── Run card ──────────────────────────────────────────────────────────────────

function RunCard({
  run, isActive, onSelect, onOpenBoard,
}: {
  run: RunResult
  isActive: boolean
  onSelect: () => void
  onOpenBoard: () => void
}) {
  const thumbUrl = artifactUrl(run.run_id, 'board.png')

  return (
    <div
      onClick={onSelect}
      className={`group relative cursor-pointer rounded overflow-hidden border transition-all duration-150
        ${isActive
          ? 'border-zinc-600 bg-zinc-800/80'
          : 'border-zinc-800 hover:border-zinc-700 bg-transparent hover:bg-zinc-900/60'
        }`}
    >
      {/* Thumbnail — shows leftmost panel of board.png (the input image) */}
      <div className="relative overflow-hidden bg-zinc-900 h-10">
        <img
          src={thumbUrl}
          alt=""
          className="w-full h-full object-cover object-left-top opacity-70 group-hover:opacity-90 transition-opacity"
          loading="lazy"
          onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
        />
        {/* Status stripe on left edge */}
        <div className={`absolute left-0 top-0 bottom-0 w-0.5 ${
          run.status === 'pass' ? 'bg-pass' : 'bg-fail'
        }`} />

        {/* View Board button — appears on hover */}
        <button
          onClick={(e) => { e.stopPropagation(); onOpenBoard() }}
          className="absolute right-1.5 top-1/2 -translate-y-1/2
                     opacity-0 group-hover:opacity-100 transition-opacity
                     px-1.5 py-0.5 rounded text-[10px] font-mono
                     bg-zinc-900/90 text-zinc-300 border border-zinc-700
                     hover:bg-zinc-800 hover:text-zinc-100 hover:border-zinc-600"
        >
          Board ↗
        </button>
      </div>

      {/* Card body */}
      <div className="px-2.5 py-2">
        <div className="flex items-center justify-between mb-1">
          <span className="text-[10px] font-mono text-zinc-500 tabular-nums">
            {formatDate(run.run_id)}
          </span>
          <span className={`text-[9px] font-mono font-semibold tracking-widest px-1.5 py-0.5 rounded
            ${run.status === 'pass'
              ? 'text-pass bg-pass/10'
              : 'text-fail bg-fail/10'
            }`}>
            {run.status.toUpperCase()}
          </span>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <span className="kernel-badge text-[9px]">{run.kernel_name}</span>
          <span className="text-[10px] font-mono text-zinc-600">
            {run.out_h}×{run.out_w}
          </span>
          {run.has_roi && (
            <span className="text-[9px] font-mono text-zinc-700 px-1 py-0.5
                             bg-zinc-800 rounded border border-zinc-700/50">
              ROI
            </span>
          )}
          {run.mismatches === 0 ? (
            <span className="text-[9px] font-mono text-pass/70 ml-auto">
              {(run.total_pixels / 1000).toFixed(0)}k ✓
            </span>
          ) : (
            <span className="text-[9px] font-mono text-fail/70 ml-auto">
              {run.mismatches}Δ
            </span>
          )}
        </div>
      </div>

      {/* Active indicator */}
      {isActive && (
        <div className="absolute bottom-0 left-0 right-0 h-px bg-accent/40" />
      )}
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

export default function RunGallery({
  runs, currentRunId, onSelectRun, onOpenBoard, onRunsLoaded,
}: RunGalleryProps) {
  const refresh = useCallback(() => {
    fetchRuns()
      .then(fresh => onRunsLoaded?.(fresh))
      .catch(() => { /* backend offline */ })
  }, [onRunsLoaded])

  useEffect(() => {
    const id = setInterval(refresh, 10_000)
    return () => clearInterval(id)
  }, [refresh])

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex-shrink-0 flex items-center justify-between px-4 py-2.5
                      border-b border-zinc-800">
        <span className="section-label">Run Gallery</span>
        <div className="flex items-center gap-2">
          {runs.length > 0 && (
            <span className="text-[10px] font-mono text-zinc-700">
              {runs.filter(r => r.status === 'pass').length}/{runs.length} pass
            </span>
          )}
        </div>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto px-2 py-2 space-y-1.5">
        {runs.length === 0 ? (
          <EmptyGallery />
        ) : (
          runs.map(run => (
            <RunCard
              key={run.run_id}
              run={run}
              isActive={run.run_id === currentRunId}
              onSelect={() => onSelectRun(run)}
              onOpenBoard={() => onOpenBoard(run)}
            />
          ))
        )}
      </div>

      {/* Footer */}
      <div className="flex-shrink-0 border-t border-zinc-800 px-4 py-2">
        <p className="text-[10px] font-mono text-zinc-700">
          board · diff · report stored in results/runs/
        </p>
      </div>
    </div>
  )
}
