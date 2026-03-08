import { useEffect, useState } from 'react'
import { useParams, Navigate, Link } from 'react-router-dom'
import { useAuth } from '../lib/AuthContext'
import { GlassCard } from '../components/ui/GlassCard'
import { Button } from '../components/ui/Button'
import { MedalMilitary, ChartBar, ListChecks, ClockCounterClockwise, Plus } from '@phosphor-icons/react'

export default function Results() {
    const { id } = useParams()
    const { session, loading: authLoading } = useAuth()
    const [result, setResult] = useState(null)
    const [error, setError] = useState("")

    useEffect(() => {
        if (!session || !id) return

        const fetchResult = async () => {
            try {
                const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
                const response = await fetch(`${apiUrl}/history/${id}`, {
                    headers: { 'Authorization': `Bearer ${session.access_token}` }
                })
                const data = await response.json()
                if (!response.ok) {
                    const errMsg = Array.isArray(data.detail)
                        ? data.detail.map(d => d.msg).join(", ")
                        : (data.detail || "Failed to load results")
                    throw new Error(errMsg)
                }
                setResult(data.result)
            } catch (err) {
                setError(err.message)
            }
        }
        fetchResult()
    }, [id, session])

    if (authLoading) return null
    if (!session) return <Navigate to="/login" />

    if (error) return <div className="pt-32 px-6 text-center text-red-600 text-sm">{error}</div>
    if (!result) return <div className="pt-32 px-6 text-center text-muted text-sm"><span className="animate-pulse">Loading audit data…</span></div>

    const audit = result.audit || {}
    const isEligible = audit.eligible

    let missingCourses = [...(audit.failed_courses || [])]
    const missingCats = audit.missing_courses || {}
        ;['ged', 'math', 'science', 'business', 'major', 'capstone', 'internship'].forEach(cat => {
            if (Array.isArray(missingCats[cat])) missingCourses = [...missingCourses, ...missingCats[cat]]
        })

    const gradeDist = result.grade_distribution || {}

    return (
        <div className="min-h-screen pt-28 px-6 lg:px-12 flex flex-col items-center pb-24 bg-background">
            <div className="w-full max-w-5xl">
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <div className="flex items-center gap-2 mb-2">
                            <MedalMilitary size={14} weight="thin" className="text-muted" />
                            <span className="text-xs uppercase tracking-widest text-muted font-medium">Degree Audit</span>
                        </div>
                        <h1 className="text-4xl font-display text-foreground">Results</h1>
                        <p className="text-muted text-sm mt-1">{result.program || 'Analysis complete'}</p>
                    </div>
                    <div className="flex gap-2">
                        <Link to="/history"><Button variant="ghost" className="text-xs h-8 px-3 inline-flex items-center gap-1.5"><ClockCounterClockwise size={13} weight="regular" />History</Button></Link>
                        <Link to="/dashboard"><Button variant="glass" className="text-xs h-8 px-3 inline-flex items-center gap-1.5"><Plus size={13} weight="bold" />New Audit</Button></Link>
                    </div>
                </div>

                {/* Stat cards */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-8">
                    <GlassCard className={`lg:col-span-1 border-t-4 ${isEligible ? 'border-t-green-500' : 'border-t-red-500'}`}>
                        <p className="text-xs uppercase tracking-widest text-muted mb-2">Status</p>
                        <h2 className={`text-4xl md:text-5xl font-display ${isEligible ? 'text-green-600' : 'text-red-600'}`}>
                            {isEligible ? 'ELIGIBLE' : 'DEFICIENT'}
                        </h2>
                    </GlassCard>

                    <GlassCard>
                        <p className="text-xs uppercase tracking-widest text-muted mb-2">Credits</p>
                        <h2 className="text-4xl md:text-5xl font-display text-foreground">
                            {audit.credits_completed || 0}
                            <span className="text-xl text-muted ml-1">/ {audit.credits_required || 0}</span>
                        </h2>
                    </GlassCard>

                    <GlassCard>
                        <p className="text-xs uppercase tracking-widest text-muted mb-2">CGPA</p>
                        <h2 className="text-4xl md:text-5xl font-display text-foreground">{(result.cgpa?.final || 0).toFixed(3)}</h2>
                    </GlassCard>
                </div>

                {/* Missing courses */}
                {missingCourses.length > 0 && (
                    <GlassCard className="mb-8 border border-red-200 bg-red-50/60">
                        <h3 className="text-sm font-medium text-red-700 mb-4">Action Required: Missing or Failed Courses</h3>
                        <div className="flex flex-wrap gap-2">
                            {missingCourses.map((c, i) => (
                                <span key={i} className="px-3 py-1 bg-red-100 border border-red-200 rounded-md text-red-700 text-sm font-medium">{c}</span>
                            ))}
                        </div>
                    </GlassCard>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                    <GlassCard>
                        <h3 className="text-sm font-medium text-foreground mb-5 flex items-center gap-2">
                            <ListChecks size={16} weight="thin" className="text-muted" />
                            Academic Roadmap
                        </h3>
                        <div className="flex flex-col gap-3">
                            {audit.roadmap && audit.roadmap.length > 0 ? (
                                audit.roadmap.map((step, i) => (
                                    <div key={i} className="border-l-2 border-foreground/20 pl-4 py-1">
                                        <p className="text-sm text-foreground/80">{step}</p>
                                    </div>
                                ))
                            ) : (
                                <div className="border-l-2 border-green-500 pl-4 py-1">
                                    <p className="text-green-600 font-medium text-sm">All requirements complete!</p>
                                    <p className="text-muted text-xs mt-1">Ready for graduation approval.</p>
                                </div>
                            )}
                        </div>
                    </GlassCard>

                    <GlassCard>
                        <h3 className="text-sm font-medium text-foreground mb-5 flex items-center gap-2">
                            <ChartBar size={16} weight="thin" className="text-muted" />
                            Grade Distribution
                        </h3>
                        <div className="flex flex-col gap-3">
                            {Object.entries(gradeDist).map(([grade, count]) => (
                                <div key={grade} className="flex items-center gap-3">
                                    <span className="text-foreground/70 font-medium text-sm w-8">{grade}</span>
                                    <div className="flex-1 bg-black/6 h-1.5 rounded-full overflow-hidden">
                                        <div
                                            className="bg-foreground/50 h-full rounded-full"
                                            style={{ width: `${(count / Math.max(...Object.values(gradeDist))) * 100}%` }}
                                        />
                                    </div>
                                    <span className="text-muted text-xs">{count}</span>
                                </div>
                            ))}
                            {Object.keys(gradeDist).length === 0 && <p className="text-muted text-sm">No grades recorded.</p>}
                        </div>
                    </GlassCard>
                </div>
            </div>
        </div>
    )
}
