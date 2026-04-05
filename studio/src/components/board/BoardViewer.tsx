/**
 * BoardViewer — fullscreen overlay for consulting a validation run's board artifact.
 *
 * Opened when the user clicks "View Board" in the Run Gallery or Validation Panel.
 * Shows the V4 board.png (4-panel: Input | Python Golden | RTL Output | Diff Map)
 * at maximum legible size with prev/next navigation between runs.
 *
 * The board.png is the primary portfolio artifact of the project.
 * This viewer puts it front and center.
 */
import { useEffect, useCallback } from 'react'
import type { RunResult } from '../../types'
import { artifactUrl } from '../../api/client'

interface BoardViewerProps {
  run: RunResult
  allRuns: RunResult[]
  onClose: () => void
  onNavigate: (run: RunResult) => void
}

function formatDate(run_id: string): string {
  const m = run_id.match(/(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})/)
  if (!m) return run_id.slice(-12)
  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
  const [, yyyy, mo, dd, hh, mm] = m
  return `${months[parseInt(mo)-1]} ${dd}, ${yyyy}  ${hh}:${mm}`
}

export default function BoardViewer({ run, allRuns, onClose, onNavigate }: BoardViewerProps) {
  const idx     = allRuns.findIndex(r => r.run_id === run.run_id)
  const hasPrev = idx > 0
  const hasNext = idx < allRuns.length - 1

  const goPrev = useCallback(() => {
    if (hasPrev) onNavigate(allRuns[idx - 1])
  }, [hasPrev, idx, allRuns, onNavigate])

  const goNext = useCallback(() => {
    if (hasNext) onNavigate(allRuns[idx + 1])
  }, [hasNext, idx, allRuns, onNavigate])

  // Keyboard navigation
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape')       onClose()
      if (e.key === 'ArrowLeft')    goPrev()
      if (e.key === 'ArrowRight')   goNext()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose, goPrev, goNext])

  const boardUrl = artifactUrl(run.run_id, 'board.png')

  return (
    /* Backdrop */
    <div
      className="board-backdrop fixed inset-0 z-50 flex flex-col animate-fade-in"
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      {/* Top bar */}
      <div className="flex-shrink-0 flex items-center justify-between px-6 py-3
                      border-b border-zinc-800/60">
        <div className="flex items-center gap-4">
          <span className="text-accent font-mono text-xs tracking-widest select-none">EV</span>
          <span className="w-px h-3 bg-zinc-700" />
          <span className="text-zinc-300 text-sm font-medium">Board Viewer</span>
        </div>

        {/* Run metadata */}
        <div className="flex items-center gap-4">
          <span className="hidden md:block text-[11px] font-mono text-zinc-500">
            {formatDate(run.run_id)}
          </span>
          <span className="kernel-badge">{run.kernel_name}</span>
          <span className="text-[11px] font-mono text-zinc-500">
            {run.out_h}×{run.out_w}
          </span>
          <span className={`px-2 py-0.5 rounded text-[11px] font-mono font-medium
            ${run.status === 'pass' ? 'status-pass' : 'status-fail'}`}>
            {run.status.toUpperCase()}
          </span>
          {run.mismatches === 0 ? (
            <span className="hidden sm:block text-[11px] font-mono text-pass">
              {run.total_pixels.toLocaleString()} / {run.total_pixels.toLocaleString()} match
            </span>
          ) : (
            <span className="hidden sm:block text-[11px] font-mono text-fail">
              {run.mismatches} mismatch{run.mismatches > 1 ? 'es' : ''}
            </span>
          )}
        </div>

        <div className="flex items-center gap-3">
          {/* Navigation */}
          <div className="flex items-center gap-1">
            <button
              onClick={goPrev}
              disabled={!hasPrev}
              className="w-7 h-7 flex items-center justify-center rounded text-zinc-500
                         hover:text-zinc-200 hover:bg-zinc-800 transition-colors
                         disabled:opacity-20 disabled:cursor-not-allowed text-sm"
              title="Previous run (←)"
            >
              ←
            </button>
            <span className="text-[10px] font-mono text-zinc-700 px-1">
              {idx + 1} / {allRuns.length}
            </span>
            <button
              onClick={goNext}
              disabled={!hasNext}
              className="w-7 h-7 flex items-center justify-center rounded text-zinc-500
                         hover:text-zinc-200 hover:bg-zinc-800 transition-colors
                         disabled:opacity-20 disabled:cursor-not-allowed text-sm"
              title="Next run (→)"
            >
              →
            </button>
          </div>

          {/* Artifact links */}
          <a
            href={boardUrl}
            download
            className="h-7 px-2.5 flex items-center text-[11px] font-mono text-zinc-500
                       hover:text-zinc-200 bg-zinc-800/50 hover:bg-zinc-800 rounded
                       border border-zinc-700/50 hover:border-zinc-600 transition-colors"
            title="Download board.png"
          >
            ↓ board.png
          </a>

          {/* Close */}
          <button
            onClick={onClose}
            className="w-7 h-7 flex items-center justify-center rounded text-zinc-500
                       hover:text-zinc-200 hover:bg-zinc-800 transition-colors"
            title="Close (Esc)"
          >
            ×
          </button>
        </div>
      </div>

      {/* Board image — fills remaining height */}
      <div className="flex-1 relative overflow-hidden flex items-center justify-center p-6 animate-board-open">
        <img
          key={run.run_id}        /* re-mount on navigation for clean load */
          src={boardUrl}
          alt={`Board for ${run.run_id}`}
          className="max-w-full max-h-full object-contain rounded-sm shadow-2xl"
          style={{ imageRendering: 'pixelated' }}
        />

        {/* Side navigation hit areas */}
        {hasPrev && (
          <button
            onClick={goPrev}
            className="absolute left-2 top-1/2 -translate-y-1/2 w-10 h-20
                       flex items-center justify-center rounded text-zinc-600
                       hover:text-zinc-300 hover:bg-zinc-800/60 transition-colors text-xl"
          >
            ‹
          </button>
        )}
        {hasNext && (
          <button
            onClick={goNext}
            className="absolute right-2 top-1/2 -translate-y-1/2 w-10 h-20
                       flex items-center justify-center rounded text-zinc-600
                       hover:text-zinc-300 hover:bg-zinc-800/60 transition-colors text-xl"
          >
            ›
          </button>
        )}
      </div>

      {/* Bottom: panel labels (matches the V4 board structure) */}
      <div className="flex-shrink-0 flex items-center justify-center gap-8 py-3
                      border-t border-zinc-800/40">
        {[
          { label: 'Input',         color: 'text-zinc-500'  },
          { label: 'Python Golden', color: 'text-accent/60' },
          { label: 'RTL Output',    color: 'text-pass/60'   },
          { label: 'Diff Map',      color: 'text-zinc-500'  },
        ].map(({ label, color }) => (
          <span key={label} className={`text-[10px] font-mono tracking-wider uppercase ${color}`}>
            {label}
          </span>
        ))}
      </div>

      {/* Keyboard hint */}
      <div className="flex-shrink-0 flex items-center justify-center pb-3 gap-3">
        {[['←', 'Prev'], ['→', 'Next'], ['Esc', 'Close']].map(([k, label]) => (
          <span key={k} className="flex items-center gap-1 text-[10px] font-mono text-zinc-700">
            <kbd className="kbd">{k}</kbd> {label}
          </span>
        ))}
      </div>
    </div>
  )
}
