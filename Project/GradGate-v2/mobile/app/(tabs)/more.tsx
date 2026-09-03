import { useEffect, useState } from 'react'
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import { useAuth } from '../../src/lib/AuthContext'
import { fetchApiHealth, fetchAuditOptions, fetchOcrStatus } from '../../src/lib/api'
import { Card } from '../../src/components/Card'
import { PrimaryButton } from '../../src/components/PrimaryButton'
import { SectionLabel } from '../../src/components/SectionLabel'
import { colors, radius } from '../../src/theme'

type ProbeState = 'idle' | 'checking' | 'ready' | 'error'

const MCP_TOOLS = [
  'gradgate_health',
  'gradgate_audit_options',
  'gradgate_ocr_status',
  'gradgate_audit_csv',
  'gradgate_audit_document',
  'gradgate_audit_reviewed_document',
  'gradgate_history_list',
  'gradgate_history_get',
]

const MCP_RESOURCES = [
  'gradgate://curriculum/catalog',
  'gradgate://curriculum/official-bucket-models',
]

export default function MoreScreen() {
  const { session, signOut } = useAuth()
  const [probeState, setProbeState] = useState<ProbeState>('idle')
  const [apiVersion, setApiVersion] = useState('')
  const [programCount, setProgramCount] = useState<number | null>(null)
  const [ocrReady, setOcrReady] = useState<boolean | null>(null)
  const [message, setMessage] = useState('')

  const runMcpProbe = async () => {
    setProbeState('checking')
    setMessage('')

    try {
      const [health, options, ocr] = await Promise.all([
        fetchApiHealth(),
        fetchAuditOptions(),
        fetchOcrStatus(),
      ])

      setApiVersion(health.version || 'unknown')
      setProgramCount(options.programs?.length ?? null)
      setOcrReady(Boolean(ocr.ready))
      setProbeState('ready')
      setMessage('MCP-compatible API tools can reach health, options, and OCR readiness.')
    } catch (error: any) {
      setProbeState('error')
      setMessage(error?.message || 'Could not reach the GradGate API.')
    }
  }

  useEffect(() => {
    runMcpProbe()
  }, [])

  const confirmLogout = () => {
    Alert.alert('Sign out?', 'You can sign back in with Google any time.', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Sign Out',
        style: 'destructive',
        onPress: async () => {
          try {
            await signOut()
          } catch (error: any) {
            Alert.alert('Sign out failed', error?.message || 'Please try again.')
          }
        },
      },
    ])
  }

  const statusColor =
    probeState === 'ready'
      ? colors.green
      : probeState === 'error'
        ? colors.red
        : colors.muted

  const statusLabel =
    probeState === 'checking'
      ? 'Checking'
      : probeState === 'ready'
        ? 'Ready'
        : probeState === 'error'
          ? 'Offline'
          : 'Not checked'

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
    >
      <View style={styles.header}>
        <SectionLabel>More</SectionLabel>
        <Text style={styles.heading}>Settings & Integrations</Text>
        <Text style={styles.sub}>Account controls, local API readiness, and a peek at GradGate's MCP bridge.</Text>
      </View>

      <Card style={styles.accountCard}>
        <View style={styles.accountIcon}>
          <Ionicons name="person-outline" size={22} color={colors.foreground} />
        </View>
        <View style={{ flex: 1 }}>
          <Text style={styles.accountLabel}>Signed in as</Text>
          <Text style={styles.accountEmail} selectable numberOfLines={1}>
            {session?.user?.email || 'Unknown user'}
          </Text>
        </View>
      </Card>

      <Card style={styles.card}>
        <View style={styles.cardHeader}>
          <View>
            <SectionLabel>GradGate API</SectionLabel>
            <Text style={styles.cardTitle}>Runtime Status</Text>
          </View>
          <View style={[styles.statusPill, { borderColor: statusColor }]}>
            {probeState === 'checking' ? (
              <ActivityIndicator size="small" color={colors.muted} />
            ) : (
              <View style={[styles.statusDot, { backgroundColor: statusColor }]} />
            )}
            <Text style={[styles.statusText, { color: statusColor }]}>{statusLabel}</Text>
          </View>
        </View>

        <View style={styles.metricGrid}>
          <Metric label="API" value={apiVersion || 'Waiting'} />
          <Metric label="Programs" value={programCount === null ? 'Waiting' : String(programCount)} />
          <Metric label="OCR" value={ocrReady === null ? 'Waiting' : ocrReady ? 'Ready' : 'Needs setup'} />
        </View>

        {message ? (
          <Text
            style={[styles.message, probeState === 'error' && styles.errorMessage]}
            selectable
          >
            {message}
          </Text>
        ) : null}

        <PrimaryButton
          label={probeState === 'checking' ? 'Checking...' : 'Refresh Status'}
          onPress={runMcpProbe}
          loading={probeState === 'checking'}
          variant="outline"
        />
      </Card>

      <Card style={styles.card}>
        <View style={styles.cardHeader}>
          <View>
            <SectionLabel>MCP Bridge</SectionLabel>
            <Text style={styles.cardTitle}>Agent-Ready GradGate</Text>
          </View>
          <Ionicons name="git-network-outline" size={24} color={colors.foreground} />
        </View>

        <Text style={styles.bodyText}>
          The MCP server exposes GradGate as tools an agent can call: health checks, OCR readiness,
          transcript audits, reviewed OCR continuation, history, and curriculum resources.
        </Text>

        <View style={styles.commandBox}>
          <Text style={styles.commandLabel}>Local MCP command</Text>
          <Text style={styles.commandText} selectable>python -m gradgate_mcp</Text>
        </View>

        <View style={styles.toolWrap}>
          {MCP_TOOLS.map((tool) => (
            <View key={tool} style={styles.toolChip}>
              <Text style={styles.toolText}>{tool}</Text>
            </View>
          ))}
        </View>
      </Card>

      <Card style={styles.card}>
        <SectionLabel>Resources</SectionLabel>
        <Text style={styles.cardTitle}>Read-Only Curriculum Context</Text>
        {MCP_RESOURCES.map((resource) => (
          <View key={resource} style={styles.resourceRow}>
            <Ionicons name="book-outline" size={16} color={colors.muted} />
            <Text style={styles.resourceText} selectable>{resource}</Text>
          </View>
        ))}
      </Card>

      <Card style={styles.card}>
        <SectionLabel>Settings</SectionLabel>
        <TouchableOpacity style={styles.settingRow} onPress={runMcpProbe} activeOpacity={0.75}>
          <View style={styles.settingLeft}>
            <Ionicons name="refresh-outline" size={19} color={colors.foreground} />
            <Text style={styles.settingText}>Refresh API and MCP readiness</Text>
          </View>
          <Ionicons name="chevron-forward" size={17} color={colors.muted} />
        </TouchableOpacity>

        <TouchableOpacity style={styles.settingRow} onPress={confirmLogout} activeOpacity={0.75}>
          <View style={styles.settingLeft}>
            <Ionicons name="log-out-outline" size={19} color={colors.red} />
            <Text style={[styles.settingText, { color: colors.red }]}>Log out</Text>
          </View>
          <Ionicons name="chevron-forward" size={17} color={colors.muted} />
        </TouchableOpacity>
      </Card>
    </ScrollView>
  )
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.metric}>
      <Text style={styles.metricValue} numberOfLines={1}>{value}</Text>
      <Text style={styles.metricLabel}>{label}</Text>
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  content: { padding: 24, paddingTop: 64, paddingBottom: 50, gap: 16 },
  header: { gap: 4 },
  heading: { fontFamily: 'InstrumentSerif_400Regular', fontSize: 34, color: colors.foreground },
  sub: { fontFamily: 'DMSans_400Regular', fontSize: 14, color: colors.muted, marginTop: 2 },
  accountCard: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  accountIcon: {
    width: 46,
    height: 46,
    borderRadius: 23,
    backgroundColor: 'rgba(26,23,20,0.04)',
    borderWidth: 1,
    borderColor: colors.stroke,
    alignItems: 'center',
    justifyContent: 'center',
  },
  accountLabel: { fontFamily: 'DMSans_400Regular', fontSize: 12, color: colors.muted },
  accountEmail: { fontFamily: 'DMSans_600SemiBold', fontSize: 14, color: colors.foreground },
  card: { gap: 14 },
  cardHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 12 },
  cardTitle: { fontFamily: 'DMSans_600SemiBold', fontSize: 18, color: colors.foreground, marginTop: 3 },
  statusPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 7,
    borderRadius: radius.pill,
    borderWidth: 1,
    backgroundColor: 'rgba(255,255,255,0.65)',
  },
  statusDot: { width: 7, height: 7, borderRadius: 4 },
  statusText: { fontFamily: 'DMSans_600SemiBold', fontSize: 11, textTransform: 'uppercase', letterSpacing: 0.4 },
  metricGrid: { flexDirection: 'row', gap: 8 },
  metric: {
    flex: 1,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.stroke,
    backgroundColor: 'rgba(26,23,20,0.03)',
    padding: 10,
    gap: 2,
  },
  metricValue: { fontFamily: 'DMSans_600SemiBold', fontSize: 13, color: colors.foreground },
  metricLabel: { fontFamily: 'DMSans_400Regular', fontSize: 10, color: colors.muted, textTransform: 'uppercase', letterSpacing: 0.4 },
  message: { fontFamily: 'DMSans_400Regular', fontSize: 13, color: colors.muted },
  errorMessage: { color: colors.red },
  bodyText: { fontFamily: 'DMSans_400Regular', fontSize: 13, lineHeight: 19, color: colors.muted },
  commandBox: {
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.stroke,
    backgroundColor: colors.foreground,
    padding: 13,
    gap: 5,
  },
  commandLabel: { fontFamily: 'DMSans_500Medium', fontSize: 11, color: 'rgba(250,248,245,0.7)', textTransform: 'uppercase', letterSpacing: 0.5 },
  commandText: { fontFamily: 'DMSans_600SemiBold', fontSize: 13, color: colors.background },
  toolWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  toolChip: {
    paddingHorizontal: 10,
    paddingVertical: 7,
    borderRadius: radius.pill,
    backgroundColor: 'rgba(26,23,20,0.04)',
    borderWidth: 1,
    borderColor: colors.stroke,
  },
  toolText: { fontFamily: 'DMSans_500Medium', fontSize: 11, color: colors.foreground },
  resourceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    borderRadius: radius.md,
    backgroundColor: 'rgba(26,23,20,0.03)',
    borderWidth: 1,
    borderColor: colors.stroke,
    padding: 11,
  },
  resourceText: { flex: 1, fontFamily: 'DMSans_500Medium', fontSize: 12, color: colors.foreground },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.stroke,
    backgroundColor: 'rgba(255,255,255,0.6)',
    padding: 14,
  },
  settingLeft: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  settingText: { fontFamily: 'DMSans_500Medium', fontSize: 14, color: colors.foreground },
})
