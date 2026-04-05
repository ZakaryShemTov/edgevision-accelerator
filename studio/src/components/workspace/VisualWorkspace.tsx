import type { DisplayMode, KernelName, RunResult, FilterResult, RoiSelection } from '../../types'
import { artifactUrl } from '../../api/client'
import ImagePanel from './ImagePanel'

interface VisualWorkspaceProps {
  displayMode: DisplayMode
  kernel: KernelName
  filterResult: FilterResult | null
  filterLoading: boolean
  filterError: string | null
  currentRun: RunResult | null
  roiActive: boolean
  roi: RoiSelection | null
  onRoiChange: (roi: RoiSelection | null) => void
}

function dimLabel(h: number, w: number) { return `${h}×${w}` }

function StatChip({ label, value, mono, accent }: {
  label: string; value: string; mono?: boolean; accent?: boolean
}) {
  return (
    <div className="flex items-baseline gap-1">
      <span className="text-[9px] font-mono text-zinc-700 uppercase tracking-wider">{label}</span>
      <span className={`text-[11px] ${mono ? 'font-mono' : ''} ${accent ? 'text-accent/80' : 'text-zinc-400'}`}>
        {value}
      </span>
    </div>
  )
}

// Empty workspace placeholder — shows when no filter has been run yet
function EmptyWorkspace({ kernel }: { kernel: KernelName }) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-5 select-none">
      {/* Large minimal logo mark */}
      <div className="relative">
        <div className="w-16 h-16 rounded-lg border border-zinc-800 flex items-center justify-center
                        bg-gradient-to-br from-zinc-900 to-zinc-950">
          <span className="text-zinc-700 font-mono text-2xl">⊞</span>
        </div>
        <div className="absolute -bottom-1 -right-1 w-4 h-4 rounded-sm bg-zinc-900 border border-zinc-800
                        flex items-center justify-center">
          <span className="text-accent/60 text-[8px] font-mono">∫</span>
        </div>
      </div>

      <div className="text-center space-y-1">
        <p className="text-xs font-mono text-zinc-500">No preview loaded</p>
        <p className="text-[10px] font-mono text-zinc-700">
          Select a source and click <span className="text-zinc-500">Run Filter</span>
        </p>
      </div>

      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-zinc-900 border border-zinc-800">
          <span className="w-1.5 h-1.5 rounded-full bg-accent/40" />
          <span className="text-[10px] font-mono text-zinc-600">{kernel}</span>
        </div>
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-zinc-900 border border-zinc-800">
          <span className="text-[10px] font-mono text-zinc-700">INT8 · 3×3 · stride 1</span>
        </div>
      </div>
    </div>
  )
}

