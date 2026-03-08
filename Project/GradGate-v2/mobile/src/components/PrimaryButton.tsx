import React from 'react'
import { TouchableOpacity, Text, StyleSheet, ViewStyle, ActivityIndicator } from 'react-native'
import { colors, fonts, radius } from '../../src/theme'

interface PrimaryButtonProps {
  label: string
  onPress: () => void
  disabled?: boolean
  loading?: boolean
  style?: ViewStyle
  variant?: 'primary' | 'ghost' | 'outline'
}

export function PrimaryButton({ label, onPress, disabled, loading, style, variant = 'primary' }: PrimaryButtonProps) {
  const variantStyle = variant === 'ghost'
    ? styles.ghost
    : variant === 'outline'
    ? styles.outline
    : styles.primary

  const textStyle = variant === 'primary' ? styles.primaryText : styles.ghostText

  return (
    <TouchableOpacity
      style={[styles.base, variantStyle, (disabled || loading) && styles.disabled, style]}
      onPress={onPress}
      activeOpacity={0.8}
      disabled={disabled || loading}
    >
      {loading
        ? <ActivityIndicator size="small" color={variant === 'primary' ? colors.background : colors.foreground} />
        : <Text style={textStyle}>{label}</Text>
      }
    </TouchableOpacity>
  )
}

const styles = StyleSheet.create({
  base: {
    height: 52,
    borderRadius: radius.sm,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 24,
  },
  primary: {
    backgroundColor: colors.foreground,
  },
  ghost: {
    backgroundColor: 'transparent',
  },
  outline: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: colors.strokeMed,
  },
  disabled: {
    opacity: 0.4,
  },
  primaryText: {
    fontFamily: fonts.semi,
    fontSize: 15,
    color: colors.background,
    letterSpacing: 0.1,
  },
  ghostText: {
    fontFamily: fonts.medium,
    fontSize: 14,
    color: colors.muted,
  },
})
