import React from 'react';
import { NavigationContainer, DarkTheme } from '@react-navigation/native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { StatusBar } from 'react-native';

import { HaulOSProvider } from './src/state/HaulOSContext';
import { AppNavigator } from './src/navigation/AppNavigator';

export default function App() {
  return (
    <SafeAreaProvider>
      <HaulOSProvider>
        <NavigationContainer theme={DarkTheme}>
          <StatusBar barStyle="light-content" />
          <AppNavigator />
        </NavigationContainer>
      </HaulOSProvider>
    </SafeAreaProvider>
  );
}
