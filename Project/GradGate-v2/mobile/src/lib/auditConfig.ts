export const FALLBACK_PROGRAMS = [
  { value: 'CSE', label: 'Computer Science & Engineering', waivable_courses: ['ENG102', 'MAT112'], supports_minor: true },
  { value: 'EEE', label: 'Electrical & Electronic Engineering', waivable_courses: [], supports_minor: true },
  { value: 'ETE', label: 'Electronic & Telecom Engineering', waivable_courses: [], supports_minor: true },
  { value: 'CEE', label: 'Civil & Environmental Engineering', waivable_courses: [], supports_minor: true },
  { value: 'ENV', label: 'Environmental Science & Management', waivable_courses: [], supports_minor: false },
  { value: 'ENG', label: 'English', waivable_courses: [], supports_minor: false },
  { value: 'BBA', label: 'Business Administration', waivable_courses: ['ENG102', 'BUS112'], supports_minor: false },
  { value: 'ECO', label: 'Economics', waivable_courses: [], supports_minor: false },
]

export const FALLBACK_LEVELS = [
  { value: 'all', label: 'Full Audit' },
  { value: '1', label: 'Level 1 — Credit Tally' },
  { value: '2', label: 'Level 2 — CGPA & Probation' },
  { value: '3', label: 'Level 3 — Full Audit' },
  { value: 'dist', label: 'Grade Distribution' },
]

export const FALLBACK_REPORT_MODES = ['normal', 'full']
export const FALLBACK_MINORS = ['MATH', 'PHYSICS']
export const FALLBACK_BBA_CONCENTRATIONS = [
  { value: 'ACT', label: 'Accounting' },
  { value: 'FIN', label: 'Finance' },
  { value: 'MKT', label: 'Marketing' },
  { value: 'MGT', label: 'Management' },
  { value: 'HRM', label: 'Human Resource Management' },
  { value: 'MIS', label: 'Management Information Systems' },
  { value: 'INB', label: 'International Business' },
  { value: 'SCM', label: 'Supply Chain Management' },
  { value: 'ECO', label: 'Economics' },
]

export function defaultAuditOptions() {
  return {
    programs: FALLBACK_PROGRAMS,
    levels: FALLBACK_LEVELS,
    report_modes: FALLBACK_REPORT_MODES,
    supported_minors: FALLBACK_MINORS,
    bba_concentrations: FALLBACK_BBA_CONCENTRATIONS,
  }
}

export function levelLabel(level?: string) {
  return FALLBACK_LEVELS.find((item) => item.value === level)?.label ?? level ?? 'Full Audit'
}
