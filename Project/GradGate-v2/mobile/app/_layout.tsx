import { useEffect } from 'react'
import { Slot, useRouter, useSegments } from 'expo-router'
import { StatusBar } from 'expo-status-bar'
import { useFonts, InstrumentSerif_400Regular } from '@expo-google-fonts/instrument-serif'
import {
  DMSans_400Regular,
  DMSans_500Medium,
  DMSans_600SemiBold,
} from '@expo-google-fonts/dm-sans'
import { View } from 'react-native'
import { AuthProvider, useAuth } from '../src/lib/AuthContext'
import { colors } from '../src/theme'

function AuthGuard() {
  const { session, loading } = useAuth()
  const router = useRouter()
  const segments = useSegments()

  useEffect(() => {
    if (loading) return
    const inAuth = segments[0] === '(auth)'
    if (!session && !inAuth) {
      router.replace('/(auth)/login')
    } else if (session && inAuth) {
      router.replace('/(tabs)/')
    }
  }, [session, loading, segments])

  return <Slot />
}

export default function RootLayout() {
  const [fontsLoaded] = useFonts({
    InstrumentSerif_400Regular,
    DMSans_400Regular,
    DMSans_500Medium,
    DMSans_600SemiBold,
  })

  if (!fontsLoaded) {
    return <View style={{ flex: 1, backgroundColor: colors.background }} />
  }

  return (
    <AuthProvider>
      <StatusBar style="dark" />
      <AuthGuard />
    </AuthProvider>
  )
}
