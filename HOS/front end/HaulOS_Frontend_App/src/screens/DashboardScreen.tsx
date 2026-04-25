import React from 'react';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Text } from 'react-native';

import { Card, KVRow, PrimaryButton, Screen, SecondaryButton, SectionTitle, StatusPill } from '../components/UI';
import { RootStackParamList } from '../navigation/AppNavigator';
import { useHaulOS } from '../state/HaulOSContext';
import { API_BASE_URL } from '../config';

export function DashboardScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const {
    backendStatus,
    backendMessage,
    routeOptions,
    selectedRouteSummary,
    tripDraft,
    refreshSystem,
  } = useHaulOS();

  const statusTone = backendStatus === 'success' ? 'success' : backendStatus === 'error' ? 'danger' : backendStatus === 'loading' ? 'warning' : 'neutral';

  return (
    <Screen>
      <Card>
        <SectionTitle title="Backend link" subtitle="Front-end shell talking to your HaulOS backend." />
        <StatusPill text={backendStatus} tone={statusTone} />
        <KVRow label="API base URL" value={API_BASE_URL} />
        <Text style={{ color: '#9DB0C4' }}>{backendMessage || 'Tap refresh to test the backend.'}</Text>
        <SecondaryButton title="Refresh backend" onPress={() => void refreshSystem()} />
      </Card>

      <Card>
        <SectionTitle title="Driver flow" subtitle="This is the actual shell your driver would use." />
        <PrimaryButton title="Plan a trip" onPress={() => navigation.navigate('TripSetup')} />
        <SecondaryButton title="Open report hub" onPress={() => navigation.navigate('Reports')} />
        <SecondaryButton title="Open ops / admin" onPress={() => navigation.navigate('AdminTools')} />
      </Card>

      <Card>
        <SectionTitle title="Current trip snapshot" subtitle="Keeps your last draft and selected route in memory." />
        <KVRow label="Origin" value={tripDraft?.originLabel} />
        <KVRow label="Destination" value={tripDraft?.destinationLabel} />
        <KVRow label="Routes loaded" value={routeOptions.length} />
        <KVRow label="Selected route" value={selectedRouteSummary?.label} />
        {selectedRouteSummary ? (
          <PrimaryButton title="Go to route briefing" onPress={() => navigation.navigate('RouteBriefing')} />
        ) : null}
      </Card>
    </Screen>
  );
}
