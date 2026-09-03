import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowRight, CheckCircle } from '@phosphor-icons/react'
import { Button } from '../components/ui/Button'
import { GlassCard } from '../components/ui/GlassCard'
import { AnimatedText } from '../components/ui/AnimatedText'
import { AlgorithmicBackground } from '../components/AlgorithmicBackground'
import { useAuth } from '../lib/AuthContext'
import emblem from '../assets/brand/gradgate-emblem-ui.png'

const features = [
    "CSE, BBA, EEE & ETE programs",
    "CSV & image transcript support",
    "CGPA, credit & deficiency analysis",
]

export default function Landing() {
    const { session } = useAuth()
    const ctaTarget = session ? '/dashboard' : '/login'

    return (
        <div className="paper-hero min-h-screen flex items-center pt-20 text-left pl-6 md:pl-16 lg:pl-32">

            <div className="max-w-4xl z-10 w-full relative">
                {/* Badge */}
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6 }}
                >
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-black/10 bg-white/60 backdrop-blur-sm mb-8">
                        <img src={emblem} alt="" className="h-5 w-5 rounded-lg object-cover ring-1 ring-black/5" />
                        <span className="text-xs font-medium text-muted tracking-wide">Intelligent Degree Auditing</span>
                    </div>
                </motion.div>

                {/* Hero headline */}
                <h1 className="flex flex-col gap-2">
                    <AnimatedText
                        text="Take control of your"
                        className="text-5xl md:text-7xl lg:text-[80px] font-sans font-light tracking-tight text-foreground/70 leading-tight"
                        delay={0.1}
                    />
                    <AnimatedText
                        text="academic journey."
                        className="text-6xl md:text-8xl lg:text-[100px] font-display italic text-foreground leading-none pb-2"
                        delay={0.6}
                    />
                </h1>

                {/* One-liner */}
                <motion.p
                    className="mt-6 text-base text-muted max-w-sm leading-relaxed"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 1.2, duration: 0.8 }}
                >
                    Audit smarter. Graduate faster.
                </motion.p>

                {/* Feature pills */}
                <motion.ul
                    className="mt-4 flex flex-col gap-1.5"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 1.5, duration: 0.6 }}
                >
                    {features.map((f, i) => (
                        <li key={i} className="flex items-center gap-2 text-sm text-muted">
                            <CheckCircle size={13} weight="fill" className="text-foreground/30 shrink-0" />
                            {f}
                        </li>
                    ))}
                </motion.ul>

                {/* CTAs */}
                <motion.div
                    className="mt-10 flex items-center gap-6"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 1.8, duration: 0.6 }}
                >
                    <Link to={ctaTarget}>
                        <Button className="h-13 px-8 text-sm font-semibold group inline-flex items-center gap-2">
                            {session ? 'Go to Dashboard' : 'Get Started'}
                            <ArrowRight size={14} weight="bold" className="group-hover:translate-x-1 transition-transform" />
                        </Button>
                    </Link>
                    {session && (
                        <Link to="/history" className="text-sm text-muted hover:text-foreground transition-colors">
                            View History →
                        </Link>
                    )}
                </motion.div>
            </div>

            {/* Right side preview card */}
            <motion.div
                className="hidden lg:block absolute right-16 top-1/2 -translate-y-1/2 w-[360px]"
                initial={{ opacity: 0, x: 50 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 1.8, duration: 1, type: "spring" }}
            >
                <div className="brand-orb absolute -right-10 -top-12 h-40 w-40 rounded-full" />
                <GlassCard className="shadow-2xl shadow-black/10">
                    <div className="flex justify-between items-center mb-5">
                        <h3 className="text-[11px] font-semibold uppercase tracking-widest text-muted">Sample Overview</h3>
                        <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full border border-black/10 text-muted">Preview</span>
                    </div>
                    <div className="mb-5">
                        <div className="flex justify-between text-xs mb-2 text-muted">
                            <span>Degree Progress</span>
                            <span>78%</span>
                        </div>
                        <div className="w-full bg-black/6 h-1 rounded-full overflow-hidden">
                            <div className="bg-foreground h-full rounded-full w-[78%]"></div>
                        </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4 pt-5 border-t border-black/6">
                        <div className="min-w-0">
                            <p className="text-[10px] text-muted mb-1 uppercase tracking-wider">Credits</p>
                            <p className="text-2xl font-display text-foreground">94 <span className="text-muted text-sm font-sans font-normal">/ 120</span></p>
                        </div>
                        <div>
                            <p className="text-[10px] text-muted mb-1 uppercase tracking-wider">CGPA</p>
                            <p className="text-2xl font-display text-foreground">3.82</p>
                        </div>
                    </div>
                    <div className="mt-4 pt-4 border-t border-black/5 flex items-center justify-between">
                        <span className="text-xs text-muted">CSE Program</span>
                        <span className="text-xs text-green-600 font-medium">On Track</span>
                    </div>
                </GlassCard>
            </motion.div>
        </div>
    )
}
