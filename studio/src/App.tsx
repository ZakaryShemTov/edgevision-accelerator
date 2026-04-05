import { useState, useCallback, useEffect } from 'react'
import type { AppState, KernelName, DisplayMode, RunResult, RoiSelection } from './types'
import type { MediaItem } from './api/client'
import { fetchMedia, fetchRuns, runFilter, runValidate } from './api/client'
import Header from './components/layout/Header'
import PresentationBar from './components/layout/PresentationBar'
import ControlPanel from './components/sidebar/ControlPanel'
import VisualWorkspace from './components/workspace/VisualWorkspace'
import ValidationPanel from './components/validation/ValidationPanel'
import RunGallery from './components/gallery/RunGallery'
import BoardViewer from './components/board/BoardViewer'

const DEFAULT_SOURCE = 'cameraman.png'

const INITIAL_STATE: AppState = {
  source: DEFAULT_SOURCE,
  sourceName: DEFAULT_SOURCE,
  sourceType: 'image',
  kernel: 'sobel_x',
  displayMode: 'split',
  roiActive: false,
  roi: null,
  filterLoading: false,
  filterResult: null,
  filterError: null,
  runStatus: 'idle',
  currentRun: null,
  runHistory: [],
  validateError: null,
  presentationMode: false,
  boardViewerRunId: null,
}

