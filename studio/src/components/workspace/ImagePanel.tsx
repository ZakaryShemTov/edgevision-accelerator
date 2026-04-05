/**
 * A single image slot in the Visual Workspace.
 *
 * Shows a styled placeholder when no image data is available.
 * Accepts a base64 PNG data URI or a full URL (for artifact images).
 * Optionally renders a ROI selector overlay on top of the image.
 */
import type { RoiSelection } from '../../types'
import RoiSelector from './RoiSelector'

interface ImagePanelProps {
  label: string
  sublabel?: string
  variant: 'input' | 'output' | 'rtl' | 'diff'
  imageSrc?: string
  naturalWidth?: number
  naturalHeight?: number
  className?: string
  // ROI — only meaningful on the input panel
  roiActive?: boolean
  roi?: RoiSelection | null
  onRoiChange?: (roi: RoiSelection | null) => void
}

const GRADIENTS: Record<ImagePanelProps['variant'], string> = {
  input:
    'radial-gradient(ellipse 60% 55% at 35% 42%, rgba(180,180,190,0.07) 0%, transparent 70%),' +
    'linear-gradient(160deg, #111116 0%, #17171e 50%, #111116 100%)',
  output:
    'repeating-linear-gradient(0deg, rgba(34,211,238,0.04) 0px, rgba(34,211,238,0.04) 1px, transparent 1px, transparent 5px),' +
    'linear-gradient(160deg, #040810 0%, #080e1c 50%, #040810 100%)',
  rtl:
    'repeating-linear-gradient(0deg, rgba(52,211,153,0.035) 0px, rgba(52,211,153,0.035) 1px, transparent 1px, transparent 5px),' +
    'linear-gradient(160deg, #04100a 0%, #080e0a 50%, #04100a 100%)',
  diff:
    'linear-gradient(160deg, #101010 0%, #1a1a1a 50%, #101010 100%)',
}

const LABEL_COLORS: Record<ImagePanelProps['variant'], string> = {
  input:  'text-zinc-400',
  output: 'text-accent',
  rtl:    'text-pass',
  diff:   'text-zinc-400',
}

export default function ImagePanel({
  label, sublabel, variant, imageSrc,
  naturalWidth, naturalHeight,
  className = '',
  roiActive = false, roi, onRoiChange,
}: ImagePanelProps) {
  const showRoi = roiActive && naturalWidth && naturalHeight && onRoiChange

  return (
    <div className={`relative flex flex-col rounded-sm overflow-hidden
                     border border-zinc-800/80 bg-surface-1 ${className}`}>
      {/* Image area */}
      <div
        className="flex-1 relative overflow-hidden"
        style={{ background: imageSrc ? undefined : GRADIENTS[variant] }}
      >
        {imageSrc ? (
          <img
            src={imageSrc.startsWith('data:') || imageSrc.startsWith('http') || imageSrc.startsWith('/')
              ? imageSrc
              : `data:image/png;base64,${imageSrc}`}
            alt={label}
            className="w-full h-full object-contain"
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="flex flex-col items-center gap-0 opacity-10 select-none">
              <div className="w-6 h-px bg-zinc-400" />
              <div className="h-6 w-px bg-zinc-400 -mt-px" />
            </div>
          </div>
        )}

        {/* ROI overlay — only on input panel when active */}
        {showRoi && (
          <RoiSelector
            naturalWidth={naturalWidth}
            naturalHeight={naturalHeight}
            roi={roi ?? null}
            onRoiChange={onRoiChange}
          />
        )}
      </div>

      {/* Label strip */}
      <div className="flex-shrink-0 flex items-center justify-between px-2 py-1
                      border-t border-zinc-800/60 bg-surface-0/60">
        <span className={`text-[10px] font-mono font-medium tracking-widest uppercase ${LABEL_COLORS[variant]}`}>
          {label}
        </span>
        {sublabel && (
          <span className="text-[10px] font-mono text-zinc-600">{sublabel}</span>
        )}
      </div>
    </div>
  )
}
