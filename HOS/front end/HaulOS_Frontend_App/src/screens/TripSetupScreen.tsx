import React, { useMemo, useState } from 'react';
import { Alert, Text, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { Card, Chip, Label, PrimaryButton, Screen, SectionTitle, TextField } from '../components/UI';
import { RootStackParamList } from '../navigation/AppNavigator';
import { useHaulOS } from '../state/HaulOSContext';
import { TripCreateRequest } from '../types/api';

const comboOptions = ['semi', 'b_double', 'a_double', 'road_train', 'short_triple_road_train'];
const platformOptions = ['flat_top', 'drop_deck', 'low_loader', 'extendable', 'widener', 'skel', 'tanker', 'tipper'];
const directions = ['inland_north', 'coastal_north', 'south', 'east'];

function parseNumber(input: string, fallback: number) {
  const value = Number(input);
  return Number.isFinite(value) && value > 0 ? value : fallback;
}

export function TripSetupScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const { locations, createTripAndCalculate } = useHaulOS();

  const [originLabel, setOriginLabel] = useState('Perth Depot');
  const [destinationLabel, setDestinationLabel] = useState('Newman');
  const [combinationType, setCombinationType] = useState('semi');
  const [trailerCount, setTrailerCount] = useState('1');
  const [platformType, setPlatformType] = useState('drop_deck');
  const [targetCombinationType, setTargetCombinationType] = useState('short_triple_road_train');
  const [targetTrailerCount, setTargetTrailerCount] = useState('3');
  const [routeDirection, setRouteDirection] = useState('inland_north');
  const [requiresRTAA, setRequiresRTAA] = useState(true);
  const [rtaaName, setRTAAName] = useState('Wubin RTAA');
  const [heightM, setHeightM] = useState('5.2');
  const [widthM, setWidthM] = useState('7.0');
  const [lengthM, setLengthM] = useState('36.0');
  const [grossMassT, setGrossMassT] = useState('68.0');
  const [permitsHeld, setPermitsHeld] = useState(true);
  const [hazmat, setHazmat] = useState(false);
  const [loading, setLoading] = useState(false);

  const draft = useMemo<TripCreateRequest>(() => ({
    originLabel,
    destinationLabel,
    vehicle: {
      combination_type: combinationType,
      trailer_count: parseNumber(trailerCount, 1),
      platform_type: platformType,
      target_combination_type: targetCombinationType,
      target_trailer_count: parseNumber(targetTrailerCount, 3),
      route_direction: routeDirection,
      requires_rtaa_reconfiguration: requiresRTAA,
      rtaa_name: requiresRTAA ? rtaaName : undefined,
      height_m: parseNumber(heightM, 5.2),
      width_m: parseNumber(widthM, 7.0),
      length_m: parseNumber(lengthM, 36.0),
      gross_mass_t: parseNumber(grossMassT, 68.0),
      is_road_train: combinationType.includes('road_train') || targetCombinationType.includes('road_train'),
      is_oversize: parseNumber(widthM, 7.0) > 2.6 || parseNumber(heightM, 5.2) > 4.3,
      hazmat,
      permits_held: permitsHeld,
      metadata_json: {
        notes: 'Created from the front-end shell.',
      },
    },
  }), [combinationType, destinationLabel, grossMassT, hazmat, heightM, lengthM, originLabel, permitsHeld, platformType, requiresRTAA, routeDirection, rtaaName, targetCombinationType, targetTrailerCount, trailerCount, widthM]);

  async function handleCreateTrip() {
    try {
      setLoading(true);
      await createTripAndCalculate(draft);
      navigation.navigate('RouteOptions');
    } catch (error) {
      Alert.alert('Trip setup failed', error instanceof Error ? error.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }

  return (
    <Screen>
      <Card>
        <SectionTitle title="Trip path" subtitle="Use demo labels or replace them with your own backend locations later." />
        <Label text="Origin" />
        <TextField value={originLabel} onChangeText={setOriginLabel} placeholder="Perth Depot" />
        <Label text="Destination" />
        <TextField value={destinationLabel} onChangeText={setDestinationLabel} placeholder="Newman" />
        <Text style={{ color: '#9DB0C4' }}>Quick picks: {locations.join(', ')}</Text>
      </Card>

      <Card>
        <SectionTitle title="Combination plan" subtitle="Combination type and platform type stay separate in HaulOS." />
        <Label text="Current combination" />
        <View style={{ flexDirection: 'row', flexWrap: 'wrap' }}>
          {comboOptions.map((item) => (
            <Chip key={item} title={item} selected={combinationType === item} onPress={() => setCombinationType(item)} />
          ))}
        </View>
        <Label text="Current trailer count" />
        <TextField value={trailerCount} onChangeText={setTrailerCount} keyboardType="number-pad" />
        <Label text="Platform type" />
        <View style={{ flexDirection: 'row', flexWrap: 'wrap' }}>
          {platformOptions.map((item) => (
            <Chip key={item} title={item} selected={platformType === item} onPress={() => setPlatformType(item)} />
          ))}
        </View>
      </Card>

      <Card>
        <SectionTitle title="RTAA reconfiguration" subtitle="Built for Wubin / Carnarvon logic and future network rules." />
        <View style={{ flexDirection: 'row', flexWrap: 'wrap' }}>
          <Chip title="RTAA required" selected={requiresRTAA} onPress={() => setRequiresRTAA(true)} />
          <Chip title="No RTAA" selected={!requiresRTAA} onPress={() => setRequiresRTAA(false)} />
        </View>
        <Label text="Route direction" />
        <View style={{ flexDirection: 'row', flexWrap: 'wrap' }}>
          {directions.map((item) => (
            <Chip key={item} title={item} selected={routeDirection === item} onPress={() => setRouteDirection(item)} />
          ))}
        </View>
        <Label text="Target combination" />
        <View style={{ flexDirection: 'row', flexWrap: 'wrap' }}>
          {comboOptions.map((item) => (
            <Chip key={item} title={item} selected={targetCombinationType === item} onPress={() => setTargetCombinationType(item)} />
          ))}
        </View>
        <Label text="Target trailer count" />
        <TextField value={targetTrailerCount} onChangeText={setTargetTrailerCount} keyboardType="number-pad" />
        <Label text="RTAA name" />
        <TextField value={rtaaName} onChangeText={setRTAAName} placeholder="Wubin RTAA" />
      </Card>

      <Card>
        <SectionTitle title="Load and compliance" subtitle="These values drive route legality and managed-passage logic." />
        <Label text="Height (m)" />
        <TextField value={heightM} onChangeText={setHeightM} keyboardType="numeric" />
        <Label text="Width (m)" />
        <TextField value={widthM} onChangeText={setWidthM} keyboardType="numeric" />
        <Label text="Length (m)" />
        <TextField value={lengthM} onChangeText={setLengthM} keyboardType="numeric" />
        <Label text="Gross mass (t)" />
        <TextField value={grossMassT} onChangeText={setGrossMassT} keyboardType="numeric" />
        <View style={{ flexDirection: 'row', flexWrap: 'wrap' }}>
          <Chip title="Permits held" selected={permitsHeld} onPress={() => setPermitsHeld((v) => !v)} />
          <Chip title="Hazmat" selected={hazmat} onPress={() => setHazmat((v) => !v)} />
        </View>
      </Card>

      <PrimaryButton title={loading ? 'Working…' : 'Create trip and calculate routes'} onPress={() => void handleCreateTrip()} disabled={loading} />
    </Screen>
  );
}
