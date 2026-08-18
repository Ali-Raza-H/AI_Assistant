import { useEffect, useRef } from 'react'
import type { CielState, ConnectionState } from '../state/types'

type VisualMode = 'idle' | 'listening' | 'routing' | 'working' | 'speaking' | 'error' | 'offline'

function modeFor(state: CielState, connection: ConnectionState, listening: boolean): VisualMode {
  if (connection !== 'online') return 'offline'
  if (state.status === 'error') return 'error'
  if (state.stage === 'speech') return 'speaking'
  if (state.stage === 'router') return 'routing'
  if (state.stage === 'tools') return 'working'
  if (['context', 'memory', 'brain', 'observation', 'response', 'controller'].includes(state.stage)) return 'working'
  if (listening) return 'listening'
  return 'idle'
}

const colors: Record<VisualMode, string> = {
  idle: '#5ad6df',
  listening: '#eafcff',
  routing: '#7ae1e8',
  working: '#e7bb61',
  speaking: '#efffff',
  error: '#e65b55',
  offline: '#596164',
}

export function CielCore({ state, connection, listening }: { state: CielState; connection: ConnectionState; listening: boolean }) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const mode = modeFor(state, connection, listening)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const context = canvas.getContext('2d')
    if (!context) return
    let frame = 0
    let animation = 0
    const ratio = Math.min(window.devicePixelRatio || 1, 2)
    const size = 520
    canvas.width = size * ratio
    canvas.height = size * ratio
    context.scale(ratio, ratio)

    const draw = () => {
      const center = size / 2
      const time = frame / 60
      const color = colors[mode]
      context.clearRect(0, 0, size, size)
      context.save()
      context.translate(center, center)

      context.strokeStyle = '#151a1c'
      context.lineWidth = 1
      for (const radius of [88, 128, 178, 224]) {
        context.beginPath()
        context.arc(0, 0, radius, 0, Math.PI * 2)
        context.stroke()
      }

      const speed = mode === 'speaking' ? 2.8 : mode === 'working' ? 1.7 : mode === 'routing' ? 1.2 : 0.35
      const tickCount = 72
      context.strokeStyle = color
      context.globalAlpha = mode === 'offline' ? 0.35 : 0.8
      for (let index = 0; index < tickCount; index += 1) {
        const angle = (index / tickCount) * Math.PI * 2 + time * speed * 0.1
        const activity = (Math.sin(index * 1.71 + time * speed * 2) + 1) / 2
        const inner = 177
        const outer = inner + (index % 6 === 0 ? 16 : 5 + activity * 7)
        context.beginPath()
        context.moveTo(Math.cos(angle) * inner, Math.sin(angle) * inner)
        context.lineTo(Math.cos(angle) * outer, Math.sin(angle) * outer)
        context.stroke()
      }

      context.lineWidth = 2
      context.globalAlpha = 0.95
      for (let ring = 0; ring < 3; ring += 1) {
        const radius = 102 + ring * 27
        const direction = ring % 2 ? -1 : 1
        const start = time * speed * direction + ring * 1.4
        const length = mode === 'speaking' ? 0.9 + Math.sin(time * 5 + ring) * 0.3 : 0.45 + ring * 0.14
        context.beginPath()
        context.arc(0, 0, radius, start, start + length)
        context.stroke()
        context.beginPath()
        context.arc(0, 0, radius, start + Math.PI, start + Math.PI + length * 0.55)
        context.stroke()
      }

      const pulse = mode === 'speaking' ? Math.sin(time * 7) * 9 : Math.sin(time * 1.4) * 3
      context.globalAlpha = 1
      context.fillStyle = color
      context.beginPath()
      context.arc(0, 0, 4 + Math.max(0, pulse * 0.15), 0, Math.PI * 2)
      context.fill()

      context.strokeStyle = color
      context.lineWidth = 1
      context.globalAlpha = 0.6
      const waveWidth = 112
      context.beginPath()
      for (let x = -waveWidth; x <= waveWidth; x += 3) {
        const envelope = 1 - Math.abs(x) / waveWidth
        const amplitude = mode === 'speaking' ? 18 : mode === 'working' ? 7 : 2
        const y = Math.sin(x * 0.13 + time * speed * 5) * envelope * amplitude
        if (x === -waveWidth) context.moveTo(x, y)
        else context.lineTo(x, y)
      }
      context.stroke()

      context.restore()
      frame += 1
      animation = requestAnimationFrame(draw)
    }
    draw()
    return () => cancelAnimationFrame(animation)
  }, [mode])

  const labels: Record<VisualMode, string> = {
    idle: 'READY',
    listening: 'LISTENING',
    routing: 'ROUTING',
    working: 'PROCESSING',
    speaking: 'SPEAKING',
    error: 'FAULT',
    offline: 'OFFLINE',
  }

  return (
    <div className={`ciel-core ${mode}`}>
      <div className="core-coordinate top">CIEL // {String(state.iteration).padStart(2, '0')}</div>
      <canvas ref={canvasRef} aria-label={`CIEL is ${labels[mode].toLowerCase()}`} />
      <div className="core-label">
        <span>{labels[mode]}</span>
        <small>{state.stage === 'idle' ? 'AWAITING DIRECTIVE' : `STAGE / ${state.stage.toUpperCase()}`}</small>
      </div>
      <div className="core-coordinate bottom">SYS.{connection === 'online' ? 'ONLINE' : 'NO LINK'}</div>
    </div>
  )
}
