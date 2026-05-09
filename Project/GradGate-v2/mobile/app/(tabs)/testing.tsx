import { useState } from 'react'
import {
  View, Text, ScrollView, StyleSheet, TouchableOpacity, Alert, ActivityIndicator
} from 'react-native'
import { useRouter } from 'expo-router'
import * as DocumentPicker from 'expo-document-picker'
import { Ionicons } from '@expo/vector-icons'
import { useAuth } from '../../src/lib/AuthContext'
import { runTranscriptAudit } from '../../src/lib/api'
import { defaultAuditOptions } from '../../src/lib/auditConfig'
import { Card } from '../../src/components/Card'
import { PrimaryButton } from '../../src/components/PrimaryButton'
import { SectionLabel } from '../../src/components/SectionLabel'
import { colors, fonts, radius } from '../../src/theme'

const PROGRAMS = defaultAuditOptions().programs.map((item) => item.value)

type Status = 'idle' | 'running' | 'done' | 'error'
interface FileEntry {
  id: string
  uri: string
  name: string
  type: string
  program: string
  status: Status
  scanId?: string
  error?: string
}

export default function TestingScreen() {
  const { session } = useAuth()
  const router = useRouter()
  const [files, setFiles] = useState<FileEntry[]>([])
  const [runningAll, setRunningAll] = useState(false)

  const pickFiles = async () => {
    const result = await DocumentPicker.getDocumentAsync({
      type: ['text/csv', 'application/pdf', 'image/*'],
      copyToCacheDirectory: true,
      multiple: true,
    })
    if (!result.canceled && result.assets) {
      const newFiles: FileEntry[] = result.assets.map(a => ({
        id: `${Date.now()}-${Math.random()}`,
        uri: a.uri,
        name: a.name,
        type: a.mimeType || 'text/csv',
        program: 'CSE',
        status: 'idle',
      }))
      setFiles(prev => [...prev, ...newFiles])
    }
  }

  const updateFile = (id: string, patch: Partial<FileEntry>) => {
    setFiles(prev => prev.map(f => f.id === id ? { ...f, ...patch } : f))
  }

  const runOne = async (entry: FileEntry) => {
    if (!session) return
    updateFile(entry.id, { status: 'running' })
    try {
      const isCSV = entry.name.endsWith('.csv') || entry.type === 'text/csv'
      const data = await runTranscriptAudit(session, {
        file: {
          uri: entry.uri,
          name: entry.name,
          type: isCSV ? 'text/csv' : entry.type,
        },
        program: entry.program,
        level: 'all',
        report: 'normal',
        concentration: '',
        minor: '',
        waivers: [],
      })
      if (data.status === 'review_required') {
        throw new Error(data.review?.warnings?.[0] || 'Review required before auditing this document.')
      }
      updateFile(entry.id, { status: 'done', scanId: data.scan_id })
    } catch (e: any) {
      updateFile(entry.id, { status: 'error', error: e.message })
    }
  }

  const runAll = async () => {
    setRunningAll(true)
    const idle = files.filter(f => f.status === 'idle' || f.status === 'error')
    for (const f of idle) await runOne(f)
    setRunningAll(false)
  }

  const stats = {
    total: files.length,
    done: files.filter(f => f.status === 'done').length,
    running: files.filter(f => f.status === 'running').length,
    error: files.filter(f => f.status === 'error').length,
  }

  const statusIcon = (s: Status) => {
    switch (s) {
      case 'running': return <ActivityIndicator size="small" color={colors.foreground} />
      case 'done': return <Ionicons name="checkmark-circle" size={18} color={colors.green} />
      case 'error': return <Ionicons name="alert-circle" size={18} color={colors.red} />
      default: return <Ionicons name="ellipse-outline" size={18} color={colors.muted} />
    }
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
    >
      <View style={styles.header}>
        <SectionLabel>Batch Testing</SectionLabel>
        <Text style={styles.heading}>Testing</Text>
        <Text style={styles.sub}>Upload multiple transcripts and run audits in batch.</Text>
      </View>

      {/* Stats bar */}
      {files.length > 0 && (
        <Card style={styles.statsBar}>
          <StatPill label="Loaded" value={stats.total} />
          <StatPill label="Done" value={stats.done} color={colors.green} />
          <StatPill label="Error" value={stats.error} color={colors.red} />
          <StatPill label="Running" value={stats.running} />
        </Card>
      )}

      {/* Actions */}
      <View style={styles.actions}>
        <PrimaryButton label="+ Add Files" onPress={pickFiles} variant="outline" style={{ flex: 1 }} />
        {files.length > 0 && (
          <>
            <PrimaryButton label="Run All" onPress={runAll} loading={runningAll} style={{ flex: 1 }} />
            <TouchableOpacity style={styles.clearBtn} onPress={() => setFiles([])}>
              <Text style={styles.clearText}>Clear</Text>
            </TouchableOpacity>
          </>
        )}
      </View>

      {/* File list */}
      {files.length === 0 ? (
        <View style={styles.emptyBox}>
          <Ionicons name="flask-outline" size={28} color={colors.muted} />
          <Text style={styles.emptyTitle}>No files loaded</Text>
          <Text style={styles.emptySub}>Tap "Add Files" to load transcripts for batch testing.</Text>
        </View>
      ) : (
        <View style={styles.list}>
          {files.map(entry => (
            <Card key={entry.id} style={styles.fileRow}>
              <View style={styles.fileInfo}>
                {statusIcon(entry.status)}
                <View style={{ flex: 1 }}>
                  <Text style={styles.fileName} numberOfLines={1}>{entry.name}</Text>
                  {entry.error && <Text style={styles.errorMsg} numberOfLines={2}>{entry.error}</Text>}
                </View>
              </View>
              {/* Program chips */}
              <View style={styles.programRow}>
                {PROGRAMS.map(p => (
                  <TouchableOpacity
                    key={p}
                    style={[styles.chip, entry.program === p && styles.chipActive]}
                    onPress={() => updateFile(entry.id, { program: p })}
                  >
                    <Text style={[styles.chipText, entry.program === p && styles.chipTextActive]}>{p}</Text>
                  </TouchableOpacity>
                ))}
              </View>
              <View style={styles.fileActions}>
                {entry.status === 'idle' || entry.status === 'error' ? (
                  <TouchableOpacity style={styles.runBtn} onPress={() => runOne(entry)}>
                    <Text style={styles.runBtnText}>{entry.status === 'error' ? 'Retry' : 'Run'}</Text>
                  </TouchableOpacity>
                ) : entry.status === 'done' ? (
                  <TouchableOpacity style={styles.viewBtn} onPress={() => router.push(`/results/${entry.scanId}`)}>
                    <Text style={styles.viewBtnText}>View Results →</Text>
                  </TouchableOpacity>
                ) : null}
              </View>
            </Card>
          ))}
        </View>
      )}
    </ScrollView>
  )
}

