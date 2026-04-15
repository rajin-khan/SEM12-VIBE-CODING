import { useEffect, useState } from 'react'
import { useParams, Navigate, Link } from 'react-router-dom'
import { useAuth } from '../lib/AuthContext'
import { GlassCard } from '../components/ui/GlassCard'
import { Button } from '../components/ui/Button'
import { ChartBar, ClockCounterClockwise, ListChecks, MedalMilitary, Plus, WarningCircle } from '@phosphor-icons/react'
import { levelLabel } from '../lib/auditConfig'
import { fetchResult } from '../lib/api'

function formatDate(value) {
    const date = new Date(value)
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    })
}

function MetricCard({ label, value, accent = '' }) {
    return (
        <GlassCard className={accent}>
            <p className="mb-2 text-xs uppercase tracking-widest text-muted">{label}</p>
            <h2 className="text-4xl font-display text-foreground">{value}</h2>
        </GlassCard>
    )
}

function SectionTitle({ icon, title, subtitle }) {
    return (
        <div className="mb-5">
            <div className="mb-2 flex items-center gap-2">
                {icon}
                <span className="text-xs font-medium uppercase tracking-widest text-muted">{title}</span>
            </div>
            {subtitle && <p className="text-sm text-muted">{subtitle}</p>}
        </div>
    )
}

