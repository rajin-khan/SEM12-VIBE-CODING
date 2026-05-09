import React from 'react'
import { View, ViewStyle, StyleSheet, StyleProp } from 'react-native'
import { colors, radius, shadow } from '../../src/theme'

interface CardProps {
  children: React.ReactNode
  style?: StyleProp<ViewStyle>
  variant?: 'default' | 'tinted'
}

export function Card({ children, style, variant = 'default' }: CardProps) {
  return (
    <View style={[styles.card, variant === 'tinted' && styles.tinted, style]}>
      {children}
    </View>
  )
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: 'rgba(255, 255, 255, 0.85)',
    borderRadius: radius.card,
    padding: 20,
    borderWidth: 1,
    borderColor: colors.stroke,
    ...shadow.md,
  },
  tinted: {
    backgroundColor: colors.surface,
  },
})
