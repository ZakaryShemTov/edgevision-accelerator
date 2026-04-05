// ── Kernel ───────────────────────────────────────────────────────────────────

export type KernelName = 'sobel_x' | 'sobel_y' | 'laplacian' | 'gaussian'

export const KERNELS: { name: KernelName; label: string; shortcut: string }[] = [
  { name: 'sobel_x',   label: 'Sobel X',   shortcut: '1' },
  { name: 'sobel_y',   label: 'Sobel Y',   shortcut: '2' },
  { name: 'laplacian', label: 'Laplacian', shortcut: '3' },
  { name: 'gaussian',  label: 'Gaussian',  shortcut: '4' },
]

// ── Display mode ─────────────────────────────────────────────────────────────

export type DisplayMode = 'split' | 'board' | 'input' | 'output' | 'diff'

export const DISPLAY_MODES: { mode: DisplayMode; label: string }[] = [
  { mode: 'split',  label: 'Split'  },
  { mode: 'board',  label: 'Board'  },
  { mode: 'input',  label: 'Input'  },
  { mode: 'output', label: 'Output' },
  { mode: 'diff',   label: 'Diff'   },
]

// ── Source ───────────────────────────────────────────────────────────────────

export type SourceType = 'image' | 'video'
export type Source     = string | File   // string = filename in data/

// ── ROI ──────────────────────────────────────────────────────────────────────

export interface RoiSelection {
  x: number
  y: number
  w: number
  h: number
}

// ── Run result ───────────────────────────────────────────────────────────────

export type RunStatus = 'idle' | 'running' | 'pass' | 'fail'

export interface RunResult {
  run_id: string
  kernel_name: KernelName
  status: 'pass' | 'fail'
  total_pixels: number
  matches: number
  mismatches: number
  img_h: number
  img_w: number
  out_h: number
  out_w: number
  saturated_pct: number
  output_min: number
  output_max: number
  output_mean: number
  has_roi: boolean
  roi: [number, number, number, number] | null
}

// ── Filter result ─────────────────────────────────────────────────────────────

export interface FilterResult {
  kernel: KernelName
  input_h: number
  input_w: number
  output_h: number
  output_w: number
  output_min: number
  output_max: number
  output_mean: number
  saturated_pixels: number
  saturated_pct: number
  input_png_b64: string
  output_png_b64: string
}

// ── App state ─────────────────────────────────────────────────────────────────

export interface AppState {
  // Source selection
  source: Source
  sourceName: string
  sourceType: SourceType

  // Controls
  kernel: KernelName
  displayMode: DisplayMode

  // ROI
  roiActive: boolean
  roi: RoiSelection | null

  // Preview (software)
  filterLoading: boolean
  filterResult: FilterResult | null
  filterError: string | null

  // Validation (hardware)
  runStatus: RunStatus
  currentRun: RunResult | null
  runHistory: RunResult[]
  validateError: string | null

  // UI modes
  presentationMode: boolean
  boardViewerRunId: string | null   // run to display in Board Viewer, null = closed
}