function StatPill({ label, value, color = colors.foreground }: { label: string; value: number; color?: string }) {
  return (
    <View style={statPillStyles.pill}>
      <Text style={[statPillStyles.value, { color }]}>{value}</Text>
      <Text style={statPillStyles.label}>{label}</Text>
    </View>
  )
}
const statPillStyles = StyleSheet.create({
  pill: { flex: 1, alignItems: 'center', gap: 2 },
  value: { fontFamily: 'DMSans_600SemiBold', fontSize: 18 },
  label: { fontFamily: 'DMSans_400Regular', fontSize: 10, color: colors.muted, textTransform: 'uppercase', letterSpacing: 0.5 },
})

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  content: { padding: 24, paddingTop: 64, paddingBottom: 50, gap: 16 },
  header: { gap: 4 },
  heading: { fontFamily: 'InstrumentSerif_400Regular', fontSize: 34, color: colors.foreground },
  sub: { fontFamily: 'DMSans_400Regular', fontSize: 14, color: colors.muted, marginTop: 2 },
  statsBar: { flexDirection: 'row', padding: 16, gap: 0 },
  actions: { flexDirection: 'row', gap: 8, alignItems: 'center' },
  clearBtn: { paddingHorizontal: 12, paddingVertical: 10 },
  clearText: { fontFamily: 'DMSans_400Regular', color: colors.muted, fontSize: 13 },
  emptyBox: { alignItems: 'center', paddingVertical: 60, gap: 10 },
  emptyTitle: { fontFamily: 'DMSans_500Medium', fontSize: 16, color: colors.foreground },
  emptySub: { fontFamily: 'DMSans_400Regular', fontSize: 13, color: colors.muted, textAlign: 'center', maxWidth: 260 },
  list: { gap: 10 },
  fileRow: { gap: 12 },
  fileInfo: { flexDirection: 'row', alignItems: 'flex-start', gap: 10 },
  fileName: { fontFamily: 'DMSans_500Medium', fontSize: 13, color: colors.foreground },
  errorMsg: { fontFamily: 'DMSans_400Regular', fontSize: 11, color: colors.red, marginTop: 2 },
  programRow: { flexDirection: 'row', gap: 6 },
  chip: { flex: 1, paddingVertical: 6, borderRadius: radius.sm, backgroundColor: 'rgba(26,23,20,0.04)', borderWidth: 1, borderColor: colors.stroke, alignItems: 'center' },
  chipActive: { backgroundColor: colors.foreground, borderColor: colors.foreground },
  chipText: { fontFamily: 'DMSans_500Medium', fontSize: 11, color: colors.muted },
  chipTextActive: { color: colors.background },
  fileActions: { flexDirection: 'row', justifyContent: 'flex-end' },
  runBtn: { paddingHorizontal: 14, paddingVertical: 7, backgroundColor: colors.foreground, borderRadius: radius.sm },
  runBtnText: { fontFamily: 'DMSans_600SemiBold', fontSize: 12, color: colors.background },
  viewBtn: { paddingHorizontal: 14, paddingVertical: 7 },
  viewBtnText: { fontFamily: 'DMSans_500Medium', fontSize: 12, color: colors.muted },
})
