import React from 'react';
import { Text, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { Card, Divider, KVRow, MapPlaceholder, PrimaryButton, Screen, SectionTitle, StatusPill } from '../components/UI';
import { RootStackParamList } from '../navigation/AppNavigator';
import { useHaulOS } from '../state/HaulOSContext';

export function RouteBriefingScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const { routeDetail, selectedRouteSummary } = useHaulOS();

  if (!routeDetail || !selectedRouteSummary) {
    return (
      <Screen>
        <Card>
          <SectionTitle title="No route selected" subtitle="Pick a route first." />
        </Card>
      </Screen>
    );
  }

  return (
    <Screen>
      <MapPlaceholder
        title={selectedRouteSummary.label}
        subtitle={routeDetail.managed_passage_required ? 'Managed passage route shown on purpose — not hidden.' : 'Clean/legal route selected.'}
      />

      <Card>
        <SectionTitle title="Route summary" subtitle="This is the pre-departure briefing block." />
        <StatusPill
          text={routeDetail.managed_passage_required ? 'Managed passage' : routeDetail.legal_status}
          tone={routeDetail.managed_passage_required ? 'warning' : 'success'}
        />
        <KVRow label="Distance" value={`${routeDetail.summary.distance_km} km`} />
        <KVRow label="ETA" value={`${routeDetail.summary.eta_minutes} min`} />
        <KVRow label="Hazards" value={routeDetail.summary.hazard_count} />
        <KVRow label="Managed reasons" value={routeDetail.managed_passage_reasons.join(', ') || 'None'} />
      </Card>

      <Card>
        <SectionTitle title="Stage plan" subtitle="RTAA and combination change logic lives here." />
        {routeDetail.stages?.map((stage, index) => (
          <View key={`${stage.stage_number}-${index}`} style={{ gap: 8, marginBottom: 14 }}>
            <StatusPill text={`Stage ${stage.stage_number}: ${stage.stage_type}`} tone={stage.action_required ? 'warning' : 'neutral'} />
            <KVRow label="Start" value={stage.start_location_name || stage.start_combination_type} />
            <KVRow label="End" value={stage.end_location_name || stage.end_combination_type} />
            <KVRow label="Action required" value={stage.action_required || 'None'} />
            <KVRow label="Action status" value={stage.action_status || 'n/a'} />
            {stage.notes ? <Text style={{ color: '#9DB0C4' }}>{stage.notes}</Text> : null}
            {index < (routeDetail.stages?.length || 0) - 1 ? <Divider /> : null}
          </View>
        ))}
      </Card>

      <Card>
        <SectionTitle title="Risk briefing" subtitle="This is what the driver sees before wheels turn." />
        {routeDetail.pre_departure_briefing.map((item) => (
          <View key={item.briefing_id} style={{ gap: 6, marginBottom: 14 }}>
            <StatusPill text={`${item.briefing_type} · ${item.severity}`} tone={item.departure_allowed ? 'neutral' : 'warning'} />
            <Text style={{ color: '#F4F7FB', fontWeight: '700' }}>{item.title}</Text>
            <Text style={{ color: '#9DB0C4' }}>{item.driver_message}</Text>
            {item.location_name ? <Text style={{ color: '#9DB0C4' }}>Location: {item.location_name}</Text> : null}
          </View>
        ))}
      </Card>

      <Card>
        <SectionTitle title="Segment preview" subtitle="Including contra flow or utility actions where flagged." />
        {routeDetail.segments.slice(0, 8).map((segment) => (
          <View key={segment.segment_id} style={{ gap: 6, marginBottom: 14 }}>
            <Text style={{ color: '#F4F7FB', fontWeight: '700' }}>{segment.road_name}</Text>
            <Text style={{ color: '#9DB0C4' }}>{segment.location_name}</Text>
            <KVRow label="Distance" value={`${segment.distance_km} km`} />
            <KVRow label="Managed movement" value={String(segment.managed_movement?.movement_type || 'none')} />
            <KVRow label="Stage" value={segment.stage_number ?? '—'} />
          </View>
        ))}
      </Card>

      <PrimaryButton title="Start live trip" onPress={() => navigation.navigate('LiveTrip')} />
    </Screen>
  );
}
