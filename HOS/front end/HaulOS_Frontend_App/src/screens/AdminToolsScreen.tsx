import React from 'react';
import { Text, View } from 'react-native';

import { Card, KVRow, PrimaryButton, Screen, SectionTitle, StatusPill } from '../components/UI';
import { useHaulOS } from '../state/HaulOSContext';

export function AdminToolsScreen() {
  const { profiles, bridges, refreshAdminData } = useHaulOS();

  return (
    <Screen>
      <Card>
        <SectionTitle title="Admin tools" subtitle="Read-only shell for import profiles and bridge assets." />
        <PrimaryButton title="Refresh admin data" onPress={() => void refreshAdminData()} />
      </Card>

      <Card>
        <SectionTitle title="Saved bridge import profiles" subtitle="Pulled from /v1/import-profiles/bridges." />
        {profiles.length === 0 ? (
          <Text style={{ color: '#9DB0C4' }}>No saved import profiles returned by the backend.</Text>
        ) : (
          profiles.map((profile) => (
            <View key={profile.profile_id} style={{ gap: 6, marginBottom: 14 }}>
              <StatusPill text={profile.name} tone="neutral" />
              <KVRow label="Vendor" value={profile.source_vendor} />
              <KVRow label="Version" value={profile.source_version} />
              <KVRow label="Auto update existing" value={profile.update_existing_default ? 'Yes' : 'No'} />
              <Text style={{ color: '#9DB0C4' }}>{JSON.stringify(profile.mapping_overrides)}</Text>
            </View>
          ))
        )}
      </Card>

      <Card>
        <SectionTitle title="Bridge assets" subtitle="Pulled from /v1/bridges. Useful for ops sanity checks." />
        {bridges.length === 0 ? (
          <Text style={{ color: '#9DB0C4' }}>No bridge assets returned by the backend.</Text>
        ) : (
          bridges.slice(0, 20).map((bridge) => (
            <View key={bridge.bridge_id} style={{ gap: 6, marginBottom: 14 }}>
              <Text style={{ color: '#F4F7FB', fontWeight: '700' }}>{bridge.name || bridge.asset_code || bridge.bridge_id}</Text>
              <KVRow label="Road" value={bridge.road_name} />
              <KVRow label="Locality" value={bridge.locality} />
              <KVRow label="Height" value={bridge.clearance_height_m} />
              <KVRow label="Width" value={bridge.clearance_width_m} />
              <KVRow label="Mass" value={bridge.max_mass_t} />
            </View>
          ))
        )}
      </Card>
    </Screen>
  );
}
