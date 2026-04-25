import React, { useMemo, useState } from 'react';
import { Alert, Text, View } from 'react-native';

import { Card, Chip, Label, PrimaryButton, Screen, SectionTitle, TextField } from '../components/UI';
import { useHaulOS } from '../state/HaulOSContext';

const modes = ['hazard', 'fuel', 'rest', 'comment'] as const;

export function ReportsScreen() {
  const { tripId, selectedRouteSummary, submitComment, submitFuel, submitHazard, submitRest } = useHaulOS();
  const [mode, setMode] = useState<typeof modes[number]>('hazard');
  const [category, setCategory] = useState('debris');
  const [severity, setSeverity] = useState('medium');
  const [message, setMessage] = useState('');
  const [roadName, setRoadName] = useState('Great Northern Highway');
  const [locationName, setLocationName] = useState('');
  const [fuelStatus, setFuelStatus] = useState('low_supply');
  const [queueLevel, setQueueLevel] = useState('medium');
  const [restStatus, setRestStatus] = useState('nearly_full');
  const [spaceType, setSpaceType] = useState('road_train');
  const [entityType, setEntityType] = useState('route');
  const [entityId, setEntityId] = useState('');
  const inferredEntityId = useMemo(() => entityId || selectedRouteSummary?.route_id || tripId || 'manual_entity', [entityId, selectedRouteSummary?.route_id, tripId]);

  async function handleSubmit() {
    try {
      if (mode === 'hazard') {
        await submitHazard({
          trip_id: tripId,
          route_id: selectedRouteSummary?.route_id || undefined,
          category,
          severity,
          road_name: roadName,
          location_name: locationName,
          message,
          source: 'driver',
        });
      }

      if (mode === 'fuel') {
        await submitFuel({
          status: fuelStatus,
          queue_level: queueLevel,
          comment: message,
          source: 'driver',
        });
      }

      if (mode === 'rest') {
        await submitRest({
          status: restStatus,
          space_type: spaceType,
          comment: message,
          source: 'driver',
        });
      }

      if (mode === 'comment') {
        await submitComment({
          trip_id: tripId,
          entity_type: entityType,
          entity_id: inferredEntityId,
          comment: message,
          source: 'driver',
        });
      }

      Alert.alert('Report sent', 'The backend accepted the report.');
      setMessage('');
      setLocationName('');
    } catch (error) {
      Alert.alert('Report failed', error instanceof Error ? error.message : 'Unknown error');
    }
  }

  return (
    <Screen>
      <Card>
        <SectionTitle title="Report mode" subtitle="Fast enough for field use." />
        <View style={{ flexDirection: 'row', flexWrap: 'wrap' }}>
          {modes.map((item) => (
            <Chip key={item} title={item} selected={mode === item} onPress={() => setMode(item)} />
          ))}
        </View>
        <Text style={{ color: '#9DB0C4' }}>Trip: {tripId || 'none'} · Route: {selectedRouteSummary?.route_id || 'none'}</Text>
      </Card>

      {mode === 'hazard' ? (
        <Card>
          <SectionTitle title="Hazard report" subtitle="Debris, crash, water, powerline, roadworks and more." />
          <Label text="Category" />
          <TextField value={category} onChangeText={setCategory} placeholder="debris" />
          <Label text="Severity" />
          <TextField value={severity} onChangeText={setSeverity} placeholder="medium" />
          <Label text="Road name" />
          <TextField value={roadName} onChangeText={setRoadName} placeholder="Great Northern Highway" />
          <Label text="Location name" />
          <TextField value={locationName} onChangeText={setLocationName} placeholder="Near Wubin" />
          <Label text="Message" />
          <TextField value={message} onChangeText={setMessage} placeholder="Large tyre carcass left lane" multiline />
        </Card>
      ) : null}

      {mode === 'fuel' ? (
        <Card>
          <SectionTitle title="Fuel status" subtitle="Use this for available / low supply / no diesel reports." />
          <Label text="Fuel status" />
          <TextField value={fuelStatus} onChangeText={setFuelStatus} placeholder="low_supply" />
          <Label text="Queue level" />
          <TextField value={queueLevel} onChangeText={setQueueLevel} placeholder="medium" />
          <Label text="Comment" />
          <TextField value={message} onChangeText={setMessage} placeholder="Only one pump working." multiline />
        </Card>
      ) : null}

      {mode === 'rest' ? (
        <Card>
          <SectionTitle title="Rest area status" subtitle="Occupancy and suitability for the combination you are running." />
          <Label text="Status" />
          <TextField value={restStatus} onChangeText={setRestStatus} placeholder="nearly_full" />
          <Label text="Space type" />
          <TextField value={spaceType} onChangeText={setSpaceType} placeholder="road_train" />
          <Label text="Comment" />
          <TextField value={message} onChangeText={setMessage} placeholder="Triples bays full." multiline />
        </Card>
      ) : null}

      {mode === 'comment' ? (
        <Card>
          <SectionTitle title="Driver comment" subtitle="Global field intelligence layer." />
          <Label text="Entity type" />
          <TextField value={entityType} onChangeText={setEntityType} placeholder="route" />
          <Label text="Entity ID" />
          <TextField value={entityId} onChangeText={setEntityId} placeholder={selectedRouteSummary?.route_id || tripId || 'manual_entity'} />
          <Label text="Comment" />
          <TextField value={message} onChangeText={setMessage} placeholder="Contra flow crew already staged at Mount Magnet." multiline />
        </Card>
      ) : null}

      <PrimaryButton title="Submit report" onPress={() => void handleSubmit()} disabled={!message.trim() && mode !== 'rest'} />
    </Screen>
  );
}
