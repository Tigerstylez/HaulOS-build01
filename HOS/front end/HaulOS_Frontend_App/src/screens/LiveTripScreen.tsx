import React, { useEffect } from 'react';
import { Text, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { Card, KVRow, MapPlaceholder, PrimaryButton, Screen, SectionTitle, StatusPill } from '../components/UI';
import { RootStackParamList } from '../navigation/AppNavigator';
import { useHaulOS } from '../state/HaulOSContext';

export function LiveTripScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const { routeDetail, upcomingEvents, refreshUpcomingEvents } = useHaulOS();

  useEffect(() => {
    void refreshUpcomingEvents();
    const timer = setInterval(() => {
      void refreshUpcomingEvents();
    }, 15000);
    return () => clearInterval(timer);
  }, [refreshUpcomingEvents]);

  if (!routeDetail) {
    return (
      <Screen>
        <Card>
          <SectionTitle title="No live trip yet" subtitle="Start from the route briefing screen." />
        </Card>
      </Screen>
    );
  }

  return (
    <Screen>
      <MapPlaceholder
        title="Live navigation shell"
        subtitle="Swap this placeholder for your real map later. The event feed underneath is already live from the backend."
      />

      <Card>
        <SectionTitle title="Trip pulse" subtitle="What matters right now." />
        <KVRow label="Route" value={routeDetail.label} />
        <KVRow label="Managed passage" value={routeDetail.managed_passage_required ? 'Yes' : 'No'} />
        <KVRow label="Upcoming events" value={upcomingEvents.length} />
        <PrimaryButton title="Refresh live events" onPress={() => void refreshUpcomingEvents()} />
      </Card>

      <Card>
        <SectionTitle title="Upcoming alerts" subtitle="Approach warnings, hazards, contra flow and utility windows." />
        {upcomingEvents.length === 0 ? (
          <Text style={{ color: '#9DB0C4' }}>No events loaded yet.</Text>
        ) : (
          upcomingEvents.map((event) => (
            <View key={event.event_id} style={{ gap: 6, marginBottom: 14 }}>
              <StatusPill text={`${event.event_type}${event.event_subtype ? ` · ${event.event_subtype}` : ''}`} tone={event.requires_acknowledgement ? 'warning' : 'neutral'} />
              <Text style={{ color: '#F4F7FB', fontWeight: '700' }}>{event.title}</Text>
              <Text style={{ color: '#9DB0C4' }}>{event.driver_message}</Text>
              <KVRow label="Location" value={event.location_name} />
              <KVRow label="Distance to event" value={`${event.distance_to_event_km} km`} />
              <KVRow label="Triggers" value={event.trigger_distances_km.join(', ')} />
            </View>
          ))
        )}
      </Card>

      <Card>
        <SectionTitle title="Managed passage watch" subtitle="The driver should never miss these." />
        {routeDetail.segments
          .filter((segment) => String(segment.managed_movement?.movement_type || 'none') !== 'none')
          .map((segment) => (
            <View key={segment.segment_id} style={{ gap: 6, marginBottom: 14 }}>
              <StatusPill text={String(segment.managed_movement?.movement_type || 'managed')} tone="warning" />
              <Text style={{ color: '#F4F7FB', fontWeight: '700' }}>{segment.location_name}</Text>
              <Text style={{ color: '#9DB0C4' }}>{String(segment.managed_movement?.driver_message || 'Await instruction before movement.')}</Text>
            </View>
          ))}
      </Card>

      <PrimaryButton title="Open report hub" onPress={() => navigation.navigate('Reports')} />
    </Screen>
  );
}
