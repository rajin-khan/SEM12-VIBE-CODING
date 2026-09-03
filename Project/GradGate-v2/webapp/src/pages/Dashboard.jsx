import { useEffect, useMemo, useRef, useState } from 'react'
import { useAuth } from '../lib/AuthContext'
import { Navigate, useNavigate } from 'react-router-dom'
import { GlassCard } from '../components/ui/GlassCard'
import { Button } from '../components/ui/Button'
import { CaretDown, FileCsv, FileImage, SlidersHorizontal, UploadSimple, X } from '@phosphor-icons/react'
import { defaultAuditOptions, levelLabel } from '../lib/auditConfig'
import { SCANNED_EXTENSIONS, fetchAuditOptions, fetchOcrStatus, runTranscriptAudit, submitReviewedAudit } from '../lib/api'
import emblem from '../assets/brand/gradgate-emblem-ui.png'

function WaiverInput({ waivers, setWaivers, disabled }) {
    const [value, setValue] = useState('')

    const commit = () => {
        const next = value
            .split(',')
            .map((item) => item.trim().toUpperCase())
            .filter(Boolean)
        if (next.length) {
            setWaivers((prev) => Array.from(new Set([...prev, ...next])))
        }
        setValue('')
    }

    return (
        <div className="flex flex-col gap-3">
            <div className="flex flex-wrap gap-2 min-h-11 rounded-lg border border-black/10 bg-white/60 p-3">
                {waivers.map((waiver) => (
                    <span
                        key={waiver}
                        className="inline-flex items-center gap-1 rounded-md border border-black/10 bg-black/5 px-2.5 py-1 text-xs font-medium text-foreground"
                    >
                        {waiver}
                        <button
                            type="button"
                            onClick={() => setWaivers((prev) => prev.filter((item) => item !== waiver))}
                            disabled={disabled}
                            className="text-muted hover:text-foreground"
                        >
                            <X size={10} weight="bold" />
                        </button>
                    </span>
                ))}
                <input
                    value={value}
                    onChange={(event) => setValue(event.target.value.toUpperCase())}
                    onBlur={commit}
                    onKeyDown={(event) => {
                        if (event.key === 'Enter' || event.key === ',') {
                            event.preventDefault()
                            commit()
                        }
                        if (event.key === 'Backspace' && !value && waivers.length) {
                            setWaivers((prev) => prev.slice(0, -1))
                        }
                    }}
                    disabled={disabled}
                    className="min-w-32 flex-1 bg-transparent text-sm outline-none placeholder:text-muted"
                    placeholder="Type course code and press Enter"
                />
            </div>
            <p className="text-xs text-muted">Example: `ENG102`, `MAT112`, `BUS112`</p>
        </div>
    )
}

