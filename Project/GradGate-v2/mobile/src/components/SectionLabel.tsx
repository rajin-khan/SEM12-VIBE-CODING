import React from 'react'
import { View, Text, StyleSheet } from 'react-native'
import { colors, fonts } from '../../src/theme'

interface LabelProps {
  children: string
  icon?: React.ReactNode
}

export function SectionLabel({ children, icon }: LabelProps) {
  return (
    <View style={styles.row}>
      {icon && <View style={styles.icon}>{icon}</View>}
      <Text style={styles.text}>{children.toUpperCase()}</Text>
    </View>
  )
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 6,
  },
  icon: {
    opacity: 0.5,
  },
  text: {
    fontFamily: fonts.medium,
    fontSize: 11,
    letterSpacing: 1.5,
    color: colors.muted,
  },
})
