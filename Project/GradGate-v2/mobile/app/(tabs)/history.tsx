import { useEffect, useState } from 'react'
import { View, Text, ScrollView, StyleSheet, TouchableOpacity, ActivityIndicator } from 'react-native'
import { useRouter } from 'expo-router'
import { Ionicons } from '@expo/vector-icons'
import { useAuth } from '../../src/lib/AuthContext'
import { fetchHistory } from '../../src/lib/api'
import { Card } from '../../src/components/Card'
import { SectionLabel } from '../../src/components/SectionLabel'
import { colors, fonts, radius } from '../../src/theme'

export default function HistoryScreen() {
  const { session } = useAuth()
  const router = useRouter()
  const [history, setHistory] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!session) return
    fetchHistory(session)
      .then(setHistory)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [session])

  const formatDate = (iso: string) => {
    const d = new Date(iso)
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
    >
      <View style={styles.header}>
        <SectionLabel>Audit History</SectionLabel>
        <Text style={styles.heading}>Past Scans</Text>
      </View>

      {error ? (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      ) : loading ? (
        <View style={styles.loadingBox}>
          {[1, 2, 3].map(i => (
            <View key={i} style={styles.skeleton} />
          ))}
        </View>
      ) : history.length === 0 ? (
        <View style={styles.emptyBox}>
          <View style={styles.emptyIcon}>
            <Ionicons name="document-text-outline" size={28} color={colors.muted} />
          </View>
          <Text style={styles.emptyTitle}>No audits yet</Text>
          <Text style={styles.emptySub}>Upload a transcript to run your first degree audit.</Text>
        </View>
      ) : (
        <View style={styles.list}>
          {history.map((scan: any) => (
            <TouchableOpacity key={scan.id} onPress={() => router.push(`/results/${scan.id}`)} activeOpacity={0.8}>
              <Card style={styles.row}>
                <View style={styles.fileIcon}>
                  <Ionicons name="document-text-outline" size={18} color={colors.muted} />
                </View>
                <View style={styles.rowInfo}>
                  <Text style={styles.rowTitle}>
                    <Text style={styles.bold}>{scan.program}</Text> Degree Audit
                  </Text>
                  <Text style={styles.rowSub}>
                    {formatDate(scan.created_at)}
                    {scan.file_name ? `  ·  ${scan.file_name}` : ''}
                  </Text>
                </View>
                <View style={styles.badge}>
                  <Text style={styles.badgeText}>{scan.input_type}</Text>
                </View>
                <Ionicons name="chevron-forward" size={16} color={colors.muted} />
              </Card>
            </TouchableOpacity>
          ))}
        </View>
      )}
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  content: { padding: 24, paddingTop: 64, paddingBottom: 40, gap: 20 },
  header: { gap: 4 },
  heading: { fontFamily: 'InstrumentSerif_400Regular', fontSize: 34, color: colors.foreground },
  errorBox: { backgroundColor: '#FEF2F2', padding: 14, borderRadius: radius.md, borderWidth: 1, borderColor: '#FECACA' },
  errorText: { fontFamily: 'DMSans_400Regular', color: '#DC2626', fontSize: 13 },
  loadingBox: { gap: 10 },
  skeleton: { height: 80, borderRadius: radius.card, backgroundColor: 'rgba(26,23,20,0.05)' },
  emptyBox: { alignItems: 'center', paddingVertical: 60, gap: 10 },
  emptyIcon: { width: 60, height: 60, borderRadius: 30, backgroundColor: 'rgba(26,23,20,0.04)', borderWidth: 1, borderColor: colors.stroke, alignItems: 'center', justifyContent: 'center' },
  emptyTitle: { fontFamily: 'DMSans_500Medium', fontSize: 16, color: colors.foreground },
  emptySub: { fontFamily: 'DMSans_400Regular', fontSize: 13, color: colors.muted, textAlign: 'center', maxWidth: 260 },
  list: { gap: 10 },
  row: { flexDirection: 'row', alignItems: 'center', gap: 12, padding: 16 },
  fileIcon: { width: 40, height: 40, borderRadius: radius.md, backgroundColor: 'rgba(26,23,20,0.04)', borderWidth: 1, borderColor: colors.stroke, alignItems: 'center', justifyContent: 'center' },
  rowInfo: { flex: 1, gap: 3 },
  rowTitle: { fontFamily: 'DMSans_400Regular', fontSize: 14, color: colors.foreground },
  bold: { fontFamily: 'DMSans_600SemiBold' },
  rowSub: { fontFamily: 'DMSans_400Regular', fontSize: 12, color: colors.muted },
  badge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: radius.pill, backgroundColor: 'rgba(26,23,20,0.05)', borderWidth: 1, borderColor: colors.stroke },
  badgeText: { fontFamily: 'DMSans_500Medium', fontSize: 10, color: colors.muted, textTransform: 'uppercase', letterSpacing: 0.8 },
})
