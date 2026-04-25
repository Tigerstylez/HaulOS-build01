import { apiGet, apiPost } from './client';
import {
  BridgeAsset,
  HealthResponse,
  ImportProfile,
  RouteDetail,
  RouteOptionsResponse,
  TripCreateRequest,
  UpcomingEvent,
} from '../types/api';

export function fetchHealth() {
  return apiGet<HealthResponse>('/v1/system/health');
}

export function fetchDemoLocations() {
  return apiGet<{ locations: string[] }>('/v1/demo/locations');
}

export function createTrip(payload: TripCreateRequest) {
  return apiPost<{ trip_id: string; status: string }>('/v1/trips', payload);
}

export function calculateRoutes(tripId: string, preference: 'balanced' | 'fastest' | 'lowest_hazard' = 'balanced') {
  return apiPost<RouteOptionsResponse>('/v1/routes/calculate', {
    trip_id: tripId,
    mode: 'managed_passage',
    preference,
  });
}

export function fetchRoute(routeId: string) {
  return apiGet<RouteDetail>(`/v1/routes/${routeId}`);
}

export function fetchRouteBriefing(routeId: string) {
  return apiGet<{ route_id: string; pre_departure_briefing: RouteDetail['pre_departure_briefing'] }>(`/v1/routes/${routeId}/briefing`);
}

export function fetchUpcomingEvents(tripId: string) {
  return apiGet<{ trip_id: string; upcoming_events: UpcomingEvent[] }>(`/v1/trips/${tripId}/events/upcoming`);
}

export function createHazardReport(payload: {
  trip_id?: string | null;
  route_id?: string | null;
  category: string;
  severity: string;
  road_name?: string;
  location_name?: string;
  lat?: number;
  lon?: number;
  message: string;
  source?: string;
  confidence_score?: number;
  delay_minutes?: number;
  extra_data?: Record<string, unknown>;
}) {
  return apiPost<{ hazard_id: string; status: string }>('/v1/hazards', payload);
}

export function createFuelReport(payload: {
  fuel_stop_id?: string | null;
  status: string;
  queue_level?: string;
  comment?: string;
  source?: string;
}) {
  return apiPost<{ fuel_report_id: string; status: string }>('/v1/fuel-reports', payload);
}

export function createRestReport(payload: {
  rest_area_id?: string | null;
  status: string;
  space_type?: string;
  comment?: string;
  source?: string;
}) {
  return apiPost<{ rest_report_id: string; status: string }>('/v1/rest-reports', payload);
}

export function createDriverComment(payload: {
  trip_id?: string | null;
  entity_type: string;
  entity_id: string;
  comment: string;
  confidence_score?: number;
  source?: string;
}) {
  return apiPost<{ comment_id: string; status: string }>('/v1/comments', payload);
}

export function fetchBridgeImportProfiles() {
  return apiGet<{ profiles: ImportProfile[] }>('/v1/import-profiles/bridges');
}

export function fetchBridges() {
  return apiGet<{ bridges: BridgeAsset[] }>('/v1/bridges');
}
