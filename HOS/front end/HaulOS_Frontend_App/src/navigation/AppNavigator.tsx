import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

import { DashboardScreen } from '../screens/DashboardScreen';
import { TripSetupScreen } from '../screens/TripSetupScreen';
import { RouteOptionsScreen } from '../screens/RouteOptionsScreen';
import { RouteBriefingScreen } from '../screens/RouteBriefingScreen';
import { LiveTripScreen } from '../screens/LiveTripScreen';
import { ReportsScreen } from '../screens/ReportsScreen';
import { AdminToolsScreen } from '../screens/AdminToolsScreen';

export type RootStackParamList = {
  Dashboard: undefined;
  TripSetup: undefined;
  RouteOptions: undefined;
  RouteBriefing: undefined;
  LiveTrip: undefined;
  Reports: undefined;
  AdminTools: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();

export function AppNavigator() {
  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: { backgroundColor: '#08111C' },
        headerTintColor: '#F4F7FB',
        contentStyle: { backgroundColor: '#08111C' },
      }}
    >
      <Stack.Screen name="Dashboard" component={DashboardScreen} options={{ title: 'HaulOS' }} />
      <Stack.Screen name="TripSetup" component={TripSetupScreen} options={{ title: 'Plan Trip' }} />
      <Stack.Screen name="RouteOptions" component={RouteOptionsScreen} options={{ title: 'Route Options' }} />
      <Stack.Screen name="RouteBriefing" component={RouteBriefingScreen} options={{ title: 'Route Briefing' }} />
      <Stack.Screen name="LiveTrip" component={LiveTripScreen} options={{ title: 'Live Trip' }} />
      <Stack.Screen name="Reports" component={ReportsScreen} options={{ title: 'Reports' }} />
      <Stack.Screen name="AdminTools" component={AdminToolsScreen} options={{ title: 'Ops / Admin' }} />
    </Stack.Navigator>
  );
}
