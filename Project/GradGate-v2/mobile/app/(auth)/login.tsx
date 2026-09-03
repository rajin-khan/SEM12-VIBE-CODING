import { useState } from 'react'
import { ImageBackground, View, Text, TouchableOpacity, StyleSheet, Alert } from 'react-native'
import { useRouter } from 'expo-router'
import * as WebBrowser from 'expo-web-browser'
import { makeRedirectUri } from 'expo-auth-session'
import { supabase } from '../../src/lib/supabase'
import { LogoMark } from '../../src/components/LogoMark'
import { PrimaryButton } from '../../src/components/PrimaryButton'
import { colors, fonts, radius } from '../../src/theme'

WebBrowser.maybeCompleteAuthSession()

const paperGrid = require('../../assets/brand/gradgate-paper-grid.png')

export default function LoginScreen() {
  const [loading, setLoading] = useState(false)

  const handleGoogleLogin = async () => {
    setLoading(true)
    try {
      const redirectUri = makeRedirectUri({ scheme: 'gradgate', path: 'auth/callback' })
      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: { redirectTo: redirectUri, skipBrowserRedirect: true },
      })
      if (error) throw error
      if (data?.url) {
        const result = await WebBrowser.openAuthSessionAsync(data.url, redirectUri)
        if (result.type === 'success') {
          const url = result.url
          const params = new URLSearchParams(url.split('#')[1])
          const access_token = params.get('access_token')
          const refresh_token = params.get('refresh_token')
          if (access_token && refresh_token) {
            await supabase.auth.setSession({ access_token, refresh_token })
          }
        }
      }
    } catch (e: any) {
      Alert.alert('Sign in error', e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <ImageBackground source={paperGrid} style={styles.container} imageStyle={styles.backgroundImage}>
      <View style={styles.inner}>
        {/* Logo */}
        <LogoMark size="lg" />
        <Text style={styles.tagline}>Audit smarter. Graduate faster.</Text>

        {/* Card */}
        <View style={styles.card}>
          <Text style={styles.title}>Welcome back</Text>
          <Text style={styles.subtitle}>Sign in to access your audits and history.</Text>

          <View style={styles.divider} />

          {/* Google button */}
          <TouchableOpacity
            style={[styles.googleBtn, loading && { opacity: 0.5 }]}
            onPress={handleGoogleLogin}
            disabled={loading}
            activeOpacity={0.8}
          >
            {/* Google G */}
            <View style={styles.googleG}>
              <Text style={styles.googleGText}>G</Text>
            </View>
            <Text style={styles.googleBtnText}>
              {loading ? 'Opening browser...' : 'Continue with Google'}
            </Text>
          </TouchableOpacity>

          <Text style={styles.terms}>
            By signing in, you agree to our{'\n'}Terms of Service and Privacy Policy.
          </Text>
        </View>
      </View>
    </ImageBackground>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  backgroundImage: {
    opacity: 0.18,
  },
  inner: {
    width: '100%',
    maxWidth: 380,
    alignItems: 'center',
    gap: 20,
  },
  tagline: {
    fontFamily: fonts.body,
    fontSize: 14,
    color: colors.muted,
    marginTop: 4,
  },
  card: {
    width: '100%',
    backgroundColor: 'rgba(255,255,255,0.9)',
    borderRadius: radius.card,
    padding: 28,
    borderWidth: 1,
    borderColor: colors.stroke,
    shadowColor: '#1A1714',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.07,
    shadowRadius: 20,
    gap: 12,
  },
  title: {
    fontFamily: 'InstrumentSerif_400Regular',
    fontSize: 24,
    color: colors.foreground,
  },
  subtitle: {
    fontFamily: fonts.body,
    fontSize: 14,
    color: colors.muted,
    lineHeight: 21,
  },
  divider: {
    height: 1,
    backgroundColor: colors.stroke,
    marginVertical: 4,
  },
  googleBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.foreground,
    borderRadius: radius.sm,
    height: 52,
    gap: 12,
  },
  googleG: {
    width: 20,
    height: 20,
    backgroundColor: colors.background,
    borderRadius: 3,
    alignItems: 'center',
    justifyContent: 'center',
  },
  googleGText: {
    fontFamily: fonts.semi,
    fontSize: 13,
    color: colors.foreground,
  },
  googleBtnText: {
    fontFamily: fonts.semi,
    fontSize: 15,
    color: colors.background,
  },
  terms: {
    fontFamily: fonts.body,
    fontSize: 11,
    color: colors.muted,
    textAlign: 'center',
    lineHeight: 17,
  },
})
