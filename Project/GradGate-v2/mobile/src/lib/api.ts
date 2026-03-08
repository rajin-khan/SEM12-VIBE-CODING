import { Session } from '@supabase/supabase-js'

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000'

function authHeaders(session: Session) {
    return { Authorization: `Bearer ${session.access_token}` }
}

export async function auditCSV(session: Session, fileUri: string, fileName: string, program: string) {
    const formData = new FormData()
    formData.append('file', { uri: fileUri, name: fileName, type: 'text/csv' } as any)
    formData.append('program', program)

    const res = await fetch(`${API_URL}/audit/csv`, {
        method: 'POST',
        headers: authHeaders(session),
        body: formData,
    })
    const data = await res.json()
    if (!res.ok) {
        const msg = Array.isArray(data.detail) ? data.detail.map((d: any) => d.msg).join(', ') : data.detail || 'Audit failed'
        throw new Error(msg)
    }
    return data
}

export async function auditImage(session: Session, fileUri: string, fileName: string, mimeType: string, program: string) {
    const formData = new FormData()
    formData.append('file', { uri: fileUri, name: fileName, type: mimeType } as any)
    formData.append('program', program)

    const res = await fetch(`${API_URL}/audit/image`, {
        method: 'POST',
        headers: authHeaders(session),
        body: formData,
    })
    const data = await res.json()
    if (!res.ok) {
        const msg = Array.isArray(data.detail) ? data.detail.map((d: any) => d.msg).join(', ') : data.detail || 'Audit failed'
        throw new Error(msg)
    }
    return data
}

export async function fetchHistory(session: Session) {
    const res = await fetch(`${API_URL}/history`, { headers: authHeaders(session) })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || 'Failed to load history')
    return data
}

export async function fetchResult(session: Session, id: string) {
    const res = await fetch(`${API_URL}/history/${id}`, { headers: authHeaders(session) })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || 'Failed to load result')
    return data
}
