import { useState, useRef } from 'react'
import {
  View, Text, ScrollView, StyleSheet, TouchableOpacity,
  Alert, Platform, ActivityIndicator
} from 'react-native'
import { useRouter } from 'expo-router'
import * as ImagePicker from 'expo-image-picker'
import * as DocumentPicker from 'expo-document-picker'
import { Ionicons } from '@expo/vector-icons'
import { useAuth } from '../../src/lib/AuthContext'
import { auditCSV, auditImage } from '../../src/lib/api'
import { Card } from '../../src/components/Card'
import { PrimaryButton } from '../../src/components/PrimaryButton'
import { SectionLabel } from '../../src/components/SectionLabel'
import { colors, fonts, radius } from '../../src/theme'

const PROGRAMS = [
  { value: 'CSE', label: 'CSE' },
  { value: 'BBA', label: 'BBA' },
  { value: 'EEE', label: 'EEE' },
  { value: 'ETE', label: 'ETE' },
]

export default function UploadScreen() {
  const { session } = useAuth()
  const router = useRouter()
  const [file, setFile] = useState<{ uri: string; name: string; type: string } | null>(null)
  const [program, setProgram] = useState('CSE')
  const [loading, setLoading] = useState(false)

  const pickFile = async () => {
    const result = await DocumentPicker.getDocumentAsync({
      type: ['text/csv', 'application/pdf', 'image/png', 'image/jpeg'],
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
      const name = `transcript_${Date.now()}.jpg`
      setFile({ uri: asset.uri, name, type: 'image/jpeg' })
    }
  }

  const runAudit = async () => {
    if (!file || !session) return
    setLoading(true)
    try {
      const isCSV = file.name.endsWith('.csv') || file.type === 'text/csv'
      const data = isCSV
        ? await auditCSV(session, file.uri, file.name, program)
        : await auditImage(session, file.uri, file.name, file.type, program)
      router.push(`/results/${data.scan_id}`)
    } catch (e: any) {
      Alert.alert('Audit failed', e.message)
    } finally {
      setLoading(false)
    }
  }

  const fileIsImage = file && !file.name.endsWith('.csv')

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
    >
      <View style={styles.header}>
        <SectionLabel>New Audit</SectionLabel>
        <Text style={styles.heading}>Upload Transcript</Text>
        <Text style={styles.sub}>Analyze your degree progress instantly.</Text>
      </View>

      <Card style={styles.card}>
        {/* Upload zone */}
        <TouchableOpacity style={styles.dropZone} onPress={pickFile} activeOpacity={0.7}>
          <View style={styles.iconCircle}>
            <Ionicons
              name={file ? (fileIsImage ? 'image-outline' : 'document-text-outline') : 'cloud-upload-outline'}
              size={28}
              color={file ? colors.foreground : colors.muted}
            />
          </View>
          <Text style={styles.dropLabel} numberOfLines={1}>
            {file ? file.name : 'Tap to select transcript'}
          </Text>
          <Text style={styles.dropSub}>CSV, PDF, PNG, or JPG</Text>
        </TouchableOpacity>

        {/* Camera */}
        <TouchableOpacity style={styles.cameraBtn} onPress={openCamera} activeOpacity={0.8}>
          <Ionicons name="camera-outline" size={16} color={colors.foreground} />
          <Text style={styles.cameraBtnText}>Scan with Camera</Text>
        </TouchableOpacity>
      </Card>

      {/* Program selector */}
      <View style={styles.section}>
        <SectionLabel>Target Program</SectionLabel>
        <View style={styles.programRow}>
          {PROGRAMS.map(p => (
            <TouchableOpacity
              key={p.value}
              style={[styles.programChip, program === p.value && styles.programChipActive]}
              onPress={() => setProgram(p.value)}
              activeOpacity={0.7}
            >
              <Text style={[styles.programChipText, program === p.value && styles.programChipTextActive]}>
                {p.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      <PrimaryButton
        label={loading ? 'Running Audit...' : 'Run Complete Degree Audit'}
        onPress={runAudit}
        disabled={!file}
        loading={loading}
        style={styles.cta}
      />
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  content: { padding: 24, paddingTop: 64, paddingBottom: 40, gap: 20 },
  header: { gap: 4 },
  heading: { fontFamily: 'InstrumentSerif_400Regular', fontSize: 34, color: colors.foreground },
  sub: { fontFamily: 'DMSans_400Regular', fontSize: 14, color: colors.muted, marginTop: 2 },
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
  programRow: { flexDirection: 'row', gap: 8 },
  programChip: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: radius.md,
    backgroundColor: 'rgba(26,23,20,0.04)',
    borderWidth: 1,
    borderColor: colors.stroke,
    alignItems: 'center',
  },
  programChipActive: { backgroundColor: colors.foreground, borderColor: colors.foreground },
  programChipText: { fontFamily: 'DMSans_500Medium', fontSize: 13, color: colors.muted },
  programChipTextActive: { color: colors.background },
  cta: { marginTop: 4 },
})
