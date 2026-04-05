import { useRef } from 'react'
import type { KernelName, DisplayMode, RunStatus, RoiSelection } from '../../types'
import type { MediaItem } from '../../api/client'
import { KERNELS, DISPLAY_MODES } from '../../types'

interface ControlPanelProps {
  sourceType: 'image' | 'video'
  sourceName: string
  kernel: KernelName
  displayMode: DisplayMode
  runStatus: RunStatus
  filterLoading: boolean
  roiActive: boolean
  roi: RoiSelection | null
  mediaList: MediaItem[]
  mediaLoading: boolean
  onSourceSelect: (item: MediaItem) => void
  onFileUpload: (file: File) => void
  onKernelChange: (k: KernelName) => void
  onDisplayModeChange: (m: DisplayMode) => void
  onToggleRoi: () => void
  onRunFilter: () => void
  onValidate: () => void
}

function SectionLabel({ children }: { children: string }) {
  return <p className="section-label mb-2">{children}</p>
}

function Divider() {
  return <div className="border-t border-zinc-800 my-4" />
}

export default function ControlPanel({
  sourceType,
  sourceName,
  kernel,
  displayMode,
  runStatus,
  filterLoading,
  roiActive,
  roi,
  mediaList,
  mediaLoading,
  onSourceSelect,
  onFileUpload,
  onKernelChange,
  onDisplayModeChange,
  onToggleRoi,
  onRunFilter,
  onValidate,
}: ControlPanelProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const isRunning = runStatus === 'running' || filterLoading

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) onFileUpload(file)
    e.target.value = ''
  }

  return (
    <aside className="border-r border-zinc-800 bg-surface-0 flex flex-col overflow-hidden">
      <div className="flex-1 overflow-y-auto p-4">

        {/* SOURCE */}
        <section>
          <SectionLabel>Source</SectionLabel>

          {/* Media list */}
          <div className="space-y-0.5 mb-2">
            {mediaLoading ? (
              // Loading skeleton
              <>
                {[1, 2, 3].map(i => (
                  <div key={i} className="w-full flex items-center gap-2 px-2 py-1.5 rounded">
                    <div className="w-2 h-2 rounded-sm bg-zinc-800 animate-pulse flex-shrink-0" />
                    <div
                      className="h-2 rounded bg-zinc-800 animate-pulse"
                      style={{ width: `${48 + i * 14}%` }}
                    />
                  </div>
                ))}
              </>
            ) : mediaList.length > 0 ? (
              mediaList.map(item => (
                <button
                  key={item.name}
                  onClick={() => onSourceSelect(item)}
                  className={`w-full flex items-center gap-2 px-2 py-1.5 rounded text-xs
                              transition-colors
                    ${sourceName === item.name && typeof sourceName === 'string'
                      ? 'bg-zinc-800 text-zinc-200 border border-zinc-700'
                      : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-900 border border-transparent'
                    }`}
                >
                  <span className="text-zinc-600 text-[10px]">
                    {item.type === 'image' ? '▣' : '▶'}
                  </span>
                  <span className="font-mono truncate">{item.name}</span>
                  {item.type === 'video' && (
                    <span className="ml-auto text-[9px] font-mono text-zinc-700 flex-shrink-0">mp4</span>
                  )}
                </button>
              ))
            ) : (
              <div className="px-2 py-1.5 text-xs font-mono text-zinc-700">
                {sourceName}
              </div>
            )}
          </div>

          {/* Uploaded file indicator — shown when source is a custom upload not in media list */}
          {!mediaLoading && sourceType === 'image' &&
           !mediaList.some(m => m.name === sourceName) && (
            <div className="mb-2 flex items-center gap-2 px-2 py-1.5 rounded
                            bg-zinc-800/60 border border-zinc-700">
              <span className="text-zinc-500 text-[10px] flex-shrink-0">▣</span>
              <span className="text-[10px] font-mono text-zinc-300 truncate flex-1">{sourceName}</span>
              <span className="text-[9px] font-mono text-zinc-600 flex-shrink-0">upload</span>
            </div>
          )}

          {/* Video source notice */}
          {sourceType === 'video' && (
            <div className="mb-2 px-2 py-1.5 rounded bg-warn/5 border border-warn/15">
              <p className="text-[10px] font-mono text-warn/70 leading-relaxed">
                Video sources are not yet supported — select an image source or upload a PNG / JPEG.
              </p>
            </div>
          )}

          {/* Upload */}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={handleFileChange}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            className="w-full py-1.5 text-xs text-zinc-600 border border-zinc-800 border-dashed
                       rounded hover:text-zinc-400 hover:border-zinc-700 transition-colors"
          >
            + upload image
          </button>
        </section>

        <Divider />

        {/* KERNEL */}
        <section>
          <SectionLabel>Kernel</SectionLabel>
          <div className="space-y-0.5">
            {KERNELS.map(k => (
              <button
                key={k.name}
                onClick={() => onKernelChange(k.name)}
                className={`w-full flex items-center justify-between px-2 py-1.5 rounded
                            text-xs transition-all
                  ${kernel === k.name
                    ? 'bg-accent/10 text-accent border border-accent/20'
                    : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50 border border-transparent'
                  }`}
              >
                <div className="flex items-center gap-2">
                  <span className={`w-1 h-1 rounded-full ${kernel === k.name ? 'bg-accent' : 'bg-zinc-700'}`} />
                  <span className="font-mono">{k.label}</span>
                </div>
                <kbd className="kbd">{k.shortcut}</kbd>
              </button>
            ))}
          </div>
        </section>

        <Divider />

        {/* DISPLAY MODE */}
        <section>
          <SectionLabel>Display</SectionLabel>
          <div className="grid grid-cols-2 gap-1">
            {DISPLAY_MODES.map(m => (
              <button
                key={m.mode}
                onClick={() => onDisplayModeChange(m.mode)}
                className={`py-1.5 text-xs rounded font-mono transition-colors
                  ${displayMode === m.mode
                    ? 'bg-zinc-800 text-zinc-100 border border-zinc-600'
                    : 'text-zinc-500 border border-zinc-800 hover:text-zinc-300 hover:border-zinc-700'
                  }`}
              >
                {m.label}
              </button>
            ))}
          </div>
        </section>

        <Divider />

        {/* ROI */}
        <section>
          <SectionLabel>ROI</SectionLabel>
          <button
            onClick={onToggleRoi}
            className={`w-full flex items-center justify-between px-2 py-1.5 rounded
                        text-xs border transition-colors
              ${roiActive
                ? 'bg-warn/10 text-warn border-warn/30'
                : 'text-zinc-500 border-zinc-800 hover:text-zinc-300 hover:border-zinc-700'
              }`}
          >
            <span className="font-mono">{roiActive ? 'ROI active — drag to select' : 'Select region'}</span>
            <span>{roiActive ? '×' : '⊡'}</span>
          </button>

          {roi && (
            <div className="mt-1.5 px-2 py-1.5 bg-surface-1 rounded border border-zinc-800">
              <p className="text-[10px] font-mono text-zinc-500">
                x={roi.x} y={roi.y} w={roi.w} h={roi.h}
              </p>
            </div>
          )}
        </section>

        <Divider />

        {/* CONTRACT */}
        <section>
          <SectionLabel>Contract</SectionLabel>
          <div className="space-y-1 font-mono text-[11px]">
            {[
              ['pixel',  'INT8 · ±128'],
              ['weight', 'INT8 · ±128'],
              ['acc',    'INT32'],
              ['output', 'INT8 · sat'],
              ['pad',    'none'],
              ['stride', '1'],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between">
                <span className="text-zinc-600">{k}</span>
                <span className="text-zinc-400">{v}</span>
              </div>
            ))}
          </div>
        </section>
      </div>

      {/* Actions */}
      <div className="border-t border-zinc-800 p-3 space-y-1.5 flex-shrink-0">
        <button
          onClick={onRunFilter}
          disabled={isRunning}
          className="w-full py-2 text-xs font-medium rounded bg-zinc-800 text-zinc-200
                     hover:bg-zinc-700 border border-zinc-700 hover:border-zinc-600
                     transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {filterLoading ? 'Running filter…' : 'Run Filter'}
        </button>
        <button
          onClick={onValidate}
          disabled={isRunning}
          className={`w-full py-2 text-xs font-medium rounded border transition-colors
                     disabled:opacity-40 disabled:cursor-not-allowed
            ${runStatus === 'running'
              ? 'bg-warn/10 text-warn border-warn/30 cursor-not-allowed'
              : 'bg-accent/10 text-accent border-accent/30 hover:bg-accent/20 hover:border-accent/50'
            }`}
        >
          {runStatus === 'running' ? 'Running RTL sim…' : roi ? 'Validate ROI ↗' : 'Validate RTL ↗'}
        </button>
      </div>
    </aside>
  )
}