export default function VisualWorkspace({
  displayMode, kernel,
  filterResult, filterLoading, filterError,
  currentRun,
  roiActive, roi, onRoiChange,
}: VisualWorkspaceProps) {

  const inputSrc    = filterResult ? `data:image/png;base64,${filterResult.input_png_b64}` : undefined
  const outputSrc   = filterResult ? `data:image/png;base64,${filterResult.output_png_b64}` : undefined
  const rtlBoardSrc = currentRun ? artifactUrl(currentRun.run_id, 'board.png')    : undefined
  const diffSrc     = currentRun ? artifactUrl(currentRun.run_id, 'diff_map.png') : undefined

  const inH  = filterResult?.input_h  ?? currentRun?.img_h
  const inW  = filterResult?.input_w  ?? currentRun?.img_w
  const outH = filterResult?.output_h ?? currentRun?.out_h
  const outW = filterResult?.output_w ?? currentRun?.out_w

  const inDim  = inH  != null && inW  != null ? dimLabel(inH, inW)   : undefined
  const outDim = outH != null && outW != null ? dimLabel(outH, outW) : undefined

  const roiProps = { roiActive, roi, onRoiChange, naturalWidth: inW, naturalHeight: inH }

  const hasContent = !!(filterResult || currentRun)

  return (
    <main className="flex-1 bg-surface-0 flex flex-col overflow-hidden min-w-0">
      {/* Top bar */}
      <div className="flex-shrink-0 flex items-center justify-between px-4 py-2
                      border-b border-zinc-800/60 bg-surface-0">
        <div className="flex items-center gap-3 min-w-0">
          <span className="section-label flex-shrink-0">{displayMode}</span>
          {roiActive && (
            <span className="text-[10px] font-mono text-warn px-1.5 py-0.5 rounded
                             bg-warn/10 border border-warn/20 flex-shrink-0">
              drag to select ROI
            </span>
          )}
          {filterLoading && (
            <span className="text-[10px] font-mono text-zinc-500 animate-pulse flex-shrink-0">
              {hasContent ? 'recomputing…' : 'loading…'}
            </span>
          )}
          {filterError && (
            <span className="text-[10px] font-mono text-fail truncate">{filterError}</span>
          )}
        </div>
        <span className="text-[10px] font-mono text-zinc-700 flex-shrink-0 ml-3">{kernel}</span>
      </div>

      {/* Canvas */}
      <div className="flex-1 overflow-hidden relative">
        {/* Loading shimmer overlay — visible on top of existing content when recomputing */}
        {filterLoading && hasContent && (
          <div className="absolute inset-0 z-10 pointer-events-none
                          bg-gradient-to-r from-transparent via-zinc-800/10 to-transparent
                          animate-pulse" />
        )}

        {/* Centered loading indicator — shown when there's no existing content to show */}
        {filterLoading && !hasContent && (
          <div className="absolute inset-0 z-10 flex items-center justify-center">
            <div className="flex flex-col items-center gap-3">
              <div className="flex gap-1.5">
                {[0, 1, 2, 3].map(i => (
                  <span
                    key={i}
                    className="w-1.5 h-1.5 rounded-full bg-accent/50"
                    style={{ animation: `pulse 1s ease-in-out ${i * 0.15}s infinite` }}
                  />
                ))}
              </div>
              <p className="text-[11px] font-mono text-zinc-600">computing preview…</p>
            </div>
          </div>
        )}

        {!hasContent && !filterLoading ? (
          <EmptyWorkspace kernel={kernel} />
        ) : (
          <div className="w-full h-full p-4">
            {displayMode === 'split' && (
              <div className="w-full h-full grid gap-3" style={{ gridTemplateColumns: '1fr 1fr' }}>
                <ImagePanel label="Input"         variant="input"  sublabel={inDim}  imageSrc={inputSrc}  {...roiProps} />
                <ImagePanel label="Python Golden" variant="output" sublabel={outDim} imageSrc={outputSrc} />
              </div>
            )}

            {displayMode === 'board' && (
              <div className="w-full h-full grid gap-2" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
                <ImagePanel label="Input"         variant="input"  sublabel={inDim}  imageSrc={inputSrc}   {...roiProps} />
                <ImagePanel label="Python Golden" variant="output" sublabel={outDim} imageSrc={outputSrc} />
                <ImagePanel label="RTL Board"     variant="rtl"    sublabel={outDim} imageSrc={rtlBoardSrc} />
                <ImagePanel label="Diff Map"      variant="diff"   sublabel={outDim} imageSrc={diffSrc} />
              </div>
            )}

            {displayMode === 'input' && (
              <div className="w-full h-full flex items-center justify-center">
                <div className="h-full max-w-xl w-full">
                  <ImagePanel label="Input" variant="input" sublabel={inDim} imageSrc={inputSrc} className="h-full" {...roiProps} />
                </div>
              </div>
            )}

            {displayMode === 'output' && (
              <div className="w-full h-full flex items-center justify-center">
                <div className="h-full max-w-xl w-full">
                  <ImagePanel label="Python Golden" variant="output" sublabel={outDim} imageSrc={outputSrc} className="h-full" />
                </div>
              </div>
            )}

            {displayMode === 'diff' && (
              currentRun ? (
                <div className="w-full h-full flex items-center justify-center">
                  <div className="h-full max-w-xl w-full">
                    <ImagePanel label="Diff Map" variant="diff" sublabel={outDim} imageSrc={diffSrc} className="h-full" />
                  </div>
                </div>
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <p className="text-xs font-mono text-zinc-700">
                    Run Validate RTL to produce a diff.
                  </p>
                </div>
              )
            )}
          </div>
        )}
      </div>

      {/* Stats bar */}
      <div className="flex-shrink-0 border-t border-zinc-800/50 px-4 py-2
                      flex items-center gap-5 flex-wrap min-h-[34px]">
        {filterResult ? (
          <>
            <StatChip label="in"        value={`${filterResult.input_h}×${filterResult.input_w}`} />
            <StatChip label="out"       value={`${filterResult.output_h}×${filterResult.output_w}`} />
            <StatChip label="min"       value={String(filterResult.output_min)}  mono />
            <StatChip label="max"       value={String(filterResult.output_max)}  mono />
            <StatChip label="mean"      value={filterResult.output_mean.toFixed(1)} mono />
            <StatChip label="sat"       value={`${filterResult.saturated_pct.toFixed(1)}%`} />
            <span className="ml-auto text-[9px] font-mono text-zinc-700 uppercase tracking-wider">
              software preview
            </span>
          </>
        ) : currentRun ? (
          <>
            <StatChip label="pixels"    value={currentRun.total_pixels.toLocaleString()} />
            <StatChip label="min"       value={String(currentRun.output_min)}  mono />
            <StatChip label="max"       value={String(currentRun.output_max)}  mono />
            <StatChip label="mean"      value={currentRun.output_mean.toFixed(1)} mono />
            <StatChip label="sat"       value={`${currentRun.saturated_pct.toFixed(1)}%`} />
            <span className="ml-auto text-[9px] font-mono text-pass/60 uppercase tracking-wider">
              rtl verified
            </span>
          </>
        ) : null}
        {roi && (
          <StatChip label="roi" value={`${roi.w}×${roi.h}`} accent />
        )}
      </div>
    </main>
  )
}
