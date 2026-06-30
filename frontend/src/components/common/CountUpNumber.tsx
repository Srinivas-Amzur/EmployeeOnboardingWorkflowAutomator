import React, { useEffect, useMemo, useState } from "react"

interface CountUpNumberProps {
  value: number
  durationMs?: number
  className?: string
  suffix?: string
}

export const CountUpNumber: React.FC<CountUpNumberProps> = ({
  value,
  durationMs = 700,
  className = "",
  suffix = "",
}) => {
  const [display, setDisplay] = useState(0)

  const target = useMemo(() => Math.max(0, Number.isFinite(value) ? value : 0), [value])

  useEffect(() => {
    let frame = 0
    const startedAt = performance.now()

    const step = (now: number) => {
      const progress = Math.min(1, (now - startedAt) / durationMs)
      const eased = 1 - Math.pow(1 - progress, 3)
      setDisplay(Math.round(target * eased))
      if (progress < 1) {
        frame = requestAnimationFrame(step)
      }
    }

    frame = requestAnimationFrame(step)
    return () => cancelAnimationFrame(frame)
  }, [durationMs, target])

  return <span className={className}>{display}{suffix}</span>
}
