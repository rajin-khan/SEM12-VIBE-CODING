import { Slot } from 'expo-router'
import { View } from 'react-native'
import { colors } from '../../src/theme'

export default function AuthLayout() {
  return (
    <View style={{ flex: 1, backgroundColor: colors.background }}>
      <Slot />
    </View>
  )
}