function DataTable({ columns, rows, emptyLabel = 'No data available.' }) {
    if (!rows?.length) {
        return <p className="text-sm text-muted">{emptyLabel}</p>
    }

    return (
        <div className="overflow-auto rounded-xl border border-black/8">
            <table className="min-w-full divide-y divide-black/8 text-sm">
                <thead className="bg-black/3 text-left text-xs uppercase tracking-widest text-muted">
                    <tr>
                        {columns.map((column) => (
                            <th key={column.key} className="px-4 py-3 font-medium">{column.label}</th>
                        ))}
                    </tr>
                </thead>
                <tbody className="divide-y divide-black/6 bg-white/40">
                    {rows.map((row, index) => (
                        <tr key={row.id || `${row.course_code || row.semester || 'row'}-${index}`}>
                            {columns.map((column) => (
                                <td key={column.key} className="px-4 py-3 align-top text-foreground/80">
                                    {column.render ? column.render(row) : row[column.key] ?? '—'}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    )
}

export default function Results() {
    const { id } = useParams()
    const { session, loading: authLoading } = useAuth()
    const [scan, setScan] = useState(null)
    const [error, setError] = useState('')

    useEffect(() => {
        if (!session || !id) return

        fetchResult(session, id)
            .then(setScan)
            .catch((err) => setError(err.message))
    }, [id, session])

    const result = scan?.result || {}
    const audit = result.audit || {}
    const credits = result.credits || {}
    const metadata = result.metadata || {}
    const semesters = result.cgpa?.semesters || []
    const courseStatuses = credits.course_statuses || []
    const gradeDist = result.grade_distribution || {}
    const concentration = audit.concentration
    const minor = audit.minor
    const deficiencyEntries = Object.entries(audit.missing_courses || {}).filter(([_, value]) => (
        Array.isArray(value) ? value.length > 0 : Number(value) > 0
    ))

    const requestedLevel = metadata.requested_level
    const sectionOrder = {
        '1': ['level1', 'level2', 'level3'],
        '2': ['level2', 'level1', 'level3'],
        '3': ['level3', 'level1', 'level2'],
        dist: ['level2', 'level1', 'level3'],
        all: ['level3', 'level1', 'level2'],
    }[requestedLevel] || ['level3', 'level1', 'level2']

    if (authLoading) return null
    if (!session) return <Navigate to="/login" />
    if (error) return <div className="pt-32 px-6 text-center text-red-600 text-sm">{error}</div>
    if (!scan) return <div className="pt-32 px-6 text-center text-muted text-sm"><span className="animate-pulse">Loading audit data…</span></div>

    const levelSections = {
        level1: (
            <GlassCard key="level1" className="space-y-6">
                <SectionTitle
                    icon={<ListChecks size={16} weight="thin" className="text-muted" />}
                    title="Level 1"
                    subtitle="Credit tally, waivers, transfer handling, and per-course status."
                />

                <div className="grid gap-4 md:grid-cols-3">
                    <MetricCard label="Credits Earned" value={credits.total_earned ?? 0} />
                    <MetricCard label="Credits Attempted" value={credits.total_attempted ?? 0} />
                    <MetricCard label="Program Credits" value={credits.program_required ?? 0} />
                    <MetricCard label="Elective Credits" value={credits.elective ?? 0} />
                    <MetricCard label="Excluded Credits" value={credits.excluded ?? 0} />
                    <MetricCard label="Waived Credits" value={credits.waived ?? 0} />
                </div>

                {(result.waivers_applied?.length > 0 || result.non_nsu_courses_flagged?.length > 0) && (
                    <div className="grid gap-4 md:grid-cols-2">
                        <div>
                            <p className="mb-2 text-xs uppercase tracking-widest text-muted">Waivers Applied</p>
                            {result.waivers_applied?.length ? (
                                <div className="flex flex-wrap gap-2">
                                    {result.waivers_applied.map((item) => (
                                        <span key={item} className="rounded-md border border-black/10 bg-black/5 px-3 py-1 text-sm text-foreground">{item}</span>
                                    ))}
                                </div>
                            ) : <p className="text-sm text-muted">No waivers applied.</p>}
                        </div>
                        <div>
                            <p className="mb-2 text-xs uppercase tracking-widest text-muted">Transfer / Non-NSU Flags</p>
                            {result.non_nsu_courses_flagged?.length ? (
                                <div className="flex flex-wrap gap-2">
                                    {result.non_nsu_courses_flagged.map((item) => (
                                        <span key={item} className="rounded-md border border-amber-200 bg-amber-50 px-3 py-1 text-sm text-amber-800">{item}</span>
                                    ))}
                                </div>
                            ) : <p className="text-sm text-muted">No transfer flags.</p>}
                        </div>
                    </div>
                )}

                <DataTable
                    columns={[
                        { key: 'course_code', label: 'Course' },
                        { key: 'credits', label: 'Credits' },
                        { key: 'grade', label: 'Grade' },
                        { key: 'semester', label: 'Semester' },
                        { key: 'status', label: 'Status' },
                        { key: 'bucket', label: 'Bucket' },
                    ]}
                    rows={courseStatuses}
                    emptyLabel="No course status records available."
                />
            </GlassCard>
        ),
        level2: (
            <GlassCard key="level2" className="space-y-6">
                <SectionTitle
                    icon={<ChartBar size={16} weight="thin" className="text-muted" />}
                    title="Level 2"
                    subtitle="Semester progression, probation tracking, and grade distribution."
                />

                <div className="grid gap-4 md:grid-cols-3">
                    <MetricCard label="Final CGPA" value={(result.cgpa?.final ?? 0).toFixed(3)} />
                    <MetricCard label="Semesters" value={semesters.length} />
                    <MetricCard label="Requested Mode" value={levelLabel(metadata.requested_level || 'all')} />
                </div>

                <div className="space-y-4">
                    {semesters.map((semester) => (
                        <div key={semester.semester} className="rounded-xl border border-black/8 bg-white/40 p-5">
                            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                                <div>
                                    <h3 className="text-lg font-medium text-foreground">{semester.semester}</h3>
                                    <p className="text-sm text-muted">TGPA {semester.tgpa.toFixed(3)} · Cumulative {semester.cumulative_cgpa.toFixed(3)}</p>
                                </div>
                                <span className="rounded-full border border-black/10 bg-black/5 px-3 py-1 text-xs font-medium uppercase tracking-wider text-muted">
                                    {semester.probation_status}
                                </span>
                            </div>
                            <DataTable
                                columns={[
                                    { key: 'course_code', label: 'Course' },
                                    { key: 'credits', label: 'Credits' },
                                    { key: 'grade', label: 'Grade' },
                                    { key: 'status', label: 'Status' },
                                ]}
                                rows={semester.courses || []}
                            />
                        </div>
                    ))}
                </div>

                <div className="rounded-xl border border-black/8 bg-white/40 p-5">
                    <p className="mb-4 text-xs uppercase tracking-widest text-muted">Grade Distribution</p>
                    {Object.keys(gradeDist).length === 0 ? (
                        <p className="text-sm text-muted">No grades recorded.</p>
                    ) : (
                        <div className="space-y-3">
                            {Object.entries(gradeDist).map(([grade, count]) => (
                                <div key={grade} className="flex items-center gap-3">
                                    <span className="w-8 text-sm font-medium text-foreground/70">{grade}</span>
                                    <div className="h-2 flex-1 overflow-hidden rounded-full bg-black/6">
                                        <div
                                            className="h-full rounded-full bg-foreground/50"
                                            style={{ width: `${(count / Math.max(...Object.values(gradeDist))) * 100}%` }}
                                        />
                                    </div>
                                    <span className="text-xs text-muted">{count}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </GlassCard>
        ),
        level3: (
            <GlassCard key="level3" className="space-y-6">
                <SectionTitle
                    icon={<MedalMilitary size={16} weight="thin" className="text-muted" />}
                    title="Level 3"
                    subtitle="Graduation eligibility, deficiencies, roadmap, prerequisites, and concentration/minor outcomes."
                />

                <div className={`rounded-xl border px-5 py-4 ${audit.eligible ? 'border-green-200 bg-green-50/70' : 'border-red-200 bg-red-50/70'}`}>
                    <p className={`text-sm font-medium ${audit.eligible ? 'text-green-700' : 'text-red-700'}`}>
                        {audit.eligible ? 'Eligible for graduation' : 'Not eligible for graduation'}
                    </p>
                    {audit.reasons?.length > 0 && (
                        <div className="mt-3 space-y-2">
                            {audit.reasons.map((reason) => (
                                <div key={reason} className="flex items-start gap-2 text-sm text-foreground/80">
                                    <WarningCircle size={14} weight="fill" className="mt-0.5 shrink-0 text-red-500" />
                                    <span>{reason}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                    {concentration && (
                        <div className="rounded-xl border border-black/8 bg-white/40 p-5">
                            <p className="mb-2 text-xs uppercase tracking-widest text-muted">Concentration</p>
                            <h3 className="text-xl font-display text-foreground">{concentration.name}</h3>
                            <p className="mt-2 text-sm text-muted">
                                CGPA {concentration.cgpa.toFixed(3)}
                                {concentration.minimum_cgpa ? ` · minimum ${concentration.minimum_cgpa.toFixed(2)}` : ''}
                            </p>
                        </div>
                    )}
                    {minor && (
                        <div className="rounded-xl border border-black/8 bg-white/40 p-5">
                            <p className="mb-2 text-xs uppercase tracking-widest text-muted">Minor</p>
                            <h3 className="text-xl font-display text-foreground">{minor.name}</h3>
                            <p className="mt-2 text-sm text-muted">{minor.completed ? 'Completed' : 'In progress'}</p>
                        </div>
                    )}
                </div>

                <div className="grid gap-5 lg:grid-cols-2">
                    <div className="rounded-xl border border-black/8 bg-white/40 p-5">
                        <p className="mb-4 text-xs uppercase tracking-widest text-muted">Graduation Roadmap</p>
                        {audit.roadmap?.length ? (
                            <div className="space-y-3">
                                {audit.roadmap.map((step, index) => (
                                    <div key={step} className="border-l-2 border-foreground/20 pl-4">
                                        <p className="text-xs uppercase tracking-widest text-muted">Step {index + 1}</p>
                                        <p className="text-sm text-foreground/80">{step}</p>
                                    </div>
                                ))}
                            </div>
                        ) : <p className="text-sm text-muted">No roadmap items.</p>}
                    </div>

                    <div className="rounded-xl border border-black/8 bg-white/40 p-5">
                        <p className="mb-4 text-xs uppercase tracking-widest text-muted">Deficiencies</p>
                        {deficiencyEntries.length ? (
                            <div className="space-y-3">
                                {deficiencyEntries.map(([key, value]) => (
                                    <div key={key}>
                                        <p className="mb-1 text-xs uppercase tracking-widest text-muted">{key.replaceAll('_', ' ')}</p>
                                        {Array.isArray(value) ? (
                                            <div className="flex flex-wrap gap-2">
                                                {value.map((item) => (
                                                    <span key={item} className="rounded-md border border-black/10 bg-black/5 px-2.5 py-1 text-sm text-foreground">{item}</span>
                                                ))}
                                            </div>
                                        ) : (
                                            <p className="text-sm text-foreground/80">{value}</p>
                                        )}
                                    </div>
                                ))}
                            </div>
                        ) : <p className="text-sm text-muted">No outstanding deficiencies.</p>}
                    </div>
                </div>

                <DataTable
                    columns={[
                        { key: 'course', label: 'Course' },
                        { key: 'semester', label: 'Semester' },
                        {
                            key: 'missing_prereqs',
                            label: 'Missing Prereqs',
                            render: (row) => row.missing_prereqs?.join(', ') || '—',
                        },
                        { key: 'violation_type', label: 'Type' },
                    ]}
                    rows={audit.prerequisite_violations || []}
                    emptyLabel="No prerequisite violations."
                />

                {audit.failed_courses?.length > 0 && (
                    <div className="rounded-xl border border-red-200 bg-red-50/60 p-5">
                        <p className="mb-3 text-xs uppercase tracking-widest text-red-700">Failed Courses</p>
                        <div className="flex flex-wrap gap-2">
                            {audit.failed_courses.map((course) => (
                                <span key={course} className="rounded-md border border-red-200 bg-red-100 px-3 py-1 text-sm text-red-700">{course}</span>
                            ))}
                        </div>
                    </div>
                )}
            </GlassCard>
        ),
    }

    return (
        <div className="min-h-screen bg-background px-6 pb-24 pt-28 lg:px-12">
            <div className="mx-auto w-full max-w-6xl">
                <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
                    <div>
                        <div className="mb-2 flex items-center gap-2">
                            <MedalMilitary size={14} weight="thin" className="text-muted" />
                            <span className="text-xs font-medium uppercase tracking-widest text-muted">Degree Audit</span>
                        </div>
                        <h1 className="text-4xl font-display text-foreground">Results</h1>
                        <p className="mt-1 text-sm text-muted">{result.program || scan.program}</p>
                    </div>
                    <div className="flex gap-2">
                        <Link to="/history"><Button variant="ghost" className="inline-flex h-8 items-center gap-1.5 px-3 text-xs"><ClockCounterClockwise size={13} weight="regular" />History</Button></Link>
                        <Link to="/dashboard"><Button variant="glass" className="inline-flex h-8 items-center gap-1.5 px-3 text-xs"><Plus size={13} weight="bold" />New Audit</Button></Link>
                    </div>
                </div>

                <div className="mb-8 grid gap-5 lg:grid-cols-4">
                    <MetricCard label="Status" value={audit.eligible ? 'ELIGIBLE' : 'DEFICIENT'} accent={audit.eligible ? 'border-t-4 border-t-green-500' : 'border-t-4 border-t-red-500'} />
                    <MetricCard label="Credits" value={`${audit.credits_completed || 0} / ${audit.credits_required || 0}`} />
                    <MetricCard label="Final CGPA" value={(result.cgpa?.final || 0).toFixed(3)} />
                    <MetricCard label="Major CGPA" value={audit.major_cgpa ? audit.major_cgpa.toFixed(3) : '—'} />
                </div>

                <GlassCard className="mb-8">
                    <div className="flex flex-wrap items-center gap-2 text-xs text-muted">
                        <span className="rounded-full border border-black/10 bg-black/5 px-3 py-1 uppercase tracking-widest">
                            {levelLabel(metadata.requested_level || 'all')}
                        </span>
                        <span>{scan.input_type?.toUpperCase() || 'CSV'}</span>
                        {scan.file_name && <span>· {scan.file_name}</span>}
                        {scan.created_at && <span>· {formatDate(scan.created_at)}</span>}
                        {metadata.report_mode && <span>· {metadata.report_mode} report</span>}
                    </div>
                </GlassCard>

                <div className="space-y-6">
                    {sectionOrder.map((sectionKey) => levelSections[sectionKey])}
                </div>
            </div>
        </div>
    )
}
