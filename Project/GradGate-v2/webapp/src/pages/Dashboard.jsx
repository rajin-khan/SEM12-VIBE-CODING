import { useState, useRef } from 'react'
import { useAuth } from '../lib/AuthContext'
import { Navigate, useNavigate } from 'react-router-dom'
import { GlassCard } from '../components/ui/GlassCard'
import { Button } from '../components/ui/Button'
import { UploadSimple, FileCsv, FileImage, Cpu } from '@phosphor-icons/react'

const PROGRAMS = [
    { value: "CSE", label: "Computer Science & Engineering (B.Sc)" },
    { value: "BBA", label: "Business Administration (BBA)" },
    { value: "EEE", label: "Electrical & Electronic Engineering (B.Sc)" },
    { value: "ETE", label: "Electronics & Telecommunication Engineering (B.Sc)" },
]

export default function Dashboard() {
    const { session, loading } = useAuth()
    const [file, setFile] = useState(null)
    const [program, setProgram] = useState("CSE")
    const [isUploading, setIsUploading] = useState(false)
    const [error, setError] = useState("")
    const [isDragging, setIsDragging] = useState(false)
    const fileInputRef = useRef(null)
    const navigate = useNavigate()

    if (loading) return <div className="min-h-screen grid place-items-center bg-background"><p className="text-muted text-sm">Loading...</p></div>
    if (!session) return <Navigate to="/login" />

    const handleFileDrop = (e) => {
        e.preventDefault()
        setIsDragging(false)
        if (e.dataTransfer.files && e.dataTransfer.files[0]) setFile(e.dataTransfer.files[0])
    }
    const handleFileSelect = (e) => {
        if (e.target.files && e.target.files[0]) setFile(e.target.files[0])
    }

    const getFileIcon = () => {
        if (!file) return <UploadSimple size={32} weight="thin" className="text-muted" />
        if (file.name.endsWith('.csv')) return <FileCsv size={32} weight="thin" className="text-green-600" />
        return <FileImage size={32} weight="thin" className="text-blue-500" />
    }

    const handleScan = async () => {
        if (!file) { setError("Please select a file first."); return }
        setError("")
        setIsUploading(true)
        try {
            const formData = new FormData()
            formData.append("file", file)
            formData.append("program", program)

            const endpoint = file.name.toLowerCase().endsWith('.csv') ? '/audit/csv' : '/audit/image'
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'

            const response = await fetch(`${apiUrl}${endpoint}`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${session.access_token}` },
                body: formData
            })

            const data = await response.json()
            if (!response.ok) {
                const errMsg = Array.isArray(data.detail)
                    ? data.detail.map(d => d.msg).join(", ")
                    : (data.detail || data.message || "Audit failed")
                throw new Error(errMsg)
            }

            navigate(`/results/${data.scan_id}`)
        } catch (err) {
            setError(err.message)
        } finally {
            setIsUploading(false)
        }
    }

    return (
        <div className="min-h-screen pt-28 px-6 flex flex-col items-center pb-24 bg-background">
            <div className="w-full max-w-2xl">
                <div className="mb-10">
                    <div className="flex items-center gap-2 mb-2">
                        <Cpu size={14} weight="thin" className="text-muted" />
                        <span className="text-xs uppercase tracking-widest text-muted font-medium">New Audit</span>
                    </div>
                    <h1 className="text-4xl font-display text-foreground">Upload Transcript</h1>
                    <p className="text-muted text-sm mt-1">Analyze your degree progress instantly.</p>
                </div>

                <GlassCard className="flex flex-col gap-8 shadow-xl shadow-black/6">
                    {error && (
                        <div className="bg-red-50 text-red-700 p-4 rounded-lg text-sm border border-red-200 flex items-start gap-3">
                            <span className="shrink-0 mt-0.5">⚠</span>
                            <span>{error}</span>
                        </div>
                    )}

                    {/* Drop zone */}
                    <div
                        className={`border-2 border-dashed rounded-xl p-14 flex flex-col items-center justify-center cursor-pointer transition-all group
                            ${isDragging
                                ? 'border-foreground/30 bg-black/5'
                                : 'border-black/10 hover:border-black/20 hover:bg-black/3'
                            }`}
                        onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
                        onDragLeave={() => setIsDragging(false)}
                        onDrop={handleFileDrop}
                        onClick={() => fileInputRef.current?.click()}
                    >
                        <input
                            type="file"
                            ref={fileInputRef}
                            className="hidden"
                            onChange={handleFileSelect}
                            accept=".csv,.pdf,.png,.jpg,.jpeg"
                        />
                        <div className="w-16 h-16 rounded-full bg-white/70 border border-black/10 flex items-center justify-center mb-4 group-hover:scale-105 transition-transform shadow-sm">
                            {getFileIcon()}
                        </div>
                        <p className="text-foreground text-base font-medium text-center">
                            {file ? file.name : "Click or drag your transcript here"}
                        </p>
                        <p className="text-muted text-xs mt-2 text-center">CSV, PDF, PNG, or JPG · up to 10 MB</p>
                    </div>

                    {/* Program selector */}
                    <div className="flex flex-col gap-2">
                        <label className="text-xs font-medium text-muted uppercase tracking-widest pl-1">Target Program</label>
                        <select
                            value={program}
                            onChange={(e) => setProgram(e.target.value)}
                            className="bg-white/60 border border-black/10 rounded-lg p-4 text-foreground outline-none focus:border-black/25 appearance-none font-medium text-sm transition-colors"
                        >
                            {PROGRAMS.map(p => (
                                <option key={p.value} value={p.value}>{p.label}</option>
                            ))}
                        </select>
                    </div>

                    {/* Submit */}
                    <Button
                        onClick={handleScan}
                        disabled={!file || isUploading}
                        className="w-full h-14 text-base font-semibold"
                    >
                        {isUploading ? (
                            <span className="flex items-center gap-3">
                                <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                </svg>
                                Running Audit...
                            </span>
                        ) : "Run Complete Degree Audit"}
                    </Button>
                </GlassCard>
            </div>
        </div>
    )
}
