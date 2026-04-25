import React from 'react';
import { Alert, Text, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { Card, Divider, KVRow, MapPlaceholder, PrimaryButton, Screen, SectionTitle, StatusPill } from '../components/UI';
import { RootStackParamList } from '../navigation/AppNavigator';
import { useHaulOS } from '../state/HaulOSContext';
import { RouteSummary } from '../types/api';

function RouteCard({ route, onSelect }: { route: RouteSummary; onSelect: () => void }) {
  const tone = route.managed_passage_required ? 'warning' : route.legal_status === 'legal' ? 'success' : 'neutral';
  return (
    <Card>
      <SectionTitle title={route.label} subtitle={`${route.distance_km} km · ETA ${route.eta_minutes} min`} />
      <StatusPill text={route.route_status} tone={tone} />
      <KVRow label="Route class" value={route.route_class} />
      <KVRow label="Legal status" value={route.legal_status} />
      <KVRow label="Approval status" value={route.approval_status} />
      <KVRow label="Hazards" value={route.hazard_count} />
      <KVRow label="Restrictions" value={route.restriction_count} />
      <KVRow label="Managed passage" value={route.managed_passage_required ? route.managed_passage_reasons.join(', ') : 'No'} />
      <PrimaryButton title="Use this route" onPress={onSelect} />
    </Card>
  );
}

export function RouteOptionsScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const { routeOptions, chooseRoute } = useHaulOS();

  async function handleChoose(route: RouteSummary) {
    try {
      await chooseRoute(route);
      navigation.navigate('RouteBriefing');
    } catch (error) {
      Alert.alert('Route load failed', error instanceof Error ? error.message : 'Unknown error');
    }
  }

  return (
    <Screen>
      <MapPlaceholder
        title="Map shell ready"
        subtitle="Replace this placeholder with Mapbox later. The route selection logic is already wired to the backend."
      />

      {routeOptions.length === 0 ? (
        <Card>
          <SectionTitle title="No routes loaded" subtitle="Go back to Trip Setup and calculate a trip first." />
        </Card>
      ) : (
        <View style={{ gap: 16 }}>
          {routeOptions.map((route, index) => (
            <React.Fragment key={route.route_id || `${route.label}-${index}`}>
              <RouteCard route={route} onSelect={() => void handleChoose(route)} />
              {index < routeOptions.length - 1 ? <Divider /> : null}
            </React.Fragment>
          ))}
        </View>
      )}
    </Screen>
  );
}
