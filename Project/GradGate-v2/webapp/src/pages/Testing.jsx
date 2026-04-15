import { useState, useRef, useCallback } from 'react'
import { Navigate, Link } from 'react-router-dom'
import { useAuth } from '../lib/AuthContext'
import { GlassCard } from '../components/ui/GlassCard'
import { runTranscriptAudit } from '../lib/api'
import {
    FolderOpen, FileCsv, FileImage, ArrowSquareOut,
    Circle, CheckCircle, XCircle, SpinnerGap, Tray
} from '@phosphor-icons/react'

const PROGRAMS = [
    { value: "CSE", label: "CSE" },
    { value: "BBA", label: "BBA" },
    { value: "EEE", label: "EEE" },
    { value: "ETE", label: "ETE" },
]

const ACCEPTED = ['.csv', '.pdf', '.png', '.jpg', '.jpeg']

function statusIcon(status) {
    if (status === 'running') return <SpinnerGap size={16} weight="regular" className="text-muted animate-spin" />
    if (status === 'done') return <CheckCircle size={16} weight="fill" className="text-emerald-500" />
    if (status === 'error') return <XCircle size={16} weight="fill" className="text-red-500" />
    return <Circle size={16} weight="regular" className="text-muted/30" />
}

export default function Testing() {
    const { session, loading } = useAuth()
    const folderInputRef = useRef(null)
    const [files, setFiles] = useState([]) // [{file, program, status, scan_id, error}]

    if (loading) return <div className="min-h-screen grid place-items-center"><p className="text-muted text-sm">Loading...</p></div>
    if (!session) return <Navigate to="/login" />

    const handleFolderSelect = (e) => {
        const selected = Array.from(e.target.files || [])
            .filter(f => ACCEPTED.some(ext => f.name.toLowerCase().endsWith(ext)))
            .map(f => ({ file: f, program: 'CSE', status: 'idle', scan_id: null, error: null }))
        setFiles(prev => {
            // Avoid duplicates by name
            const existingNames = new Set(prev.map(p => p.file.name))
            const newFiles = selected.filter(s => !existingNames.has(s.file.name))
            return [...prev, ...newFiles]
        })
        // Reset input so same folder can be re-selected
        e.target.value = ''
    }

    const setFileField = (index, field, value) => {
        setFiles(prev => prev.map((f, i) => i === index ? { ...f, [field]: value } : f))
    }

    const runAudit = async (index) => {
        const entry = files[index]
        setFileField(index, 'status', 'running')
        setFileField(index, 'error', null)

        try {
            const data = await runTranscriptAudit(session, {
                file: entry.file,
                program: entry.program,
                level: 'all',
                report: 'normal',
                concentration: '',
                minor: '',
                waivers: [],
            })
            setFiles(prev => prev.map((f, i) => i === index
                ? { ...f, status: 'done', scan_id: data.scan_id }
                : f
            ))
        } catch (err) {
            setFiles(prev => prev.map((f, i) => i === index
                ? { ...f, status: 'error', error: err.message }
                : f
            ))
        }
    }

    const runAll = () => {
        files.forEach((f, i) => {
            if (f.status === 'idle' || f.status === 'error') runAudit(i)
        })
    }

    const removeFile = (index) => {
        setFiles(prev => prev.filter((_, i) => i !== index))
    }

    const clearAll = () => setFiles([])

    const doneCount = files.filter(f => f.status === 'done').length
    const errorCount = files.filter(f => f.status === 'error').length
    const runningCount = files.filter(f => f.status === 'running').length

    return (
        <div className="min-h-screen pt-28 px-6 flex flex-col items-center pb-24">
            <div className="w-full max-w-4xl">
                {/* Header */}
                <div className="flex items-center justify-between mb-10">
                    <div>
                        <div className="flex items-center gap-2 mb-2">
                            <Tray size={14} weight="thin" className="text-muted" />
                            <span className="text-xs uppercase tracking-widest text-muted font-medium">Batch Testing</span>
                        </div>
                        <h1 className="text-4xl font-display text-foreground">Testing Suite</h1>
                        <p className="text-muted text-sm mt-1">Upload a folder of transcripts and run audits in bulk.</p>
                    </div>
                    <div className="flex items-center gap-3">
                        {files.length > 0 && (
                            <>
                                <button
                                    onClick={clearAll}
                                    className="text-xs text-muted hover:text-foreground transition-colors px-3 py-2"
                                >
                                    Clear all
                                </button>
                                <button
                                    onClick={runAll}
                                    disabled={runningCount > 0}
                                    className="inline-flex items-center gap-2 bg-white text-black text-sm font-semibold rounded-sm px-5 py-2.5 hover:bg-white/90 transition-colors disabled:opacity-50"
                                >
                                    {runningCount > 0 ? `Running ${runningCount}...` : 'Run All'}
                                </button>
                            </>
                        )}
                    </div>
                </div>

                {/* Folder picker */}
                <GlassCard
                    className="flex flex-col items-center justify-center gap-4 cursor-pointer hover:bg-black/5 transition-colors border-dashed border-2 border-black/10 hover:border-black/20 mb-6 py-12"
                    onClick={() => folderInputRef.current?.click()}
                >
                    <input
                        ref={folderInputRef}
                        type="file"
                        className="hidden"
                        onChange={handleFolderSelect}
                        accept={ACCEPTED.join(',')}
                        multiple
                        // @ts-ignore — webkitdirectory is non-standard but widely supported
                        webkitdirectory=""
                    />
                    <div className="w-14 h-14 rounded-full bg-black/5 border border-black/10 flex items-center justify-center">
                        <FolderOpen size={28} weight="thin" className="text-muted" />
                    </div>
                    <div className="text-center">
                        <p className="text-foreground font-medium">Select a folder of transcripts</p>
                        <p className="text-muted text-xs mt-1">CSV, PDF, PNG, JPG files will be loaded automatically</p>
                    </div>
                </GlassCard>

                {/* Stats bar */}
                {files.length > 0 && (
                    <div className="flex items-center gap-6 mb-4 px-1">
                        <span className="text-xs text-muted">{files.length} file{files.length !== 1 ? 's' : ''} loaded</span>
                        {doneCount > 0 && <span className="text-xs text-emerald-400">{doneCount} completed</span>}
                        {errorCount > 0 && <span className="text-xs text-red-400">{errorCount} failed</span>}
                        {runningCount > 0 && <span className="text-xs text-muted/60">{runningCount} running…</span>}
                    </div>
                )}

                {/* File list */}
                {files.length > 0 && (
                    <div className="flex flex-col gap-2">
                        {files.map((entry, index) => {
                            const isCSV = entry.file.name.toLowerCase().endsWith('.csv')
                            return (
                                <GlassCard
                                    key={entry.file.name + index}
                                    className={`py-4 px-5 transition-all
                                        ${entry.status === 'done' ? 'border-emerald-500/20 bg-emerald-500/5' : ''}
                                        ${entry.status === 'error' ? 'border-red-500/20 bg-red-500/5' : ''}
                                    `}
                                >
                                    <div className="flex items-center gap-4">
                                        {/* Status icon */}
                                        <div className="shrink-0">{statusIcon(entry.status)}</div>

                                        {/* File icon */}
                                        <div className="w-8 h-8 rounded-lg bg-black/5 border border-black/10 flex items-center justify-center shrink-0">
                                            {isCSV
                                                ? <FileCsv size={15} weight="thin" className="text-muted" />
                                                : <FileImage size={15} weight="thin" className="text-muted" />
                                            }
                                        </div>

                                        {/* Filename */}
                                        <div className="flex-1 min-w-0">
                                            <p className="text-foreground text-sm font-medium truncate">{entry.file.name}</p>
                                            {entry.error && (
                                                <p className="text-red-400 text-xs mt-0.5 truncate">{entry.error}</p>
                                            )}
                                        </div>

                                        {/* Program picker */}
                                        <select
                                            value={entry.program}
                                            onChange={(e) => setFileField(index, 'program', e.target.value)}
                                            disabled={entry.status === 'running' || entry.status === 'done'}
                                            className="bg-black/5 border border-black/10 rounded-md px-3 py-1.5 text-foreground text-xs outline-none focus:border-black/30 appearance-none shrink-0 disabled:opacity-40"
                                        >
                                            {PROGRAMS.map(p => (
                                                <option key={p.value} value={p.value}>{p.label}</option>
                                            ))}
                                        </select>

                                        {/* Action button */}
                                        {entry.status === 'done' && entry.scan_id ? (
                                            <Link
                                                to={`/results/${entry.scan_id}`}
                                                className="inline-flex items-center gap-1.5 text-xs font-medium text-muted hover:text-foreground border border-black/10 rounded-md px-3 py-1.5 hover:border-black/20 transition-all shrink-0"
                                            >
                                                View <ArrowSquareOut size={12} weight="regular" />
                                            </Link>
                                        ) : (
                                            <button
                                                onClick={() => runAudit(index)}
                                                disabled={entry.status === 'running'}
                                                className="inline-flex items-center gap-1.5 text-xs font-medium text-black bg-white rounded-md px-3 py-1.5 hover:bg-white/90 transition-all shrink-0 disabled:opacity-40"
                                            >
                                                {entry.status === 'running' ? 'Running…' :
                                                    entry.status === 'error' ? 'Retry' : 'Run'}
                                            </button>
                                        )}

                                        {/* Remove */}
                                        <button
                                            onClick={() => removeFile(index)}
                                            className="text-muted/40 hover:text-foreground transition-colors text-lg leading-none shrink-0 pl-1"
                                            title="Remove"
                                        >
                                            ×
                                        </button>
                                    </div>
                                </GlassCard>
                            )
                        })}
                    </div>
                )}

                {/* Empty state */}
                {files.length === 0 && (
                    <p className="text-center text-muted text-sm mt-4">
                        No files loaded yet. Select a folder above to get started.
                    </p>
                )}
            </div>
        </div>
    )
}
