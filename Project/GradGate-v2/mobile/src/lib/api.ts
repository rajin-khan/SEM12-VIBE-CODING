import Constants from 'expo-constants'
import { Platform } from 'react-native'
import { Session } from '@supabase/supabase-js'

const CONFIGURED_API_URL = process.env.EXPO_PUBLIC_API_URL?.trim()
const DEFAULT_API_URL = 'http://localhost:8000'
const IOS_SIMULATOR_API_URL = 'http://127.0.0.1:8000'
const ANDROID_EMULATOR_API_URL = 'http://10.0.2.2:8000'

export interface PickedTranscriptFile {
  uri: string
  name: string
  type: string
}

export interface AuditFormState {
  file: PickedTranscriptFile
  program: string
  level: string
  report: string
  concentration: string
  minor: string
  waivers: string[]
}

export const SCANNED_EXTENSIONS = ['.pdf', '.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp', '.webp', '.heic', '.heif', '.gif']

function isIosSimulator() {
  return Platform.OS === 'ios' && !Constants.isDevice
}

function isAndroidEmulator() {
  return Platform.OS === 'android' && !Constants.isDevice
}

function apiCandidates() {
  const candidates: string[] = []

  if (isIosSimulator()) {
    candidates.push(IOS_SIMULATOR_API_URL)
  } else if (isAndroidEmulator()) {
    candidates.push(ANDROID_EMULATOR_API_URL)
  }

  if (CONFIGURED_API_URL && !candidates.includes(CONFIGURED_API_URL)) {
    candidates.push(CONFIGURED_API_URL)
  }

  if (!candidates.length) {
    candidates.push(DEFAULT_API_URL)
  }

  return candidates
}

function authHeaders(session?: Session) {
  if (!session) {
    return {}
  }
  return { Authorization: `Bearer ${session.access_token}` } as Record<string, string>
}

async function parseResponse(response: Response) {
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    const detail = data?.detail
    const structuredMessage = typeof detail === 'object' && detail !== null
      ? [detail.message, ...(detail.ocr_status?.messages || [])].filter(Boolean).join(' ')
      : ''
    const message = Array.isArray(detail)
      ? detail.map((item: any) => item.msg || item).join(', ')
      : typeof detail === 'object' && detail !== null
        ? structuredMessage || JSON.stringify(detail)
        : detail || data?.message || 'Request failed'
    throw new Error(message)
  }
  return data
}

async function performRequest(
  path: string,
  init: RequestInit = {},
  { requiresAuth = false }: { requiresAuth?: boolean } = {},
) {
  let lastNetworkError: unknown = null

  for (const baseUrl of apiCandidates()) {
    try {
      const response = await fetch(`${baseUrl}${path}`, init)
      return await parseResponse(response)
    } catch (error: any) {
      const isNetworkError =
        error instanceof TypeError &&
        /Network request failed/i.test(error.message || '')

      if (!isNetworkError) {
        throw error
      }

      lastNetworkError = error
    }
  }

  const authSuffix = requiresAuth ? ' after signing in' : ''
  throw new Error(
    `Cannot reach the GradGate API${authSuffix}. ` +
      `Start the local API on port 8000 and use localhost for Simulator or EXPO_PUBLIC_API_URL for a device.`
  )
}

function buildAuditFormData(formState: AuditFormState) {
  const formData = new FormData()
  formData.append('file', {
    uri: formState.file.uri,
    name: formState.file.name,
    type: formState.file.type,
  } as any)
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

export async function fetchApiHealth() {
  return performRequest('/health')
}

export async function fetchAuditOptions() {
  return performRequest('/audit/options')
}

export async function fetchOcrStatus() {
  return performRequest('/audit/ocr-status')
}

export async function runCsvAudit(session: Session, formState: AuditFormState) {
  const formData = buildAuditFormData(formState)
  return performRequest('/audit/csv', {
    method: 'POST',
    headers: authHeaders(session),
    body: formData,
  }, { requiresAuth: true })
}

export async function runScannedAudit(session: Session, formState: AuditFormState) {
  const formData = buildAuditFormData(formState)
  return performRequest('/audit/image', {
    method: 'POST',
    headers: authHeaders(session),
    body: formData,
  }, { requiresAuth: true })
}

export async function runTranscriptAudit(session: Session, formState: AuditFormState) {
  const name = formState.file?.name?.toLowerCase() || ''
  if (name.endsWith('.csv')) {
    return runCsvAudit(session, formState)
  }
  return runScannedAudit(session, formState)
}

export async function submitReviewedAudit(session: Session, payload: Record<string, any>) {
  return performRequest('/audit/review', {
    method: 'POST',
    headers: {
      ...authHeaders(session),
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  }, { requiresAuth: true })
}

export async function fetchHistory(session: Session) {
  return performRequest('/history', {
    headers: authHeaders(session),
  }, { requiresAuth: true })
}

export async function fetchResult(session: Session, id: string) {
  return performRequest(`/history/${id}`, {
    headers: authHeaders(session),
  }, { requiresAuth: true })
}
