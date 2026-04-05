/**
 * EdgeVision Studio — API client
 *
 * Typed wrappers around all backend endpoints.
 * Every function throws on non-2xx responses with a human-readable message.
 */

import type { FilterResult, RunResult, KernelName } from '../types'

// ── Types mirrored from backend Pydantic models ──────────────────────────────

export interface MediaItem {
  name: string
  type: 'image' | 'video'
}

// Re-export for convenience
export type { FilterResult, RunResult }

// ── Base ─────────────────────────────────────────────────────────────────────

const BASE = '/api'

/** Map raw API/network errors to human-readable messages. */
function humanizeError(raw: string): string {
  if (/Cannot decode (image|source)/i.test(raw))
    return 'Cannot read this file — upload a valid image (PNG, JPEG, etc.).'
  if (/video (files?|upload) (are|is) not supported/i.test(raw))
    return raw.replace(/^\d{3}: /, '')
  if (/source not found/i.test(raw))
    return 'Media file not found in library.'
  if (/iverilog not installed/i.test(raw))
    return 'RTL simulator (iverilog) is not installed on the server.'
  if (/must be at least 3.3/i.test(raw))
    return 'Image is too small — minimum 3×3 pixels required.'
  if (/RTL simulation failed/i.test(raw))
    return 'RTL simulation error — check iverilog installation.'
  if (/Failed to fetch|NetworkError|ECONNREFUSED/i.test(raw))
    return 'Cannot reach the backend server — is it running?'
  // Strip bare status code prefix for any other message
  return raw.replace(/^\d{3}: /, '')
}

async function _json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail ?? JSON.stringify(body)
    } catch { /* ignore */ }
    throw new Error(humanizeError(`${res.status}: ${detail}`))
  }
  return res.json() as Promise<T>
}

// ── Endpoints ────────────────────────────────────────────────────────────────

/** List available media sources from data/ */
export async function fetchMedia(): Promise<MediaItem[]> {
  try {
    return _json<MediaItem[]>(await fetch(`${BASE}/media`))
  } catch (err) {
    throw new Error(humanizeError(err instanceof Error ? err.message : 'Failed to load media list'))
  }
}

/**
 * Apply a kernel filter to a named source (from data/) or an uploaded File.
 * Returns base64-encoded input + output PNGs and statistics.
 */
export async function runFilter(
  source: string | File,
  kernel: KernelName,
): Promise<FilterResult> {
  const params = new URLSearchParams({ kernel })
  try {
    if (typeof source === 'string') {
      params.set('source', source)
      return _json<FilterResult>(await fetch(`${BASE}/filter?${params}`, { method: 'POST' }))
    }
    const form = new FormData()
    form.append('file', source)
    return _json<FilterResult>(await fetch(`${BASE}/filter?${params}`, { method: 'POST', body: form }))
  } catch (err) {
    throw new Error(humanizeError(err instanceof Error ? err.message : 'Filter failed'))
  }
}

export interface ValidateOptions {
  source: string | File
  kernel: KernelName
  roi?: { x: number; y: number; w: number; h: number } | null
}

/**
 * Run full RTL snapshot validation.
 * Blocks until the simulation completes — can take several seconds.
 */
export async function runValidate(opts: ValidateOptions): Promise<RunResult> {
  const params = new URLSearchParams({ kernel: opts.kernel })
  if (opts.roi) {
    params.set('roi_x', String(opts.roi.x))
    params.set('roi_y', String(opts.roi.y))
    params.set('roi_w', String(opts.roi.w))
    params.set('roi_h', String(opts.roi.h))
  }

  try {
    if (typeof opts.source === 'string') {
      params.set('source', opts.source)
      return _json<RunResult>(await fetch(`${BASE}/validate?${params}`, { method: 'POST' }))
    }
    const form = new FormData()
    form.append('file', opts.source)
    return _json<RunResult>(await fetch(`${BASE}/validate?${params}`, { method: 'POST', body: form }))
  } catch (err) {
    throw new Error(humanizeError(err instanceof Error ? err.message : 'Validation failed'))
  }
}

/** List all past validation runs (newest first). */
export async function fetchRuns(): Promise<RunResult[]> {
  return _json<RunResult[]>(await fetch(`${BASE}/runs`))
}

/** Get a single run's report. */
export async function fetchRun(runId: string): Promise<RunResult> {
  return _json<RunResult>(await fetch(`${BASE}/runs/${runId}`))
}

/** URL for a run artifact (board.png, diff_map.png, report.json, report.txt). */
export function artifactUrl(runId: string, filename: string): string {
  return `${BASE}/runs/${runId}/artifacts/${filename}`
}
