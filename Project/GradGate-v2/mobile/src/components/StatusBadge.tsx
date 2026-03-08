import React from 'react'
import { View, Text, StyleSheet } from 'react-native'
import { colors, fonts, radius } from '../../src/theme'

interface StatusBadgeProps {
  eligible: boolean
}

export function StatusBadge({ eligible }: StatusBadgeProps) {
  return (
    <View style={[styles.badge, eligible ? styles.green : styles.red]}>
      <Text style={[styles.text, eligible ? styles.greenText : styles.redText]}>
        {eligible ? 'ELIGIBLE' : 'DEFICIENT'}
      </Text>
    </View>
  )
}

const styles = StyleSheet.create({
  badge: {
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: radius.pill,
    alignSelf: 'flex-start',
  },
  green: { backgroundColor: colors.greenBg },
  red: { backgroundColor: colors.redBg },
  text: {
    fontFamily: fonts.semi,
    fontSize: 12,
    letterSpacing: 1,
  },
  greenText: { color: colors.green },
  redText: { color: colors.red },
})
