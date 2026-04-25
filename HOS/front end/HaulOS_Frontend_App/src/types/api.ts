export type HealthResponse = { status: string };

export type RouteSummary = {
  route_id: string | null;
  label: string;
  route_status: string;
  route_class: string;
  legal_status: string;
  approval_status: string;
  eta_minutes: number;
  distance_km: number;
  hazard_count: number;
  restriction_count: number;
  managed_passage_required: boolean;
  managed_passage_reasons: string[];
};

export type RouteOptionsResponse = {
  recommended_route: RouteSummary;
  alternate_routes: RouteSummary[];
};

export type RouteStage = {
  stage_number: number;
  stage_type: string;
  start_location_name?: string | null;
  end_location_name?: string | null;
  start_combination_type?: string | null;
  start_trailer_count?: number | null;
  end_combination_type?: string | null;
  end_trailer_count?: number | null;
  action_required?: string | null;
  action_status?: string | null;
  notes?: string | null;
  payload?: Record<string, unknown>;
};

export type RouteSegment = {
  segment_id: string;
  sequence: number;
  stage_number?: number;
  road_name: string;
  direction_of_travel?: string;
  location_name: string;
  start_landmark?: string | null;
  end_landmark?: string | null;
  distance_km: number;
  estimated_travel_time_minutes: number;
  local_roads_in_scope?: string[];
  static_restrictions?: Array<Record<string, unknown>>;
  live_hazards?: Array<Record<string, unknown>>;
  managed_movement?: Record<string, unknown>;
  trigger_rules?: Record<string, unknown>;
  hazard_visibility?: Record<string, unknown>;
};

export type RouteDetail = {
  route_id: string;
  trip_id: string;
  label: string;
  route_status: string;
  route_class: string;
  legal_status: string;
  approval_status: string;
  managed_passage_required: boolean;
  managed_passage_reasons: string[];
  summary: {
    distance_km: number;
    eta_minutes: number;
    travel_time_minutes: number;
    hazard_count: number;
    restriction_count: number;
    managed_segment_count: number;
    fuel_confidence: string;
    rest_confidence: string;
    score: number;
    recommended_label: string;
  };
  stages?: RouteStage[];
  segments: RouteSegment[];
  pre_departure_briefing: BriefingItem[];
  upcoming_events: UpcomingEvent[];
  generated_at: string;
};

export type BriefingItem = {
  briefing_id: string;
  briefing_type: string;
  title: string;
  location_name?: string;
  severity: string;
  departure_allowed: boolean;
  driver_message: string;
  dispatcher_actions?: string[];
  reference_ids?: string[];
};

export type UpcomingEvent = {
  event_id: string;
  event_type: string;
  event_subtype?: string;
  title: string;
  location_name: string;
  distance_to_event_km: number;
  trigger_distances_km: number[];
  requires_acknowledgement: boolean;
  driver_message: string;
  dispatcher_message?: string | null;
  voice_message?: string | null;
  repeat?: boolean;
};

export type VehicleInput = {
  name?: string;
  registration?: string;
  configuration?: string;
  load_type?: string;
  combination_type: string;
  trailer_count: number;
  platform_type?: string;
  target_combination_type?: string;
  target_trailer_count?: number;
  route_direction?: string;
  requires_rtaa_reconfiguration: boolean;
  rtaa_name?: string;
  height_m: number;
  width_m: number;
  length_m: number;
  gross_mass_t: number;
  axle_group_masses_t?: number[];
  permit_ids?: string[];
  is_road_train: boolean;
  is_oversize: boolean;
  hazmat: boolean;
  permits_held: boolean;
  metadata_json?: Record<string, unknown>;
};

export type TripCreateRequest = {
  originLabel: string;
  destinationLabel: string;
  vehicle: VehicleInput;
};

export type ImportProfile = {
  profile_id: string;
  profile_type: string;
  name: string;
  description?: string | null;
  mapping_overrides: Record<string, string>;
  update_existing_default: boolean;
  source_vendor?: string | null;
  source_version?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type BridgeAsset = {
  bridge_id: string;
  asset_code?: string | null;
  name?: string | null;
  road_name?: string | null;
  locality?: string | null;
  clearance_height_m?: number | null;
  clearance_width_m?: number | null;
  max_mass_t?: number | null;
  geom_geojson?: string | null;
};
