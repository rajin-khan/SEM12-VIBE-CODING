import React from 'react'
import { View, Text, StyleSheet } from 'react-native'
import { colors, fonts } from '../../src/theme'

interface LogoMarkProps {
  size?: 'sm' | 'md' | 'lg'
}

export function LogoMark({ size = 'md' }: LogoMarkProps) {
  const scale = size === 'sm' ? 0.7 : size === 'lg' ? 1.4 : 1

  return (
    <View style={[styles.row, { gap: 8 * scale }]}>
      {/* The two-bar bracket mark */}
      <View style={[styles.mark, { width: 14 * scale, height: 18 * scale }]}>
        <View style={[styles.bar, styles.barLeft, { height: 18 * scale }]} />
        <View style={[styles.bar, styles.barRight, { height: 18 * scale }]} />
        <View style={[styles.dot, {
          width: 7 * scale,
          height: 7 * scale,
          bottom: 3 * scale,
          borderRadius: 99,
        }]} />
      </View>
      <Text style={[styles.wordmark, { fontSize: 26 * scale }]}>GradGate</Text>
    </View>
  )
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  mark: {
    position: 'relative',
    justifyContent: 'flex-end',
    flexDirection: 'row',
    alignItems: 'flex-end',
  },
  bar: {
    width: 2,
    backgroundColor: colors.foreground,
    borderRadius: 1,
    position: 'absolute',
    top: 0,
  },
  barLeft: { left: 0 },
  barRight: { right: 0 },
  dot: {
    backgroundColor: colors.foreground,
    position: 'absolute',
    left: '50%',
    marginLeft: -3.5,
  },
  wordmark: {
    fontFamily: fonts.display,
    color: colors.foreground,
  },
})
