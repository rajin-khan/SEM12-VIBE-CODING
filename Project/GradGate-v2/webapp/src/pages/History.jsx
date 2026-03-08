import { useEffect, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '../lib/AuthContext'
import { GlassCard } from '../components/ui/GlassCard'
import { FileText, ArrowRight, ClockCounterClockwise } from '@phosphor-icons/react'

export default function History() {
    const { session, loading } = useAuth()
    const [history, setHistory] = useState([])
    const [isFetching, setIsFetching] = useState(true)
    const [err, setErr] = useState("")

    useEffect(() => {
        if (!session) return
        const fetchHistory = async () => {
            try {
                const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
                const res = await fetch(`${apiUrl}/history`, {
                    headers: { 'Authorization': `Bearer ${session.access_token}` }
                })
                const data = await res.json()
                if (!res.ok) throw new Error(data.detail || "Failed to load history")
                setHistory(data)
            } catch (e) {
                setErr(e.message)
            } finally {
                setIsFetching(false)
            }
        }
        fetchHistory()
    }, [session])

    if (loading) return null
    if (!session) return <Navigate to="/login" />

    const formatDate = (iso) => {
        const d = new Date(iso)
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })
    }

    return (
        <div className="min-h-screen pt-28 px-6 flex flex-col items-center pb-24 bg-background">
            <div className="w-full max-w-4xl">
                <div className="flex items-center justify-between mb-10">
                    <div>
                        <div className="flex items-center gap-2 mb-2">
                            <ClockCounterClockwise size={14} weight="thin" className="text-muted" />
                            <span className="text-xs uppercase tracking-widest text-muted font-medium">Audit History</span>
                        </div>
                        <h1 className="text-4xl font-display text-foreground">Past Scans</h1>
                    </div>
                    <Link
                        to="/dashboard"
                        className="inline-flex items-center gap-2 bg-foreground text-background text-sm font-semibold rounded-sm px-5 py-2.5 hover:bg-foreground/90 transition-colors"
                    >
                        New Audit
                    </Link>
                </div>

                {err && <div className="text-red-700 text-sm mb-6 border border-red-200 bg-red-50 rounded-lg px-4 py-3">{err}</div>}

                {isFetching ? (
                    <div className="flex flex-col gap-3">
                        {[1, 2, 3].map(i => (
                            <div key={i} className="glass-panel rounded-2xl p-6 animate-pulse">
                                <div className="h-4 bg-black/5 rounded w-1/3 mb-3" />
                                <div className="h-3 bg-black/5 rounded w-1/4" />
                            </div>
                        ))}
                    </div>
                ) : history.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-24 border border-dashed border-black/10 rounded-xl gap-4">
                        <div className="w-16 h-16 rounded-full bg-white/60 border border-black/8 flex items-center justify-center">
                            <FileText size={28} weight="thin" className="text-muted" />
                        </div>
                        <div className="text-center">
                            <p className="text-foreground/70 font-medium mb-1">No audits yet</p>
                            <p className="text-muted text-sm">Upload a transcript to run your first degree audit.</p>
                        </div>
                        <Link
                            to="/dashboard"
                            className="mt-2 inline-flex items-center gap-2 text-sm text-muted hover:text-foreground transition-colors border border-black/10 px-4 py-2 rounded-lg hover:border-black/20"
                        >
                            Start an Audit <ArrowRight size={14} weight="regular" />
                        </Link>
                    </div>
                ) : (
                    <div className="flex flex-col gap-3">
                        {history.map(scan => (
                            <Link to={`/results/${scan.id}`} key={scan.id}>
                                <GlassCard className="flex items-center justify-between hover:shadow-md transition-all cursor-pointer py-5 px-6 md:px-8 hover:bg-white/80">
                                    <div className="flex items-center gap-4">
                                        <div className="w-10 h-10 rounded-lg bg-white/70 border border-black/8 flex items-center justify-center shrink-0 shadow-sm">
                                            <FileText size={18} weight="thin" className="text-muted" />
                                        </div>
                                        <div>
                                            <h3 className="text-foreground font-medium mb-0.5">
                                                <span className="font-semibold">{scan.program}</span> Degree Audit
                                            </h3>
                                            <p className="text-muted text-xs">
                                                {formatDate(scan.created_at)}
                                                {scan.file_name && <span className="ml-2 text-foreground/30">· {scan.file_name}</span>}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-3 shrink-0">
                                        <span className="hidden sm:inline px-2 py-1 bg-black/4 rounded border border-black/8 text-[11px] font-medium text-muted uppercase tracking-widest">
                                            {scan.input_type}
                                        </span>
                                        <ArrowRight size={14} weight="regular" className="text-muted" />
                                    </div>
                                </GlassCard>
                            </Link>
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}
