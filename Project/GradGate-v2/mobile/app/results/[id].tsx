import { useEffect, useMemo, useState } from 'react'
import { View, Text, ScrollView, StyleSheet, TouchableOpacity } from 'react-native'
import { useLocalSearchParams, useRouter } from 'expo-router'
import { Ionicons } from '@expo/vector-icons'
import { useAuth } from '../../src/lib/AuthContext'
import { fetchResult } from '../../src/lib/api'
import { levelLabel } from '../../src/lib/auditConfig'
import { Card } from '../../src/components/Card'
import { SectionLabel } from '../../src/components/SectionLabel'
import { StatusBadge } from '../../src/components/StatusBadge'
import { colors, radius } from '../../src/theme'

function MetricCard({ label, value }: { label: string; value: string | number }) {
  return (
    <Card style={styles.metricCard}>
      <Text style={styles.metricLabel}>{label}</Text>
      <Text style={styles.metricValue}>{value}</Text>
    </Card>
  )
}

export default function ResultsScreen() {
  const { id } = useLocalSearchParams<{ id: string }>()
  const { session } = useAuth()
  const router = useRouter()
  const [scan, setScan] = useState<any>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!session || !id) return
    fetchResult(session, id)
      .then(setScan)
      .catch((e) => setError(e.message))
  }, [id, session])

  const result = scan?.result || {}
  const audit = result.audit || {}
  const metadata = result.metadata || {}
  const gradeDist = result.grade_distribution || {}
  const requestedLevel = metadata.requested_level
  const missingCourses = audit.missing_courses || {}
  const deficiencyEntries = Object.entries(missingCourses).filter(([_, value]) =>
    Array.isArray(value) ? value.length > 0 : Number(value) > 0
  )
  const prereqViolations = audit.prerequisite_violations || []
  const maxGradeCount = useMemo(
    () => Math.max(...(Object.values(gradeDist) as number[]), 1),
    [gradeDist]
  )

  if (error) {
    return (
      <View style={styles.centered}>
        <Text style={styles.errorText}>{error}</Text>
      </View>
    )
  }

  if (!scan) {
    return (
      <View style={styles.centered}>
        <Text style={styles.loadingText}>Loading results…</Text>
      </View>
    )
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
    >
      <TouchableOpacity style={styles.backBtn} onPress={() => router.back()} activeOpacity={0.75}>
        <Ionicons name="chevron-back" size={16} color={colors.muted} />
        <Text style={styles.backText}>Back</Text>
      </TouchableOpacity>

      <View style={styles.header}>
        <SectionLabel>Degree Audit</SectionLabel>
        <Text style={styles.heading}>Results</Text>
        <Text style={styles.sub}>{result.program || scan.program}</Text>
      </View>

      <Card style={styles.topCard}>
        <View style={styles.topRow}>
          <StatusBadge eligible={Boolean(audit.eligible)} />
          <View style={styles.metaPills}>
            {requestedLevel ? (
              <View style={styles.metaPill}>
                <Text style={styles.metaPillText}>{levelLabel(requestedLevel)}</Text>
              </View>
            ) : null}
            {scan.input_type ? (
              <View style={styles.metaPill}>
                <Text style={styles.metaPillText}>{scan.input_type.toUpperCase()}</Text>
              </View>
            ) : null}
          </View>
        </View>
        <Text style={styles.topTitle}>
          {audit.eligible ? 'Eligible for graduation' : 'Not eligible for graduation'}
        </Text>
        <Text style={styles.topSub}>
          {scan.file_name || 'Uploaded transcript'}
        </Text>
      </Card>

      <View style={styles.metricsGrid}>
        <MetricCard label="Credits" value={`${audit.credits_completed || 0}/${audit.credits_required || 0}`} />
        <MetricCard label="CGPA" value={(result.cgpa?.final || 0).toFixed(3)} />
        <MetricCard label="Major CGPA" value={(audit.major_cgpa || 0).toFixed(3)} />
      </View>

      {audit.reasons?.length ? (
        <Card>
          <Text style={styles.sectionTitle}>Blocking Reasons</Text>
          <View style={styles.stack}>
            {audit.reasons.map((reason: string) => (
              <View key={reason} style={styles.listRow}>
                <Ionicons name="alert-circle" size={16} color={colors.red} />
                <Text style={styles.listText}>{reason}</Text>
              </View>
            ))}
          </View>
        </Card>
      ) : null}

      <Card>
        <Text style={styles.sectionTitle}>Academic Roadmap</Text>
        {audit.roadmap?.length ? (
          <View style={styles.stack}>
            {audit.roadmap.map((step: string) => (
              <View key={step} style={styles.listRow}>
                <Ionicons name="git-branch-outline" size={16} color={colors.muted} />
                <Text style={styles.listText}>{step}</Text>
              </View>
            ))}
          </View>
        ) : (
          <Text style={styles.helperText}>All requirements complete.</Text>
        )}
      </Card>

      {(audit.concentration || audit.minor) ? (
        <Card>
          <Text style={styles.sectionTitle}>Specialization</Text>
          {audit.concentration ? (
            <View style={styles.infoBlock}>
              <Text style={styles.infoTitle}>Concentration</Text>
              <Text style={styles.infoText}>
                {audit.concentration.name} · CGPA {(audit.concentration.cgpa || 0).toFixed(3)}
              </Text>
            </View>
          ) : null}
          {audit.minor ? (
            <View style={styles.infoBlock}>
              <Text style={styles.infoTitle}>Minor</Text>
              <Text style={styles.infoText}>
                {audit.minor.name} · {audit.minor.completed ? 'Completed' : 'Incomplete'}
              </Text>
              {audit.minor.courses_missing?.length ? (
                <Text style={styles.helperText}>
                  Missing: {audit.minor.courses_missing.join(', ')}
                </Text>
              ) : null}
            </View>
          ) : null}
        </Card>
      ) : null}

      {deficiencyEntries.length ? (
        <Card>
          <Text style={styles.sectionTitle}>Deficiencies</Text>
          <View style={styles.stack}>
            {deficiencyEntries.map(([key, value]) => (
              <View key={key} style={styles.infoBlock}>
                <Text style={styles.infoTitle}>{key.replace(/_/g, ' ')}</Text>
                <Text style={styles.infoText}>
                  {Array.isArray(value) ? value.join(', ') : String(value)}
                </Text>
              </View>
            ))}
          </View>
        </Card>
      ) : null}

      {audit.failed_courses?.length ? (
        <Card>
          <Text style={styles.sectionTitle}>Failed Courses</Text>
          <Text style={styles.infoText}>{audit.failed_courses.join(', ')}</Text>
        </Card>
      ) : null}

      {prereqViolations.length ? (
        <Card>
          <Text style={styles.sectionTitle}>Prerequisite Violations</Text>
          <View style={styles.stack}>
            {prereqViolations.map((item: any, index: number) => (
              <View key={`${item.course}-${index}`} style={styles.infoBlock}>
                <Text style={styles.infoTitle}>{item.course}</Text>
                <Text style={styles.infoText}>
                  Missing {item.missing_prereqs?.join(', ')} · {item.semester}
                </Text>
              </View>
            ))}
          </View>
        </Card>
      ) : null}

      <Card>
        <Text style={styles.sectionTitle}>Grade Distribution</Text>
        {Object.keys(gradeDist).length ? (
          <View style={styles.stack}>
            {Object.entries(gradeDist).map(([grade, count]) => (
              <View key={grade} style={styles.gradeRow}>
                <Text style={styles.gradeLabel}>{grade}</Text>
                <View style={styles.gradeBarBg}>
                  <View
                    style={[
                      styles.gradeBar,
                      { width: `${((count as number) / maxGradeCount) * 100}%` },
                    ]}
                  />
                </View>
                <Text style={styles.gradeCount}>{count as number}</Text>
              </View>
            ))}
          </View>
        ) : (
          <Text style={styles.helperText}>No grade data available.</Text>
        )}
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
  topCard: { gap: 10 },
  topRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 8 },
  metaPills: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, justifyContent: 'flex-end' },
  metaPill: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: colors.stroke,
    backgroundColor: 'rgba(26,23,20,0.04)',
  },
  metaPillText: { fontFamily: 'DMSans_500Medium', fontSize: 10, color: colors.muted },
  topTitle: { fontFamily: 'DMSans_600SemiBold', fontSize: 18, color: colors.foreground },
  topSub: { fontFamily: 'DMSans_400Regular', fontSize: 12, color: colors.muted },
  metricsGrid: { flexDirection: 'row', gap: 10 },
  metricCard: { flex: 1, padding: 16, gap: 6 },
  metricLabel: {
    fontFamily: 'DMSans_400Regular',
    fontSize: 10,
    color: colors.muted,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
  },
  metricValue: { fontFamily: 'InstrumentSerif_400Regular', fontSize: 24, color: colors.foreground },
  sectionTitle: { fontFamily: 'DMSans_600SemiBold', fontSize: 13, color: colors.foreground, marginBottom: 10 },
  stack: { gap: 10 },
  listRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 10 },
  listText: { flex: 1, fontFamily: 'DMSans_400Regular', fontSize: 13, color: colors.foreground, lineHeight: 19 },
  infoBlock: { gap: 4 },
  infoTitle: { fontFamily: 'DMSans_500Medium', fontSize: 12, color: colors.foreground, textTransform: 'capitalize' },
  infoText: { fontFamily: 'DMSans_400Regular', fontSize: 13, color: colors.foreground, lineHeight: 19 },
  helperText: { fontFamily: 'DMSans_400Regular', fontSize: 13, color: colors.muted },
  gradeRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  gradeLabel: { width: 28, fontFamily: 'DMSans_500Medium', fontSize: 13, color: colors.foreground },
  gradeBarBg: { flex: 1, height: 6, borderRadius: 999, backgroundColor: 'rgba(26,23,20,0.07)', overflow: 'hidden' },
  gradeBar: { height: '100%', borderRadius: 999, backgroundColor: 'rgba(26,23,20,0.4)' },
  gradeCount: { width: 24, textAlign: 'right', fontFamily: 'DMSans_400Regular', fontSize: 12, color: colors.muted },
})
