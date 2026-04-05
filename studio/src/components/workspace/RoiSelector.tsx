/**
 * RoiSelector — drag-to-select ROI overlay on top of an image.
 *
 * Rendered as an absolutely-positioned layer over the image container.
 * Maps screen coordinates → image pixel coordinates, accounting for
 * object-contain letterboxing.
 *
 * naturalWidth / naturalHeight must match the image being displayed
 * (from FilterResult.input_h / input_w, or the image's natural dims).
 */
import { useRef, useState, useCallback } from 'react'
import type { RoiSelection } from '../../types'

interface RoiSelectorProps {
  naturalWidth: number
  naturalHeight: number
  roi: RoiSelection | null
  onRoiChange: (roi: RoiSelection | null) => void
}

interface Point { x: number; y: number }

/** Compute how a natural-size image fits inside a rendered container with object-contain. */
function letterboxMap(
  containerW: number, containerH: number,
  naturalW: number,   naturalH: number,
): { offsetX: number; offsetY: number; scaleX: number; scaleY: number } {
  const containerRatio = containerW / containerH
  const naturalRatio   = naturalW / naturalH

  let renderedW: number, renderedH: number
  if (naturalRatio > containerRatio) {
    // Width-constrained
    renderedW = containerW
    renderedH = containerW / naturalRatio
  } else {
    // Height-constrained
    renderedH = containerH
    renderedW = containerH * naturalRatio
  }

  return {
    offsetX: (containerW - renderedW) / 2,
    offsetY: (containerH - renderedH) / 2,
    scaleX:  naturalW / renderedW,
    scaleY:  naturalH / renderedH,
  }
}

function screenToImage(
  sx: number, sy: number,
  rect: DOMRect,
  naturalW: number, naturalH: number,
): Point {
  const { offsetX, offsetY, scaleX, scaleY } = letterboxMap(
    rect.width, rect.height, naturalW, naturalH,
  )
  return {
    x: Math.round((sx - rect.left - offsetX) * scaleX),
    y: Math.round((sy - rect.top  - offsetY) * scaleY),
  }
}

function imageToScreen(
  ix: number, iy: number,
  rect: DOMRect,
  naturalW: number, naturalH: number,
): Point {
  const { offsetX, offsetY, scaleX, scaleY } = letterboxMap(
    rect.width, rect.height, naturalW, naturalH,
  )
  return {
    x: ix / scaleX + offsetX,
    y: iy / scaleY + offsetY,
  }
}

function clamp(v: number, min: number, max: number) {
  return Math.max(min, Math.min(max, v))
}

export default function RoiSelector({
  naturalWidth, naturalHeight, roi, onRoiChange,
}: RoiSelectorProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [dragging, setDragging] = useState(false)
  const [dragStart, setDragStart] = useState<Point | null>(null)
  const [dragCurrent, setDragCurrent] = useState<Point | null>(null)

  const getRect = () => containerRef.current?.getBoundingClientRect()

  const onMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    const rect = getRect()
    if (!rect) return
    const pt = screenToImage(e.clientX, e.clientY, rect, naturalWidth, naturalHeight)
    setDragging(true)
    setDragStart(pt)
    setDragCurrent(pt)
    onRoiChange(null)
  }, [naturalWidth, naturalHeight, onRoiChange])

  const onMouseMove = useCallback((e: React.MouseEvent) => {
    if (!dragging || !dragStart) return
    const rect = getRect()
    if (!rect) return
    const pt = screenToImage(e.clientX, e.clientY, rect, naturalWidth, naturalHeight)
    setDragCurrent(pt)
  }, [dragging, dragStart, naturalWidth, naturalHeight])

  const onMouseUp = useCallback((e: React.MouseEvent) => {
    if (!dragging || !dragStart) return
    setDragging(false)

    const rect = getRect()
    if (!rect) return
    const end = screenToImage(e.clientX, e.clientY, rect, naturalWidth, naturalHeight)

    const x = clamp(Math.min(dragStart.x, end.x), 0, naturalWidth - 1)
    const y = clamp(Math.min(dragStart.y, end.y), 0, naturalHeight - 1)
    const w = clamp(Math.abs(end.x - dragStart.x), 3, naturalWidth  - x)
    const h = clamp(Math.abs(end.y - dragStart.y), 3, naturalHeight - y)

    if (w >= 3 && h >= 3) {
      onRoiChange({ x, y, w, h })
    } else {
      onRoiChange(null)
    }
    setDragStart(null)
    setDragCurrent(null)
  }, [dragging, dragStart, naturalWidth, naturalHeight, onRoiChange])

  // Build overlay rect in screen-space
  const overlayRect = (() => {
    const rect = containerRef.current?.getBoundingClientRect()
    if (!rect) return null

    let sx1: number, sy1: number, sx2: number, sy2: number

    if (dragging && dragStart && dragCurrent) {
      const a = imageToScreen(dragStart.x, dragStart.y, rect, naturalWidth, naturalHeight)
      const b = imageToScreen(dragCurrent.x, dragCurrent.y, rect, naturalWidth, naturalHeight)
      sx1 = Math.min(a.x, b.x); sy1 = Math.min(a.y, b.y)
      sx2 = Math.max(a.x, b.x); sy2 = Math.max(a.y, b.y)
    } else if (roi) {
      const tl = imageToScreen(roi.x,         roi.y,         rect, naturalWidth, naturalHeight)
      const br = imageToScreen(roi.x + roi.w, roi.y + roi.h, rect, naturalWidth, naturalHeight)
      sx1 = tl.x; sy1 = tl.y; sx2 = br.x; sy2 = br.y
    } else {
      return null
    }

    return { left: sx1, top: sy1, width: sx2 - sx1, height: sy2 - sy1 }
  })()

  return (
    <div
      ref={containerRef}
      className="absolute inset-0 cursor-crosshair select-none"
      onMouseDown={onMouseDown}
      onMouseMove={onMouseMove}
      onMouseUp={onMouseUp}
      onMouseLeave={onMouseUp}
    >
      {overlayRect && (
        <>
          {/* Semi-transparent overlay outside selection */}
          <div className="absolute inset-0 bg-black/30 pointer-events-none" />

          {/* Selection box */}
          <div
            className="absolute pointer-events-none"
            style={{
              left:   overlayRect.left,
              top:    overlayRect.top,
              width:  overlayRect.width,
              height: overlayRect.height,
              boxShadow: '0 0 0 9999px rgba(0,0,0,0.30)',
              border: '1.5px dashed rgba(251,191,36,0.8)',  // warn/amber
              background: 'rgba(251,191,36,0.05)',
            }}
          />

          {/* Dimension label */}
          {roi && (
            <div
              className="absolute pointer-events-none px-1 py-0.5 rounded
                         bg-zinc-900/90 border border-zinc-700"
              style={{
                left: overlayRect.left,
                top:  Math.max(0, overlayRect.top - 22),
                fontSize: 10,
                fontFamily: 'monospace',
                color: 'rgba(251,191,36,0.9)',
                whiteSpace: 'nowrap',
              }}
            >
              {roi.w}×{roi.h}
            </div>
          )}
        </>
      )}
    </div>
  )
}