export default function App() {
  const [state, setState] = useState<AppState>(INITIAL_STATE)
  const [mediaList, setMediaList] = useState<MediaItem[]>([])
  const [mediaLoading, setMediaLoading] = useState(true)

  // ── Bootstrap ──────────────────────────────────────────────────────────────
  useEffect(() => {
    fetchMedia()
      .then(items => { setMediaList(items); setMediaLoading(false) })
      .catch(() => { setMediaList([{ name: DEFAULT_SOURCE, type: 'image' }]); setMediaLoading(false) })

    fetchRuns()
      .then(runs => setState(s => ({ ...s, runHistory: runs })))
      .catch(() => {})
  }, [])

  // ── Global keyboard shortcuts ──────────────────────────────────────────────
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      // Don't intercept if user is typing somewhere
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return
      if (e.key === 'p' || e.key === 'P') {
        setState(s => ({ ...s, presentationMode: !s.presentationMode }))
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  // ── Source selection ───────────────────────────────────────────────────────
  const handleSourceSelect = useCallback((item: MediaItem) => {
    setState(s => ({
      ...s,
      source: item.name, sourceName: item.name, sourceType: item.type,
      filterResult: null, filterError: null, roi: null, roiActive: false,
    }))
  }, [])

  const handleFileUpload = useCallback((file: File) => {
    if (file.type.startsWith('video/')) {
      setState(s => ({
        ...s,
        filterError: 'Video upload is not supported. Please upload an image file (PNG, JPEG, etc.).',
      }))
      return
    }
    setState(s => ({
      ...s,
      source: file, sourceName: file.name, sourceType: 'image',
      filterResult: null, filterError: null, roi: null, roiActive: false,
    }))
  }, [])

  // ── Controls ───────────────────────────────────────────────────────────────
  const setKernel = useCallback((kernel: KernelName) => {
    setState(s => ({ ...s, kernel, filterResult: null, filterError: null }))
  }, [])

  const setDisplayMode = useCallback((displayMode: DisplayMode) => {
    setState(s => ({ ...s, displayMode }))
  }, [])

  const toggleRoi = useCallback(() => {
    setState(s => ({ ...s, roiActive: !s.roiActive, roi: s.roiActive ? null : s.roi }))
  }, [])

  const setRoi = useCallback((roi: RoiSelection | null) => {
    setState(s => ({ ...s, roi }))
  }, [])

  const togglePresentation = useCallback(() => {
    setState(s => ({ ...s, presentationMode: !s.presentationMode }))
  }, [])

  // ── Filter (software) ──────────────────────────────────────────────────────
  const handleRunFilter = useCallback(async () => {
    const { source, kernel } = state
    setState(s => ({ ...s, filterLoading: true, filterError: null }))
    try {
      const result = await runFilter(source, kernel)
      setState(s => ({ ...s, filterLoading: false, filterResult: result }))
    } catch (err) {
      setState(s => ({
        ...s, filterLoading: false,
        filterError: err instanceof Error ? err.message : 'Filter failed',
      }))
    }
  }, [state.source, state.kernel])

  // ── Validate (hardware) ────────────────────────────────────────────────────
  const handleValidate = useCallback(async () => {
    const { source, kernel, roi } = state
    setState(s => ({ ...s, runStatus: 'running', validateError: null }))
    try {
      const run = await runValidate({ source, kernel, roi })
      setState(s => ({
        ...s,
        runStatus: run.status,
        currentRun: run,
        runHistory: [run, ...s.runHistory.slice(0, 19)],
      }))
    } catch (err) {
      setState(s => ({
        ...s, runStatus: 'fail',
        validateError: err instanceof Error ? err.message : 'Validation failed',
      }))
    }
  }, [state.source, state.kernel, state.roi])

  // ── Gallery & board viewer ──────────────────────────────────────────────────
  const handleSelectRun = useCallback((run: RunResult) => {
    setState(s => ({ ...s, currentRun: run, runStatus: run.status }))
  }, [])

  const handleRunsLoaded = useCallback((runs: RunResult[]) => {
    setState(s => ({ ...s, runHistory: runs }))
  }, [])

  const handleOpenBoard = useCallback((run: RunResult) => {
    setState(s => ({ ...s, boardViewerRunId: run.run_id }))
  }, [])

  const handleCloseBoard = useCallback(() => {
    setState(s => ({ ...s, boardViewerRunId: null }))
  }, [])

  const handleBoardNavigate = useCallback((run: RunResult) => {
    setState(s => ({ ...s, boardViewerRunId: run.run_id, currentRun: run, runStatus: run.status }))
  }, [])

  // Resolve boardViewer run from history
  const boardViewerRun = state.boardViewerRunId
    ? (state.runHistory.find(r => r.run_id === state.boardViewerRunId) ?? state.currentRun)
    : null

  const { presentationMode } = state

  return (
    <div className="h-screen w-screen bg-surface-0 flex flex-col overflow-hidden font-sans">
      <Header
        runStatus={state.runStatus}
        kernel={state.kernel}
        filterLoading={state.filterLoading}
        presentationMode={presentationMode}
        onTogglePresentation={togglePresentation}
      />

      {/* Main content — flex layout so sidebar widths can transition */}
      <div className="flex-1 flex overflow-hidden relative">

        {/* Left sidebar */}
        <div
          className="sidebar-panel border-r border-zinc-800 bg-surface-0"
          style={{ width: presentationMode ? 0 : 240, opacity: presentationMode ? 0 : 1 }}
        >
          <div style={{ width: 240 }}>
            <ControlPanel
              sourceType={state.sourceType}
              sourceName={state.sourceName}
              kernel={state.kernel}
              displayMode={state.displayMode}
              runStatus={state.runStatus}
              filterLoading={state.filterLoading}
              roiActive={state.roiActive}
              roi={state.roi}
              mediaList={mediaList}
              mediaLoading={mediaLoading}
              onSourceSelect={handleSourceSelect}
              onFileUpload={handleFileUpload}
              onKernelChange={setKernel}
              onDisplayModeChange={setDisplayMode}
              onToggleRoi={toggleRoi}
              onRunFilter={handleRunFilter}
              onValidate={handleValidate}
            />
          </div>
        </div>

        {/* Center: Visual Workspace — always visible, stretches to fill */}
        <VisualWorkspace
          displayMode={state.displayMode}
          kernel={state.kernel}
          filterResult={state.filterResult}
          filterLoading={state.filterLoading}
          filterError={state.filterError}
          currentRun={state.currentRun}
          roiActive={state.roiActive}
          roi={state.roi}
          onRoiChange={setRoi}
        />

        {/* Right sidebar */}
        <div
          className="sidebar-panel border-l border-zinc-800 flex flex-col bg-surface-0"
          style={{ width: presentationMode ? 0 : 288, opacity: presentationMode ? 0 : 1 }}
        >
          <div style={{ width: 288 }} className="flex flex-col h-full overflow-hidden">
            <ValidationPanel
              runStatus={state.runStatus}
              currentRun={state.currentRun}
              validateError={state.validateError}
              onOpenBoard={handleOpenBoard}
            />
            <RunGallery
              runs={state.runHistory}
              currentRunId={state.currentRun?.run_id ?? null}
              onSelectRun={handleSelectRun}
              onOpenBoard={handleOpenBoard}
              onRunsLoaded={handleRunsLoaded}
            />
          </div>
        </div>

        {/* Presentation mode floating bar */}
        {presentationMode && (
          <PresentationBar
            kernel={state.kernel}
            displayMode={state.displayMode}
            runStatus={state.runStatus}
            filterLoading={state.filterLoading}
            onKernelChange={setKernel}
            onDisplayModeChange={setDisplayMode}
            onRunFilter={handleRunFilter}
            onValidate={handleValidate}
            onExit={togglePresentation}
          />
        )}
      </div>

      {/* Board Viewer — full-window overlay */}
      {boardViewerRun && (
        <BoardViewer
          run={boardViewerRun}
          allRuns={state.runHistory}
          onClose={handleCloseBoard}
          onNavigate={handleBoardNavigate}
        />
      )}
    </div>
  )
}
