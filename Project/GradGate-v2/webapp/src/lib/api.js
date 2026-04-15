const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function parseResponse(response) {
    const data = await response.json().catch(() => ({}))
    if (!response.ok) {
        const detail = data?.detail
        const structuredDetailMessage = typeof detail === 'object' && detail !== null
            ? [detail.message, ...(detail.ocr_status?.messages || [])].filter(Boolean).join(' ')
            : ''
        const message = Array.isArray(detail)
            ? detail.map((item) => item.msg || item).join(', ')
            : (typeof detail === 'object' && detail !== null)
                ? structuredDetailMessage || JSON.stringify(detail)
                : detail || data?.message || 'Request failed'
        throw new Error(message)
    }
    return data
}

function authHeaders(session, extra = {}) {
    return {
        ...(session ? { Authorization: `Bearer ${session.access_token}` } : {}),
        ...extra,
    }
}

export async function fetchAuditOptions() {
    const response = await fetch(`${API_URL}/audit/options`)
    return parseResponse(response)
}

function buildAuditFormData(formState) {
    const formData = new FormData()
    formData.append('file', formState.file)
    formData.append('program', formState.program)
    formData.append('level', formState.level)

    if (formState.waivers?.length) {
        formData.append('waivers', formState.waivers.join(','))
    }

    if (formState.level === '3' || formState.level === 'all') {
        formData.append('report', formState.report)
    }

    if (formState.program === 'BBA' && formState.concentration) {
        formData.append('concentration', formState.concentration)
    }

    if (formState.minor) {
        formData.append('minor', formState.minor)
    }
    return formData
}

export async function runCsvAudit(session, formState) {
    const formData = buildAuditFormData(formState)
    const response = await fetch(`${API_URL}/audit/csv`, {
        method: 'POST',
        headers: authHeaders(session),
        body: formData,
    })
    return parseResponse(response)
}

export async function runScannedAudit(session, formState) {
    const formData = buildAuditFormData(formState)
    const response = await fetch(`${API_URL}/audit/image`, {
        method: 'POST',
        headers: authHeaders(session),
        body: formData,
    })
    return parseResponse(response)
}

export async function runTranscriptAudit(session, formState) {
    const name = formState.file?.name?.toLowerCase() || ''
    if (name.endsWith('.csv')) {
        return runCsvAudit(session, formState)
    }
    return runScannedAudit(session, formState)
}

export async function fetchOcrStatus() {
    const response = await fetch(`${API_URL}/audit/ocr-status`)
    return parseResponse(response)
}

export async function fetchHistory(session) {
    const response = await fetch(`${API_URL}/history`, {
        headers: authHeaders(session),
    })
    return parseResponse(response)
}

export async function fetchResult(session, id) {
    const response = await fetch(`${API_URL}/history/${id}`, {
        headers: authHeaders(session),
    })
    return parseResponse(response)
}
