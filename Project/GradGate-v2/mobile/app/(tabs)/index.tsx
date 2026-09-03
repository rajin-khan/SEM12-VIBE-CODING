import { useEffect, useMemo, useState } from 'react'
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Alert,
  TextInput,
  ImageBackground,
} from 'react-native'
import { useRouter } from 'expo-router'
import * as ImagePicker from 'expo-image-picker'
import * as DocumentPicker from 'expo-document-picker'
import { Ionicons } from '@expo/vector-icons'
import { useAuth } from '../../src/lib/AuthContext'
import {
  fetchApiHealth,
  fetchAuditOptions,
  fetchOcrStatus,
  PickedTranscriptFile,
  submitReviewedAudit,
  runTranscriptAudit,
} from '../../src/lib/api'
import { defaultAuditOptions, levelLabel } from '../../src/lib/auditConfig'
import { Card } from '../../src/components/Card'
import { PrimaryButton } from '../../src/components/PrimaryButton'
import { SectionLabel } from '../../src/components/SectionLabel'
import { colors, radius } from '../../src/theme'

const heroBanner = require('../../assets/brand/gradgate-hero-banner.png')

function ChipGroup({
  options,
  value,
  onChange,
}: {
  options: Array<{ value: string; label: string }>
  value: string
  onChange: (value: string) => void
}) {
  return (
    <View style={styles.chipWrap}>
      {options.map((option) => (
        <TouchableOpacity
          key={option.value}
          style={[styles.chip, value === option.value && styles.chipActive]}
          onPress={() => onChange(option.value)}
          activeOpacity={0.75}
        >
          <Text style={[styles.chipText, value === option.value && styles.chipTextActive]}>
            {option.label}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  )
}

export default function DashboardScreen() {
  const { session } = useAuth()
  const router = useRouter()
  const [file, setFile] = useState<PickedTranscriptFile | null>(null)
  const [program, setProgram] = useState('CSE')
  const [level, setLevel] = useState('all')
  const [report, setReport] = useState('normal')
  const [concentration, setConcentration] = useState('')
  const [minor, setMinor] = useState('')
  const [waiverInput, setWaiverInput] = useState('')
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [loading, setLoading] = useState(false)
  const [auditOptions, setAuditOptions] = useState(defaultAuditOptions())
  const [ocrStatus, setOcrStatus] = useState<any>(null)
  const [apiError, setApiError] = useState('')
  const [reviewPayload, setReviewPayload] = useState<any>(null)

  useEffect(() => {
    let active = true

    fetchApiHealth()
      .then(() => {
        if (!active) return
        setApiError('')
        return Promise.allSettled([fetchAuditOptions(), fetchOcrStatus()])
      })
      .then((results) => {
        if (!active || !results) return
        const [optionsResult, ocrResult] = results

        if (optionsResult.status === 'fulfilled') {
          setAuditOptions(optionsResult.value)
          setProgram((current) =>
            optionsResult.value.programs.some((item: any) => item.value === current)
              ? current
              : optionsResult.value.programs[0]?.value || 'CSE'
          )
        }

        if (ocrResult.status === 'fulfilled') {
          setOcrStatus(ocrResult.value)
        }
      })
      .catch((error: any) => {
        if (!active) return
        setApiError(error?.message || 'Cannot reach the GradGate API.')
      })

    return () => {
      active = false
    }
  }, [])

  const selectedProgram = useMemo(
    () => auditOptions.programs.find((item: any) => item.value === program),
    [auditOptions.programs, program]
  )

  const isCsv = file?.name?.toLowerCase().endsWith('.csv')
  const isScannedDocument = Boolean(file) && !isCsv
  const canChooseReport = level === '3' || level === 'all'
  const showConcentration = program === 'BBA'
  const showMinor = Boolean(selectedProgram?.supports_minor)
  const waivableCourses = selectedProgram?.waivable_courses || []

  useEffect(() => {
    if (!canChooseReport) setReport('normal')
  }, [canChooseReport])

  useEffect(() => {
    if (!showConcentration) setConcentration('')
    if (!showMinor) setMinor('')
  }, [showConcentration, showMinor])

  const pickFile = async () => {
    const result = await DocumentPicker.getDocumentAsync({
      type: ['text/csv', 'application/pdf', 'image/*'],
      copyToCacheDirectory: true,
    })
    if (!result.canceled && result.assets[0]) {
      const asset = result.assets[0]
      setFile({ uri: asset.uri, name: asset.name, type: asset.mimeType || 'text/csv' })
    }
  }

  const openCamera = async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync()
    if (status !== 'granted') {
      Alert.alert('Permission required', 'Camera access is needed to scan transcripts.')
      return
    }

    const result = await ImagePicker.launchCameraAsync({ quality: 0.85, allowsEditing: true })
    if (!result.canceled && result.assets[0]) {
      const asset = result.assets[0]
      setFile({
        uri: asset.uri,
        name: `transcript_${Date.now()}.jpg`,
        type: 'image/jpeg',
      })
    }
  }

  const runAudit = async () => {
    if (!file) {
      Alert.alert('Transcript required', 'Select a transcript file before running an audit.')
      return
    }
    if (!session) {
      Alert.alert('Sign in required', 'Sign in with Google to run audits and save history.')
      return
    }

    setLoading(true)
    try {
      setReviewPayload(null)
      const data = await runTranscriptAudit(session, {
        file,
        program,
        level,
        report,
        concentration,
        minor,
        waivers: waiverInput
          .split(',')
          .map((item) => item.trim().toUpperCase())
          .filter(Boolean),
      })
      if (data.status === 'review_required') {
        setReviewPayload(data.review)
        return
      }
      router.push(`/results/${data.scan_id}`)
    } catch (e: any) {
      Alert.alert('Audit failed', e.message)
    } finally {
      setLoading(false)
    }
  }

  const fileIcon = !file
    ? 'cloud-upload-outline'
    : isCsv
      ? 'document-text-outline'
      : 'image-outline'

  const runReviewedAudit = async () => {
    if (!reviewPayload || !file || !session) return

    setLoading(true)
    try {
      const data = await submitReviewedAudit(session, {
        program,
        input_type: reviewPayload.input_type,
        file_name: file.name,
        extracted_csv: reviewPayload.extracted_csv,
        waivers: waiverInput
          .split(',')
          .map((item) => item.trim().toUpperCase())
          .filter(Boolean),
        level,
        report,
        concentration: concentration || null,
        minor: minor || null,
        extraction_mode: reviewPayload.extraction_mode,
        warnings: reviewPayload.warnings || [],
      })
      router.push(`/results/${data.scan_id}`)
    } catch (e: any) {
      Alert.alert('Audit failed', e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
    >
      <View style={styles.header}>
        <SectionLabel>Dashboard</SectionLabel>
        <Text style={styles.heading}>Start a Degree Audit</Text>
        <Text style={styles.sub}>Upload CSV, PDF, or transcript images through the same GradGate flow as web and CLI.</Text>
      </View>

      <ImageBackground source={heroBanner} style={styles.heroBanner} imageStyle={styles.heroBannerImage}>
        <View style={styles.heroOverlay}>
          <Text style={styles.heroEyebrow}>OCR + Degree Intelligence</Text>
          <Text style={styles.heroTitle}>Transcript to audit, without the paperwork fog.</Text>
        </View>
      </ImageBackground>

      {apiError ? (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{apiError}</Text>
        </View>
      ) : null}

      {isScannedDocument && ocrStatus && !ocrStatus.ready ? (
        <View style={styles.warningBox}>
          <Text style={styles.warningText}>
            PDF/image extraction is not fully ready on this API host. {ocrStatus.messages?.[0]}
          </Text>
        </View>
      ) : null}

      <Card style={styles.card}>
        <TouchableOpacity style={styles.dropZone} onPress={pickFile} activeOpacity={0.7}>
          <View style={styles.iconCircle}>
            <Ionicons name={fileIcon as any} size={28} color={file ? colors.foreground : colors.muted} />
          </View>
          <Text style={styles.dropLabel} numberOfLines={1}>
            {file ? file.name : 'Tap to select transcript'}
          </Text>
          <Text style={styles.dropSub}>CSV, PDF, and transcript images</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.cameraBtn} onPress={openCamera} activeOpacity={0.8}>
          <Ionicons name="camera-outline" size={16} color={colors.foreground} />
          <Text style={styles.cameraBtnText}>Scan with Camera</Text>
        </TouchableOpacity>
      </Card>

      <View style={styles.section}>
        <SectionLabel>Target Program</SectionLabel>
        <ChipGroup
          options={auditOptions.programs.map((item: any) => ({ value: item.value, label: item.value }))}
          value={program}
          onChange={setProgram}
        />
      </View>

      <View style={styles.section}>
        <SectionLabel>Audit Mode</SectionLabel>
        <ChipGroup
          options={auditOptions.levels.map((item: any) => ({
            value: item.value,
            label: item.value === 'all' ? 'Full Audit' : item.value.toUpperCase(),
          }))}
          value={level}
          onChange={setLevel}
        />
        <Text style={styles.helperText}>{levelLabel(level)}</Text>
      </View>

      <TouchableOpacity
        style={styles.advancedToggle}
        onPress={() => setShowAdvanced((value) => !value)}
        activeOpacity={0.8}
      >
        <View style={styles.advancedLabel}>
          <Ionicons name="options-outline" size={16} color={colors.muted} />
          <Text style={styles.advancedText}>Advanced Options</Text>
        </View>
        <Ionicons
          name={showAdvanced ? 'chevron-up' : 'chevron-down'}
          size={16}
          color={colors.muted}
        />
      </TouchableOpacity>

      {showAdvanced ? (
        <Card style={styles.advancedCard}>
          {canChooseReport ? (
            <View style={styles.section}>
              <SectionLabel>Report Verbosity</SectionLabel>
              <ChipGroup
                options={auditOptions.report_modes.map((mode: string) => ({
                  value: mode,
                  label: mode === 'full' ? 'Full' : 'Normal',
                }))}
                value={report}
                onChange={setReport}
              />
            </View>
          ) : null}

          <View style={styles.section}>
            <SectionLabel>Waivers</SectionLabel>
            <TextInput
              style={styles.input}
              value={waiverInput}
              onChangeText={(value) => setWaiverInput(value.toUpperCase())}
              placeholder="ENG102,MAT112"
              placeholderTextColor={colors.muted}
              autoCapitalize="characters"
              autoCorrect={false}
            />
            {waivableCourses.length ? (
              <Text style={styles.helperText}>
                Known waivable courses for {program}: {waivableCourses.join(', ')}
              </Text>
            ) : null}
          </View>

          {showConcentration ? (
            <View style={styles.section}>
              <SectionLabel>BBA Concentration</SectionLabel>
              <ChipGroup
                options={[
                  { value: '', label: 'Auto' },
                  ...auditOptions.bba_concentrations.map((item: any) => ({
                    value: item.value,
                    label: item.value,
                  })),
                ]}
                value={concentration}
                onChange={setConcentration}
              />
            </View>
          ) : null}

          {showMinor ? (
            <View style={styles.section}>
              <SectionLabel>Minor</SectionLabel>
              <ChipGroup
                options={[
                  { value: '', label: 'None' },
                  ...auditOptions.supported_minors.map((item: string) => ({ value: item, label: item })),
                ]}
                value={minor}
                onChange={setMinor}
              />
            </View>
          ) : null}
        </Card>
      ) : null}

      {reviewPayload ? (
        <Card style={styles.advancedCard}>
          <SectionLabel>Review Required</SectionLabel>
          {(reviewPayload.warnings || []).map((warning: string) => (
            <Text key={warning} style={styles.warningText}>{warning}</Text>
          ))}
          <View style={styles.previewList}>
            {(reviewPayload.extracted_preview_rows || []).slice(0, 10).map((row: any, index: number) => (
              <View key={`${row.course_code}-${index}`} style={styles.previewRow}>
                <Text style={styles.previewPrimary}>
                  {row.course_code} · {row.grade} · {row.semester}
                </Text>
                <Text style={styles.previewSecondary}>
                  {row.credits} credits · confidence {Number(row.confidence || 0).toFixed(2)}
                </Text>
              </View>
            ))}
          </View>
          <PrimaryButton
            label={loading ? 'Running Review Audit...' : 'Run Audit With Extracted Rows'}
            onPress={runReviewedAudit}
            disabled={loading}
          />
        </Card>
      ) : null}

      <PrimaryButton
        label={loading ? (reviewPayload ? 'Running Review Audit...' : isScannedDocument ? 'Extracting Transcript...' : 'Running Audit...') : 'Run Complete Degree Audit'}
        onPress={runAudit}
        disabled={!file || loading}
        loading={loading}
        style={styles.cta}
      />
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  content: { padding: 24, paddingTop: 64, paddingBottom: 40, gap: 18 },
  header: { gap: 4 },
  heading: { fontFamily: 'InstrumentSerif_400Regular', fontSize: 34, color: colors.foreground },
  sub: { fontFamily: 'DMSans_400Regular', fontSize: 14, color: colors.muted, marginTop: 2 },
  heroBanner: {
    minHeight: 150,
    borderRadius: radius.card,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: colors.stroke,
  },
  heroBannerImage: { borderRadius: radius.card },
  heroOverlay: {
    flex: 1,
    justifyContent: 'flex-end',
    padding: 18,
    backgroundColor: 'rgba(250,248,245,0.32)',
  },
  heroEyebrow: {
    fontFamily: 'DMSans_600SemiBold',
    fontSize: 10,
    color: colors.muted,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  heroTitle: {
    maxWidth: 260,
    marginTop: 5,
    fontFamily: 'InstrumentSerif_400Regular',
    fontSize: 25,
    lineHeight: 27,
    color: colors.foreground,
  },
  card: { padding: 0, overflow: 'hidden' },
  dropZone: {
    alignItems: 'center',
    paddingVertical: 40,
    paddingHorizontal: 20,
    borderBottomWidth: 1,
    borderBottomColor: colors.stroke,
    gap: 10,
  },
  iconCircle: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: 'rgba(26,23,20,0.04)',
    borderWidth: 1,
    borderColor: colors.stroke,
    alignItems: 'center',
    justifyContent: 'center',
  },
  dropLabel: { fontFamily: 'DMSans_500Medium', fontSize: 15, color: colors.foreground, maxWidth: 260 },
  dropSub: { fontFamily: 'DMSans_400Regular', fontSize: 12, color: colors.muted },
  cameraBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 16,
  },
  cameraBtnText: { fontFamily: 'DMSans_500Medium', fontSize: 14, color: colors.foreground },
  section: { gap: 10 },
  chipWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: {
    minWidth: 72,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: radius.md,
    backgroundColor: 'rgba(26,23,20,0.04)',
    borderWidth: 1,
    borderColor: colors.stroke,
    alignItems: 'center',
  },
  chipActive: { backgroundColor: colors.foreground, borderColor: colors.foreground },
  chipText: { fontFamily: 'DMSans_500Medium', fontSize: 12, color: colors.muted },
  chipTextActive: { color: colors.background },
  helperText: { fontFamily: 'DMSans_400Regular', fontSize: 12, color: colors.muted },
  advancedToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderWidth: 1,
    borderColor: colors.stroke,
    borderRadius: radius.md,
    backgroundColor: 'rgba(255,255,255,0.5)',
    paddingHorizontal: 16,
    paddingVertical: 14,
  },
  advancedLabel: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  advancedText: { fontFamily: 'DMSans_500Medium', fontSize: 14, color: colors.foreground },
  advancedCard: { gap: 16 },
  input: {
    borderWidth: 1,
    borderColor: colors.stroke,
    borderRadius: radius.md,
    backgroundColor: 'rgba(255,255,255,0.7)',
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontFamily: 'DMSans_400Regular',
    color: colors.foreground,
    fontSize: 14,
  },
  cta: { marginTop: 4 },
  errorBox: {
    backgroundColor: '#FEF2F2',
    padding: 14,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: '#FECACA',
  },
  errorText: { fontFamily: 'DMSans_400Regular', color: '#DC2626', fontSize: 13 },
  warningBox: {
    backgroundColor: '#FFF7ED',
    padding: 14,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: '#FED7AA',
  },
  warningText: { fontFamily: 'DMSans_400Regular', color: '#C2410C', fontSize: 13 },
  previewList: { gap: 10, marginBottom: 12 },
  previewRow: {
    borderWidth: 1,
    borderColor: colors.stroke,
    borderRadius: radius.md,
    backgroundColor: 'rgba(255,255,255,0.7)',
    padding: 12,
    gap: 4,
  },
  previewPrimary: { fontFamily: 'DMSans_500Medium', fontSize: 13, color: colors.foreground },
  previewSecondary: { fontFamily: 'DMSans_400Regular', fontSize: 12, color: colors.muted },
})
