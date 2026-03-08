import { useEffect, useRef } from 'react'

/**
 * ALGORITHMIC PHILOSOPHY: "Scholarly Drift"
 * 
 * Knowledge accumulates like sediment — particle trails marking the invisible 
 * currents of academic thought. A Perlin noise flow field guides thousands of 
 * ink-dark particles across parchment white, their paths converging and diverging
 * like footnotes threading through density maps of meaning.
 * 
 * Each seed produces a unique topology of accumulated wisdom — same laws of motion,
 * different emergent configuration. The beauty lives in the accumulation itself.
 * 
 * Implemented using the algorithmic-art skill pattern: seeded Perlin noise flow field,
 * particle lifecycle with trail opacity, convergence zones, and controlled chaos.
 */

// Seeded PRNG (mulberry32) — same seed = same art every time
function mulberry32(seed) {
    return function () {
        seed |= 0; seed = seed + 0x6D2B79F5 | 0
        let t = Math.imul(seed ^ seed >>> 15, 1 | seed)
        t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t
        return ((t ^ t >>> 14) >>> 0) / 4294967296
    }
}

// Smooth 2D value noise (Perlin-style) — no external lib needed
function makeNoise(seed) {
    const rand = mulberry32(seed)
    const SIZE = 256
    const g = Array.from({ length: SIZE * SIZE }, () => rand() * Math.PI * 2)
    return (x, y) => {
        const ix = Math.floor(x) & (SIZE - 1)
        const iy = Math.floor(y) & (SIZE - 1)
        const fx = x - Math.floor(x)
        const fy = y - Math.floor(y)
        // Smoothstep
        const ux = fx * fx * (3 - 2 * fx)
        const uy = fy * fy * (3 - 2 * fy)
        const a = g[ix + iy * SIZE]
        const b = g[((ix + 1) & (SIZE - 1)) + iy * SIZE]
        const c = g[ix + ((iy + 1) & (SIZE - 1)) * SIZE]
        const d = g[((ix + 1) & (SIZE - 1)) + ((iy + 1) & (SIZE - 1)) * SIZE]
        // Interpolate dot products
        const dot = (angle, dx, dy) => Math.cos(angle) * dx + Math.sin(angle) * dy
        const n00 = dot(a, fx, fy)
        const n10 = dot(b, fx - 1, fy)
        const n01 = dot(c, fx, fy - 1)
        const n11 = dot(d, fx - 1, fy - 1)
        return (1 - ux) * ((1 - uy) * n00 + uy * n01) + ux * ((1 - uy) * n10 + uy * n11)
    }
}

export function AlgorithmicBackground({ seed = 42 }) {
    const canvasRef = useRef(null)

    useEffect(() => {
        const canvas = canvasRef.current
        if (!canvas) return
        const ctx = canvas.getContext('2d')

        let animId
        let frame = 0
        const SEED = seed

        const resize = () => {
            canvas.width = canvas.offsetWidth
            canvas.height = canvas.offsetHeight
        }
        resize()

        const noise = makeNoise(SEED)
        const rand = mulberry32(SEED + 1)

        // Flow field parameters
        const COLS = 40
        const ROWS = 30
        const NUM_PARTICLES = 30
        const NOISE_SCALE = 0.003
        const SPEED = 0.9

        // Particles
        let particles = Array.from({ length: NUM_PARTICLES }, () => ({
            x: rand() * canvas.width,
            y: rand() * canvas.height,
            age: rand() * 120,
            maxAge: 80 + rand() * 120,
            size: 0.4 + rand() * 1.1,
        }))

        // Draw flow field background grid (very subtle)
        const drawGrid = () => {
            ctx.strokeStyle = 'rgba(26, 23, 20, 0.008)'
            ctx.lineWidth = 0.5
            const cellW = canvas.width / COLS
            const cellH = canvas.height / ROWS
            for (let col = 0; col <= COLS; col++) {
                ctx.beginPath()
                ctx.moveTo(col * cellW, 0)
                ctx.lineTo(col * cellW, canvas.height)
                ctx.stroke()
            }
            for (let row = 0; row <= ROWS; row++) {
                ctx.beginPath()
                ctx.moveTo(0, row * cellH)
                ctx.lineTo(canvas.width, row * cellH)
                ctx.stroke()
            }
        }

        const draw = () => {
            // On first frame, draw the subtle grid and fill background
            if (frame === 0) {
                ctx.fillStyle = '#FAF8F5'
                ctx.fillRect(0, 0, canvas.width, canvas.height)
                drawGrid()
            }

            // Very faint fade — trails barely visible
            ctx.fillStyle = 'rgba(250, 248, 245, 0.004)'
            ctx.fillRect(0, 0, canvas.width, canvas.height)

            particles.forEach(p => {
                // Sample noise field at position
                const angle = noise(p.x * NOISE_SCALE, p.y * NOISE_SCALE + frame * 0.0008) * Math.PI * 3

                p.x += Math.cos(angle) * SPEED
                p.y += Math.sin(angle) * SPEED
                p.age++

                // Life cycle — fade in and out
                const life = p.age / p.maxAge
                const opacity = life < 0.15
                    ? life / 0.15 * 0.004
                    : life > 0.75
                        ? (1 - (life - 0.75) / 0.25) * 0.004
                        : 0.004

                // Reset if dead or offscreen
                if (p.age > p.maxAge || p.x < -20 || p.x > canvas.width + 20 || p.y < -20 || p.y > canvas.height + 20) {
                    p.x = rand() * canvas.width
                    p.y = rand() * canvas.height
                    p.age = 0
                    p.maxAge = 80 + rand() * 120
                    p.size = 0.4 + rand() * 1.1
                    return
                }

                ctx.beginPath()
                ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
                ctx.fillStyle = `rgba(26, 23, 20, ${opacity})`
                ctx.fill()
            })

            frame++
            animId = requestAnimationFrame(draw)
        }

        draw()

        const handleResize = () => {
            resize()
            frame = 0
            ctx.fillStyle = '#FAF8F5'
            ctx.fillRect(0, 0, canvas.width, canvas.height)
            drawGrid()
        }
        window.addEventListener('resize', handleResize)

        return () => {
            cancelAnimationFrame(animId)
            window.removeEventListener('resize', handleResize)
        }
    }, [seed])

    return (
        <canvas
            ref={canvasRef}
            style={{
                position: 'fixed',
                inset: 0,
                width: '100%',
                height: '100%',
                zIndex: 0,
                pointerEvents: 'none',
                display: 'block',
            }}
        />
    )
}
