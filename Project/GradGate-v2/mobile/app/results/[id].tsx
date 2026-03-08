import { useEffect, useState } from 'react'
import { View, Text, ScrollView, StyleSheet, TouchableOpacity } from 'react-native'
import { useLocalSearchParams, useRouter } from 'expo-router'
import { Ionicons } from '@expo/vector-icons'
import { useAuth } from '../../src/lib/AuthContext'
import { fetchResult } from '../../src/lib/api'
import { Card } from '../../src/components/Card'
import { SectionLabel } from '../../src/components/SectionLabel'
import { StatusBadge } from '../../src/components/StatusBadge'
import { colors, fonts, radius } from '../../src/theme'

export default function ResultsScreen() {
  const { id } = useLocalSearchParams<{ id: string }>()
  const { session } = useAuth()
  const router = useRouter()
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!session || !id) return
    fetchResult(session, id)
      .then(data => setResult(data.result))
      .catch(e => setError(e.message))
  }, [id, session])

  if (error) return (
    <View style={styles.centered}>
      <Text style={styles.errorText}>{error}</Text>
    </View>
  )

  if (!result) return (
    <View style={styles.centered}>
      <Text style={styles.loadingText}>Loading results…</Text>
    </View>
  )

  const audit = result.audit || {}
  const gradeDist = result.grade_distribution || {}

  let missingCourses: string[] = [...(audit.failed_courses || [])]
  const missingCats = audit.missing_courses || {}
  ;['ged', 'math', 'science', 'business', 'major', 'capstone', 'internship'].forEach(cat => {
    if (Array.isArray(missingCats[cat])) missingCourses = [...missingCourses, ...missingCats[cat]]
  })

  const maxGrade = Math.max(...Object.values(gradeDist) as number[], 1)

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
    >
      {/* Back */}
      <TouchableOpacity style={styles.backBtn} onPress={() => router.back()} activeOpacity={0.7}>
        <Ionicons name="chevron-back" size={16} color={colors.muted} />
        <Text style={styles.backText}>Back</Text>
      </TouchableOpacity>

      <View style={styles.header}>
        <SectionLabel>Degree Audit</SectionLabel>
        <Text style={styles.heading}>Results</Text>
        {result.program && <Text style={styles.sub}>{result.program}</Text>}
      </View>

      {/* Status & Stats */}
      <View style={styles.statsRow}>
        <Card style={[styles.statCard, styles.statusCard, { borderTopWidth: 3, borderTopColor: audit.eligible ? colors.green : colors.red }]}>
          <Text style={styles.statLabel}>Status</Text>
          <Text style={[styles.statBig, { color: audit.eligible ? colors.green : colors.red }]}>
            {audit.eligible ? 'ELIGIBLE' : 'DEFICIENT'}
          </Text>
        </Card>
        <View style={styles.smallStats}>
          <Card style={styles.statCard}>
            <Text style={styles.statLabel}>Credits</Text>
            <Text style={styles.statBig}>{audit.credits_completed || 0}
              <Text style={styles.statOf}>/{audit.credits_required || 0}</Text>
            </Text>
          </Card>
          <Card style={styles.statCard}>
            <Text style={styles.statLabel}>CGPA</Text>
            <Text style={styles.statBig}>{(result.cgpa?.final || 0).toFixed(2)}</Text>
          </Card>
        </View>
      </View>

      {/* Missing courses */}
      {missingCourses.length > 0 && (
        <Card style={styles.missingCard}>
          <Text style={styles.missingTitle}>Action Required: Missing / Failed Courses</Text>
          <View style={styles.courseChips}>
            {missingCourses.map((c, i) => (
              <View key={i} style={styles.courseChip}>
                <Text style={styles.courseChipText}>{c}</Text>
              </View>
            ))}
          </View>
        </Card>
      )}

      {/* Roadmap */}
      <Card>
        <Text style={styles.sectionTitle}>Academic Roadmap</Text>
        {audit.roadmap && audit.roadmap.length > 0
          ? audit.roadmap.map((step: string, i: number) => (
            <View key={i} style={styles.roadmapItem}>
              <View style={styles.roadmapBar} />
              <Text style={styles.roadmapText}>{step}</Text>
            </View>
          ))
          : (
            <View style={[styles.roadmapItem, { borderLeftColor: colors.green }]}>
              <View style={[styles.roadmapBar, { backgroundColor: colors.green }]} />
              <Text style={[styles.roadmapText, { color: colors.green }]}>All requirements complete!</Text>
            </View>
          )
        }
      </Card>

      {/* Grade distribution */}
      <Card>
        <Text style={styles.sectionTitle}>Grade Distribution</Text>
        {Object.entries(gradeDist).length > 0
          ? Object.entries(gradeDist).map(([grade, count]) => (
            <View key={grade} style={styles.gradeRow}>
              <Text style={styles.gradeLabel}>{grade}</Text>
              <View style={styles.gradeBarBg}>
                <View style={[styles.gradeBar, { width: `${((count as number) / maxGrade) * 100}%` }]} />
              </View>
              <Text style={styles.gradeCount}>{count as number}</Text>
            </View>
          ))
          : <Text style={styles.noData}>No grade data available.</Text>
        }
      </Card>
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  content: { padding: 24, paddingTop: 60, paddingBottom: 50, gap: 16 },
  centered: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.background },
  loadingText: { fontFamily: 'DMSans_400Regular', fontSize: 14, color: colors.muted },
  errorText: { fontFamily: 'DMSans_400Regular', fontSize: 14, color: colors.red },
  backBtn: { flexDirection: 'row', alignItems: 'center', gap: 4, marginBottom: 8 },
  backText: { fontFamily: 'DMSans_400Regular', fontSize: 13, color: colors.muted },
  header: { gap: 4, marginBottom: 4 },
  heading: { fontFamily: 'InstrumentSerif_400Regular', fontSize: 34, color: colors.foreground },
  sub: { fontFamily: 'DMSans_400Regular', fontSize: 13, color: colors.muted, marginTop: 2 },
  statsRow: { flexDirection: 'row', gap: 10 },
  statusCard: { flex: 1.5 },
  smallStats: { flex: 1, gap: 10 },
  statCard: { padding: 16, gap: 6 },
  statLabel: { fontFamily: 'DMSans_400Regular', fontSize: 10, letterSpacing: 1.2, textTransform: 'uppercase', color: colors.muted },
  statBig: { fontFamily: 'InstrumentSerif_400Regular', fontSize: 28, color: colors.foreground, lineHeight: 34 },
  statOf: { fontFamily: 'DMSans_400Regular', fontSize: 16, color: colors.muted },
  missingCard: { backgroundColor: '#FEF2F2', borderColor: '#FECACA' },
  missingTitle: { fontFamily: 'DMSans_500Medium', fontSize: 13, color: colors.red, marginBottom: 10 },
  courseChips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  courseChip: { paddingHorizontal: 10, paddingVertical: 5, backgroundColor: '#FEE2E2', borderRadius: radius.md, borderWidth: 1, borderColor: '#FECACA' },
  courseChipText: { fontFamily: 'DMSans_500Medium', fontSize: 12, color: colors.red },
  sectionTitle: { fontFamily: 'DMSans_600SemiBold', fontSize: 13, color: colors.foreground, marginBottom: 16 },
  roadmapItem: { flexDirection: 'row', gap: 12, alignItems: 'flex-start', marginBottom: 10 },
  roadmapBar: { width: 2, minHeight: 18, backgroundColor: 'rgba(26,23,20,0.2)', borderRadius: 1, marginTop: 3 },
  roadmapText: { flex: 1, fontFamily: 'DMSans_400Regular', fontSize: 14, color: colors.foreground, lineHeight: 20 },
  gradeRow: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 8 },
  gradeLabel: { fontFamily: 'DMSans_500Medium', fontSize: 13, color: colors.foreground, width: 28 },
  gradeBarBg: { flex: 1, height: 5, backgroundColor: 'rgba(26,23,20,0.07)', borderRadius: 99, overflow: 'hidden' },
  gradeBar: { height: '100%', backgroundColor: 'rgba(26,23,20,0.4)', borderRadius: 99 },
  gradeCount: { fontFamily: 'DMSans_400Regular', fontSize: 12, color: colors.muted, width: 24, textAlign: 'right' },
  noData: { fontFamily: 'DMSans_400Regular', fontSize: 13, color: colors.muted },
})
