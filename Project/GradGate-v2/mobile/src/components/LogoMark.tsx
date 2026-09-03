import React from 'react'
import { Image, View, Text, StyleSheet } from 'react-native'
import { colors, fonts } from '../../src/theme'

const emblem = require('../../assets/brand/gradgate-emblem-ui.png')

interface LogoMarkProps {
  size?: 'sm' | 'md' | 'lg'
}

export function LogoMark({ size = 'md' }: LogoMarkProps) {
  const scale = size === 'sm' ? 0.7 : size === 'lg' ? 1.4 : 1

  return (
    <View style={[styles.row, { gap: 8 * scale }]}>
      <Image
        source={emblem}
        style={[styles.emblem, { width: 27 * scale, height: 27 * scale, borderRadius: 8 * scale }]}
      />
      <Text style={[styles.wordmark, { fontSize: 26 * scale }]}>GradGate</Text>
    </View>
  )
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  emblem: {
    borderWidth: 1,
    borderColor: colors.stroke,
  },
  wordmark: {
    fontFamily: fonts.display,
    color: colors.foreground,
  },
})