export default function Dashboard() {
    const { session, loading } = useAuth()
    const navigate = useNavigate()
    const fileInputRef = useRef(null)

    const [file, setFile] = useState(null)
    const [program, setProgram] = useState('CSE')
    const [level, setLevel] = useState('all')
    const [report, setReport] = useState('normal')
    const [concentration, setConcentration] = useState('')
    const [minor, setMinor] = useState('')
    const [waivers, setWaivers] = useState([])
    const [showAdvanced, setShowAdvanced] = useState(false)
    const [isUploading, setIsUploading] = useState(false)
    const [error, setError] = useState('')
    const [isDragging, setIsDragging] = useState(false)
    const [auditOptions, setAuditOptions] = useState(defaultAuditOptions())
    const [ocrStatus, setOcrStatus] = useState(null)
    const [reviewPayload, setReviewPayload] = useState(null)

    useEffect(() => {
        let active = true
        fetchAuditOptions()
            .then((data) => {
                if (!active) return
                setAuditOptions(data)
                if (data.programs?.length) {
                    setProgram((current) =>
                        data.programs.some((item) => item.value === current) ? current : data.programs[0].value
                    )
                }
            })
            .catch(() => {})
        fetchOcrStatus()
            .then((data) => {
                if (!active) return
                setOcrStatus(data)
            })
            .catch(() => {})
        return () => {
            active = false
        }
    }, [])

    const selectedProgram = useMemo(
        () => auditOptions.programs.find((item) => item.value === program),
        [auditOptions.programs, program],
    )

    const supportsMinor = Boolean(selectedProgram?.supports_minor)
    const waivableCourses = selectedProgram?.waivable_courses || []
    const isCsv = file?.name?.toLowerCase().endsWith('.csv')
    const isScannedDocument = Boolean(file) && !isCsv
    const canChooseReport = level === '3' || level === 'all'
    const showMinor = supportsMinor
    const showConcentration = program === 'BBA'

    useEffect(() => {
        if (!canChooseReport) setReport('normal')
    }, [canChooseReport])

    useEffect(() => {
        if (!showConcentration) setConcentration('')
        if (!showMinor) setMinor('')
        setWaivers((prev) => prev.filter((item) => waivableCourses.includes(item)))
    }, [showConcentration, showMinor, waivableCourses])

    if (loading) {
        return <div className="min-h-screen grid place-items-center bg-background"><p className="text-muted text-sm">Loading...</p></div>
    }
    if (!session) return <Navigate to="/login" />

    const handleFileDrop = (event) => {
        event.preventDefault()
        setIsDragging(false)
        const selected = event.dataTransfer.files?.[0]
        if (selected) {
            setFile(selected)
            setError('')
        }
    }

    const handleFileSelect = (event) => {
        const selected = event.target.files?.[0]
        if (selected) {
            setFile(selected)
            setError('')
        }
    }

    const fileIcon = !file
        ? <UploadSimple size={32} weight="thin" className="text-muted" />
        : isCsv
            ? <FileCsv size={32} weight="thin" className="text-green-600" />
            : <FileImage size={32} weight="thin" className="text-blue-500" />

    const submitLabel = level === 'all' ? 'Run Complete Degree Audit' : `Run ${levelLabel(level)}`

    const handleScan = async () => {
        if (!file) {
            setError('Please select a transcript first.')
            return
        }
        setError('')
        setReviewPayload(null)
        setIsUploading(true)
        try {
            const data = await runTranscriptAudit(session, {
                file,
                program,
                level,
                report,
                concentration,
                minor,
                waivers,
            })
            if (data.status === 'review_required') {
                setReviewPayload(data.review)
                return
            }
            navigate(`/results/${data.scan_id}`)
        } catch (err) {
            setError(err.message)
        } finally {
            setIsUploading(false)
        }
    }

    const handleReviewedSubmit = async () => {
        if (!reviewPayload || !file) return
        setError('')
        setIsUploading(true)
        try {
            const data = await submitReviewedAudit(session, {
                program,
                input_type: reviewPayload.input_type,
                file_name: file.name,
                extracted_csv: reviewPayload.extracted_csv,
                waivers,
                level,
                report,
                concentration: concentration || null,
                minor: minor || null,
                extraction_mode: reviewPayload.extraction_mode,
                warnings: reviewPayload.warnings || [],
            })
            navigate(`/results/${data.scan_id}`)
        } catch (err) {
            setError(err.message)
        } finally {
            setIsUploading(false)
        }
    }

    return (
        <div className="min-h-screen pt-28 px-6 flex flex-col items-center pb-24 bg-background">
            <div className="w-full max-w-3xl">
                <div className="paper-hero mb-10 overflow-hidden rounded-[2rem] border border-black/8 p-6 shadow-2xl shadow-black/5 md:p-8">
                    <div className="flex items-center gap-2 mb-5">
                        <img src={emblem} alt="" className="h-9 w-9 rounded-xl object-cover ring-1 ring-black/5" />
                        <span className="text-xs uppercase tracking-widest text-muted font-medium">New Audit</span>
                    </div>
                    <h1 className="text-4xl font-display text-foreground">Start a Degree Audit</h1>
                    <p className="text-muted text-sm mt-1 max-w-md">Run the same audit logic as the CLI with CSV, PDF, and transcript image uploads.</p>
                </div>

                <GlassCard className="flex flex-col gap-8 shadow-xl shadow-black/6">
                    {error && (
                        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                            {error}
                        </div>
                    )}

                    <div
                        className={`border-2 border-dashed rounded-xl p-14 flex flex-col items-center justify-center cursor-pointer transition-all group ${
                            isDragging
                                ? 'border-foreground/30 bg-black/5'
                                : 'border-black/10 hover:border-black/20 hover:bg-black/3'
                        }`}
                        onDragOver={(event) => {
                            event.preventDefault()
                            setIsDragging(true)
                        }}
                        onDragLeave={() => setIsDragging(false)}
                        onDrop={handleFileDrop}
                        onClick={() => fileInputRef.current?.click()}
                    >
                        <input
                            type="file"
                            ref={fileInputRef}
                            className="hidden"
                            onChange={handleFileSelect}
                            accept={`.csv,${SCANNED_EXTENSIONS.join(',')}`}
                        />
                        <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full border border-black/10 bg-white/70 shadow-sm transition-transform group-hover:scale-105">
                            {fileIcon}
                        </div>
                        <p className="text-center text-base font-medium text-foreground">
                            {file ? file.name : 'Click or drag your transcript here'}
                        </p>
                        <p className="mt-2 text-center text-xs text-muted">CSV, PDF, and transcript image uploads are supported through the API.</p>
                    </div>

                    {ocrStatus && !ocrStatus.ready && (
                        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                            OCR/PDF support is not fully ready on this API host yet. {ocrStatus.messages?.[0]}
                        </div>
                    )}

                    {reviewPayload && (
                        <div className="rounded-xl border border-amber-200 bg-amber-50/80 p-5">
                            <p className="text-xs font-medium uppercase tracking-widest text-amber-800">Review Required</p>
                            <div className="mt-3 space-y-2 text-sm text-amber-900">
                                {(reviewPayload.warnings || []).map((warning) => (
                                    <p key={warning}>{warning}</p>
                                ))}
                            </div>
                            <div className="mt-4 overflow-auto rounded-xl border border-amber-200 bg-white/70">
                                <table className="min-w-full divide-y divide-amber-100 text-sm">
                                    <thead className="bg-amber-50 text-left text-xs uppercase tracking-widest text-amber-700">
                                        <tr>
                                            <th className="px-4 py-3 font-medium">Course</th>
                                            <th className="px-4 py-3 font-medium">Credits</th>
                                            <th className="px-4 py-3 font-medium">Grade</th>
                                            <th className="px-4 py-3 font-medium">Semester</th>
                                            <th className="px-4 py-3 font-medium">Confidence</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-amber-100">
                                        {(reviewPayload.extracted_preview_rows || []).map((row, index) => (
                                            <tr key={`${row.course_code}-${index}`}>
                                                <td className="px-4 py-3">{row.course_code}</td>
                                                <td className="px-4 py-3">{row.credits}</td>
                                                <td className="px-4 py-3">{row.grade}</td>
                                                <td className="px-4 py-3">{row.semester}</td>
                                                <td className="px-4 py-3">{Number(row.confidence || 0).toFixed(2)}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                            <div className="mt-4 flex flex-wrap gap-3">
                                <Button onClick={handleReviewedSubmit} disabled={isUploading}>
                                    Run Audit With Extracted Rows
                                </Button>
                                <Button variant="ghost" onClick={() => setReviewPayload(null)} disabled={isUploading}>
                                    Cancel Review
                                </Button>
                            </div>
                        </div>
                    )}

                    <div className="grid gap-5 md:grid-cols-2">
                        <div className="flex flex-col gap-2">
                            <label className="pl-1 text-xs font-medium uppercase tracking-widest text-muted">Target Program</label>
                            <select
                                value={program}
                                onChange={(event) => setProgram(event.target.value)}
                                className="rounded-lg border border-black/10 bg-white/60 p-4 text-sm font-medium text-foreground outline-none focus:border-black/25"
                            >
                                {auditOptions.programs.map((item) => (
                                    <option key={item.value} value={item.value}>{item.label}</option>
                                ))}
                            </select>
                        </div>

                        <div className="flex flex-col gap-2">
                            <label className="pl-1 text-xs font-medium uppercase tracking-widest text-muted">Audit Mode</label>
                            <select
                                value={level}
                                onChange={(event) => setLevel(event.target.value)}
                                className="rounded-lg border border-black/10 bg-white/60 p-4 text-sm font-medium text-foreground outline-none focus:border-black/25"
                            >
                                {auditOptions.levels.map((item) => (
                                    <option key={item.value} value={item.value}>
                                        {item.value === 'all' ? 'Full Audit' : item.label}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>

                    <div className="rounded-xl border border-black/10 bg-white/40">
                        <button
                            type="button"
                            onClick={() => setShowAdvanced((value) => !value)}
                            className="flex w-full items-center justify-between px-5 py-4 text-left"
                        >
                            <div className="flex items-center gap-2">
                                <SlidersHorizontal size={16} weight="thin" className="text-muted" />
                                <span className="text-sm font-medium text-foreground">Advanced Options</span>
                            </div>
                            <CaretDown
                                size={14}
                                weight="bold"
                                className={`text-muted transition-transform ${showAdvanced ? 'rotate-180' : ''}`}
                            />
                        </button>

                        {showAdvanced && (
                            <div className="grid gap-5 border-t border-black/8 px-5 py-5">
                                {canChooseReport && (
                                    <div className="flex flex-col gap-2">
                                        <label className="text-xs font-medium uppercase tracking-widest text-muted">Report Verbosity</label>
                                        <select
                                            value={report}
                                            onChange={(event) => setReport(event.target.value)}
                                            className="rounded-lg border border-black/10 bg-white/60 p-4 text-sm font-medium text-foreground outline-none focus:border-black/25"
                                        >
                                            {auditOptions.report_modes.map((mode) => (
                                                <option key={mode} value={mode}>{mode === 'full' ? 'Full' : 'Normal'}</option>
                                            ))}
                                        </select>
                                    </div>
                                )}

                                <div className="flex flex-col gap-2">
                                    <label className="text-xs font-medium uppercase tracking-widest text-muted">Waivers</label>
                                    <WaiverInput waivers={waivers} setWaivers={setWaivers} disabled={isUploading} />
                                    {waivableCourses.length > 0 && (
                                        <p className="text-xs text-muted">
                                            Known waivable courses for {program}: {waivableCourses.join(', ')}
                                        </p>
                                    )}
                                </div>

                                {showConcentration && (
                                    <div className="flex flex-col gap-2">
                                        <label className="text-xs font-medium uppercase tracking-widest text-muted">BBA Concentration</label>
                                        <select
                                            value={concentration}
                                            onChange={(event) => setConcentration(event.target.value)}
                                            className="rounded-lg border border-black/10 bg-white/60 p-4 text-sm font-medium text-foreground outline-none focus:border-black/25"
                                        >
                                            <option value="">Auto-detect</option>
                                            {auditOptions.bba_concentrations.map((item) => (
                                                <option key={item.value} value={item.value}>{item.label}</option>
                                            ))}
                                        </select>
                                    </div>
                                )}

                                {showMinor && (
                                    <div className="flex flex-col gap-2">
                                        <label className="text-xs font-medium uppercase tracking-widest text-muted">Minor</label>
                                        <select
                                            value={minor}
                                            onChange={(event) => setMinor(event.target.value)}
                                            className="rounded-lg border border-black/10 bg-white/60 p-4 text-sm font-medium text-foreground outline-none focus:border-black/25"
                                        >
                                            <option value="">None</option>
                                            {auditOptions.supported_minors.map((item) => (
                                                <option key={item} value={item}>{item}</option>
                                            ))}
                                        </select>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    <Button
                        onClick={handleScan}
                        disabled={!file || isUploading}
                        className="h-14 w-full text-base font-semibold"
                    >
                        {isUploading ? (isScannedDocument ? 'Extracting Transcript…' : 'Running Audit…') : submitLabel}
                    </Button>
                </GlassCard>
            </div>
        </div>
    )
}
