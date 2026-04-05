/**
 * PresentationBar — floating controls shown during Presentation Mode.
 *
 * Appears at the bottom of the screen when sidebars are hidden.
 * Provides the essential controls (kernel, display mode, actions)
 * so the demo can continue without reopening the full UI.
 */
import type { KernelName, DisplayMode, RunStatus } from '../../types'
import { KERNELS, DISPLAY_MODES } from '../../types'

interface PresentationBarProps {
  kernel: KernelName
  displayMode: DisplayMode
  runStatus: RunStatus
  filterLoading: boolean
  onKernelChange: (k: KernelName) => void
  onDisplayModeChange: (m: DisplayMode) => void
  onRunFilter: () => void
  onValidate: () => void
  onExit: () => void
}

export default function PresentationBar({
  kernel, displayMode, runStatus, filterLoading,
  onKernelChange, onDisplayModeChange, onRunFilter, onValidate, onExit,
}: PresentationBarProps) {
  const isRunning = runStatus === 'running' || filterLoading

  return (
    <div className="absolute bottom-0 left-0 right-0 z-40 flex items-center justify-center
                    pb-4 animate-slide-down pointer-events-none">
      <div className="flex items-center gap-1 px-3 py-2 rounded-lg pointer-events-auto
                      bg-zinc-900/95 border border-zinc-700/60 shadow-2xl"
           style={{ backdropFilter: 'blur(12px)' }}>

        {/* Kernel */}
        <div className="flex items-center gap-0.5">
          {KERNELS.map(k => (
            <button
              key={k.name}
              onClick={() => onKernelChange(k.name)}
              className={`px-2.5 py-1 rounded text-[10px] font-mono transition-colors
                ${kernel === k.name
                  ? 'bg-accent/15 text-accent border border-accent/30'
                  : 'text-zinc-500 hover:text-zinc-300 border border-transparent'
                }`}
            >
              {k.label}
            </button>
          ))}
        </div>

        <span className="w-px h-5 bg-zinc-700/60 mx-1" />

        {/* Display mode */}
        <div className="flex items-center gap-0.5">
          {DISPLAY_MODES.map(m => (
            <button
              key={m.mode}
              onClick={() => onDisplayModeChange(m.mode)}
              className={`px-2 py-1 rounded text-[10px] font-mono transition-colors
                ${displayMode === m.mode
                  ? 'bg-zinc-700 text-zinc-200 border border-zinc-600'
                  : 'text-zinc-600 hover:text-zinc-400 border border-transparent'
                }`}
            >
              {m.label}
            </button>
          ))}
        </div>

        <span className="w-px h-5 bg-zinc-700/60 mx-1" />

        {/* Actions */}
        <button
          onClick={onRunFilter}
          disabled={isRunning}
          className="px-3 py-1 rounded text-[10px] font-mono text-zinc-400
                     hover:text-zinc-200 bg-zinc-800 border border-zinc-700
                     hover:border-zinc-600 transition-colors disabled:opacity-40"
        >
          Filter
        </button>

        <button
          onClick={onValidate}
          disabled={isRunning}
          className={`px-3 py-1 rounded text-[10px] font-mono transition-colors disabled:opacity-40
            ${runStatus === 'running'
              ? 'text-warn bg-warn/10 border border-warn/30 cursor-not-allowed'
              : 'text-accent bg-accent/10 border border-accent/30 hover:bg-accent/20'
            }`}
        >
          {runStatus === 'running' ? 'Running…' : 'Validate ↗'}
        </button>

        <span className="w-px h-5 bg-zinc-700/60 mx-1" />

        {/* Exit */}
        <button
          onClick={onExit}
          className="px-2 py-1 rounded text-[10px] font-mono text-zinc-600
                     hover:text-zinc-300 border border-transparent hover:border-zinc-700
                     transition-colors"
          title="Exit presentation mode"
        >
          EXIT
        </button>
      </div>
    </div>
  )
}
