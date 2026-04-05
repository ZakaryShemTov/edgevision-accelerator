import { useState, useEffect } from 'react'
import type { RunStatus, RunResult } from '../../types'
import { artifactUrl } from '../../api/client'

interface ValidationPanelProps {
  runStatus: RunStatus
  currentRun: RunResult | null
  validateError: string | null
  onOpenBoard: (run: RunResult) => void
}

function MetaRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-baseline justify-between py-[3px]">
      <span className="text-[10px] font-mono text-zinc-600 flex-shrink-0 w-20">{label}</span>
      <span className="text-[11px] font-mono text-zinc-400 text-right">{value}</span>
    </div>
  )
}

function StatusBadge({ status }: { status: RunStatus }) {
  const cfg: Record<RunStatus, string> = {
    idle:    'status-idle',
    running: 'status-running',
    pass:    'status-pass',
    fail:    'status-fail',
  }
  const labels: Record<RunStatus, string> = {
    idle: 'IDLE', running: 'RUNNING', pass: 'PASS', fail: 'FAIL',
  }
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded
                      text-[10px] font-mono font-semibold tracking-widest ${cfg[status]}`}>
      {status === 'running' && (
        <span className="w-1 h-1 rounded-full bg-warn animate-pulse" />
      )}
      {labels[status]}
    </span>
  )
}

// ── Running state ─────────────────────────────────────────────────────────────

function RunningState() {
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    const id = setInterval(() => setElapsed(e => e + 1), 1000)
    return () => clearInterval(id)
  }, [])

  const minutes = Math.floor(elapsed / 60)
  const seconds = elapsed % 60
  const timeStr = minutes > 0
    ? `${minutes}:${String(seconds).padStart(2, '0')}`
    : `${seconds}s`
  const isSlow = elapsed >= 30

  return (
    <div className="py-6 flex flex-col items-center gap-3">
      {/* Animated dot row */}
      <div className="flex gap-1.5">
        {[0, 1, 2, 3, 4].map(i => (
          <span
            key={i}
            className="w-1 h-1 rounded-full bg-warn"
            style={{
              animation: `pulse 1.2s ease-in-out ${i * 0.15}s infinite`,
              opacity: 0.4,
            }}
          />
        ))}
      </div>

      <div className="flex items-baseline gap-2">
        <p className="text-[11px] font-mono text-zinc-500">RTL simulation running…</p>
        <span className={`text-[11px] font-mono tabular-nums ${isSlow ? 'text-warn' : 'text-zinc-600'}`}>
          {timeStr}
        </span>
      </div>

      <p className="text-[10px] font-mono text-zinc-700 text-center px-4">
        Python → hex → iverilog → compare
      </p>

      {isSlow && (
        <p className="text-[10px] font-mono text-warn/60 text-center px-4">
          Large images can take up to 60s
        </p>
      )}
    </div>
  )
}

// ── Idle state ────────────────────────────────────────────────────────────────

function IdleState() {
  return (
    <div className="py-6 text-center px-4">
      <div className="w-8 h-8 rounded border border-zinc-800 flex items-center justify-center
                      mx-auto mb-3 opacity-50">
        <span className="text-zinc-600 font-mono text-sm">⊞</span>
      </div>
      <p className="text-[11px] font-mono text-zinc-600">No validation run.</p>
      <p className="text-[10px] font-mono text-zinc-700 mt-1">
        Select a source and click<br />
        <span className="text-zinc-500">Validate RTL</span> to produce a hardware proof.
      </p>
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

export default function ValidationPanel({
  runStatus, currentRun, validateError, onOpenBoard,
}: ValidationPanelProps) {
  return (
    <div className="flex-shrink-0 border-b border-zinc-800 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-zinc-800/50">
        <span className="section-label">RTL Validation</span>
        <StatusBadge status={runStatus} />
      </div>

      {/* Error */}
      {validateError && (
        <div className="mx-3 mt-2 px-2 py-1.5 bg-fail/10 border border-fail/20 rounded">
          <p className="text-[10px] font-mono text-fail break-all leading-relaxed">{validateError}</p>
        </div>
      )}

      {/* Body */}
      <div className="px-4 py-3">
        {runStatus === 'running' && !currentRun ? (
          <RunningState />
        ) : currentRun ? (
          <>
            {/* Result headline */}
            <div className="flex items-center gap-2 mb-3">
              <div className={`flex-1 flex items-baseline justify-center py-2 rounded
                               ${currentRun.status === 'pass'
                                 ? 'bg-pass/8 border border-pass/15'
                                 : 'bg-fail/8 border border-fail/15'}`}>
                <span className={`text-lg font-mono font-semibold tabular-nums
                                  ${currentRun.status === 'pass' ? 'text-pass' : 'text-fail'}`}>
                  {currentRun.matches.toLocaleString()}
                </span>
                <span className="text-[10px] font-mono text-zinc-600 ml-1.5">
                  / {currentRun.total_pixels.toLocaleString()} px
                </span>
              </div>
            </div>

            {/* Meta grid */}
            <div className="border-t border-zinc-800/50">
              <MetaRow label="kernel"    value={<span className="text-zinc-200">{currentRun.kernel_name}</span>} />
              <MetaRow label="input"     value={`${currentRun.img_h} × ${currentRun.img_w}`} />
              <MetaRow label="output"    value={`${currentRun.out_h} × ${currentRun.out_w}`} />
              {currentRun.has_roi && (
                <MetaRow label="roi" value={currentRun.roi ? `${currentRun.roi[2]}×${currentRun.roi[3]} @ (${currentRun.roi[0]},${currentRun.roi[1]})` : '—'} />
              )}
              <MetaRow label="mismatches" value={
                currentRun.mismatches === 0
                  ? <span className="text-pass/80">0</span>
                  : <span className="text-fail">{currentRun.mismatches}</span>
              } />
              <MetaRow label="saturated" value={`${currentRun.saturated_pct.toFixed(1)}%`} />
              <MetaRow label="range"     value={`${currentRun.output_min} → ${currentRun.output_max}`} />
            </div>

            {/* Open Board — primary action */}
            <button
              onClick={() => onOpenBoard(currentRun)}
              className="mt-3 w-full py-2 text-xs font-mono rounded
                         bg-zinc-800 text-zinc-200 border border-zinc-700
                         hover:bg-zinc-700 hover:border-zinc-600 transition-colors
                         flex items-center justify-center gap-2"
            >
              <span>View Board</span>
              <span className="text-zinc-500">↗</span>
            </button>

            {/* Artifact links */}
            <div className="mt-2 flex gap-1 flex-wrap">
              {[
                { file: 'diff_map.png', label: 'diff'   },
                { file: 'report.txt',   label: 'report' },
                { file: 'report.json',  label: 'json'   },
              ].map(({ file, label }) => (
                <a
                  key={file}
                  href={artifactUrl(currentRun.run_id, file)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-2 py-1 text-[10px] font-mono text-zinc-600 rounded
                             border border-zinc-800 hover:text-zinc-300 hover:border-zinc-700
                             transition-colors"
                >
                  {label} ↗
                </a>
              ))}
            </div>
          </>
        ) : (
          <IdleState />
        )}
      </div>
    </div>
  )
}
