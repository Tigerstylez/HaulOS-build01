import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import {
  calculateRoutes,
  createDriverComment,
  createFuelReport,
  createHazardReport,
  createRestReport,
  createTrip,
  fetchBridgeImportProfiles,
  fetchBridges,
  fetchDemoLocations,
  fetchHealth,
  fetchRoute,
  fetchRouteBriefing,
  fetchUpcomingEvents,
} from '../api/haulos';
import {
  BridgeAsset,
  ImportProfile,
  RouteDetail,
  RouteOptionsResponse,
  RouteSummary,
  TripCreateRequest,
  UpcomingEvent,
} from '../types/api';

export type AppStatus = 'idle' | 'loading' | 'success' | 'error';

type HaulOSContextValue = {
  backendStatus: AppStatus;
  backendMessage: string;
  locations: string[];
  tripId: string | null;
  tripDraft: TripCreateRequest | null;
  routeOptions: RouteSummary[];
  selectedRouteSummary: RouteSummary | null;
  routeDetail: RouteDetail | null;
  upcomingEvents: UpcomingEvent[];
  profiles: ImportProfile[];
  bridges: BridgeAsset[];
  refreshSystem: () => Promise<void>;
  createTripAndCalculate: (draft: TripCreateRequest) => Promise<RouteOptionsResponse>;
  chooseRoute: (route: RouteSummary) => Promise<void>;
  refreshUpcomingEvents: () => Promise<void>;
  refreshAdminData: () => Promise<void>;
  submitHazard: (payload: Parameters<typeof createHazardReport>[0]) => Promise<void>;
  submitFuel: (payload: Parameters<typeof createFuelReport>[0]) => Promise<void>;
  submitRest: (payload: Parameters<typeof createRestReport>[0]) => Promise<void>;
  submitComment: (payload: Parameters<typeof createDriverComment>[0]) => Promise<void>;
};

const HaulOSContext = createContext<HaulOSContextValue | undefined>(undefined);

export function HaulOSProvider({ children }: { children: React.ReactNode }) {
  const [backendStatus, setBackendStatus] = useState<AppStatus>('idle');
  const [backendMessage, setBackendMessage] = useState('');
  const [locations, setLocations] = useState<string[]>([]);
  const [tripId, setTripId] = useState<string | null>(null);
  const [tripDraft, setTripDraft] = useState<TripCreateRequest | null>(null);
  const [routeOptions, setRouteOptions] = useState<RouteSummary[]>([]);
  const [selectedRouteSummary, setSelectedRouteSummary] = useState<RouteSummary | null>(null);
  const [routeDetail, setRouteDetail] = useState<RouteDetail | null>(null);
  const [upcomingEvents, setUpcomingEvents] = useState<UpcomingEvent[]>([]);
  const [profiles, setProfiles] = useState<ImportProfile[]>([]);
  const [bridges, setBridges] = useState<BridgeAsset[]>([]);

  const refreshSystem = useCallback(async () => {
    try {
      setBackendStatus('loading');
      const [health, demo] = await Promise.all([fetchHealth(), fetchDemoLocations()]);
      setLocations(demo.locations);
      setBackendStatus('success');
      setBackendMessage(`Backend ${health.status}. ${demo.locations.length} demo locations loaded.`);
    } catch (error) {
      setBackendStatus('error');
      setBackendMessage(error instanceof Error ? error.message : 'Backend unavailable');
    }
  }, []);

  const refreshAdminData = useCallback(async () => {
    try {
      const [profilesResponse, bridgesResponse] = await Promise.all([
        fetchBridgeImportProfiles(),
        fetchBridges(),
      ]);
      setProfiles(profilesResponse.profiles);
      setBridges(bridgesResponse.bridges);
    } catch (error) {
      setBackendMessage(error instanceof Error ? error.message : 'Admin data failed');
    }
  }, []);

  const createTripAndCalculate = useCallback(async (draft: TripCreateRequest) => {
    setTripDraft(draft);
    const trip = await createTrip(draft);
    setTripId(trip.trip_id);
    const routeOptionsResponse = await calculateRoutes(trip.trip_id, 'balanced');
    const combined = [routeOptionsResponse.recommended_route, ...routeOptionsResponse.alternate_routes]
      .filter((item) => item.route_id);
    setRouteOptions(combined as RouteSummary[]);
    setSelectedRouteSummary(null);
    setRouteDetail(null);
    setUpcomingEvents([]);
    return routeOptionsResponse;
  }, []);

  const chooseRoute = useCallback(async (route: RouteSummary) => {
    if (!route.route_id) return;
    setSelectedRouteSummary(route);
    const [detail, upcoming] = await Promise.all([
      fetchRoute(route.route_id),
      tripId ? fetchUpcomingEvents(tripId) : Promise.resolve({ trip_id: '', upcoming_events: [] }),
    ]);
    setRouteDetail(detail);
    setUpcomingEvents(upcoming.upcoming_events);
    await fetchRouteBriefing(route.route_id);
  }, [tripId]);

  const refreshUpcomingEvents = useCallback(async () => {
    if (!tripId) return;
    const response = await fetchUpcomingEvents(tripId);
    setUpcomingEvents(response.upcoming_events);
  }, [tripId]);

  const submitHazard = useCallback(async (payload: Parameters<typeof createHazardReport>[0]) => {
    await createHazardReport(payload);
    if (tripId) {
      await refreshUpcomingEvents();
    }
  }, [refreshUpcomingEvents, tripId]);

  const submitFuel = useCallback(async (payload: Parameters<typeof createFuelReport>[0]) => {
    await createFuelReport(payload);
  }, []);

  const submitRest = useCallback(async (payload: Parameters<typeof createRestReport>[0]) => {
    await createRestReport(payload);
  }, []);

  const submitComment = useCallback(async (payload: Parameters<typeof createDriverComment>[0]) => {
    await createDriverComment(payload);
  }, []);

  useEffect(() => {
    refreshSystem().catch(() => null);
    refreshAdminData().catch(() => null);
  }, [refreshAdminData, refreshSystem]);

  const value = useMemo<HaulOSContextValue>(
    () => ({
      backendStatus,
      backendMessage,
      locations,
      tripId,
      tripDraft,
      routeOptions,
      selectedRouteSummary,
      routeDetail,
      upcomingEvents,
      profiles,
      bridges,
      refreshSystem,
      createTripAndCalculate,
      chooseRoute,
      refreshUpcomingEvents,
      refreshAdminData,
      submitHazard,
      submitFuel,
      submitRest,
      submitComment,
    }),
    [
      backendStatus,
      backendMessage,
      locations,
      tripId,
      tripDraft,
      routeOptions,
      selectedRouteSummary,
      routeDetail,
      upcomingEvents,
      profiles,
      bridges,
      refreshSystem,
      createTripAndCalculate,
      chooseRoute,
      refreshUpcomingEvents,
      refreshAdminData,
      submitHazard,
      submitFuel,
      submitRest,
      submitComment,
    ]
  );

  return <HaulOSContext.Provider value={value}>{children}</HaulOSContext.Provider>;
}

export function useHaulOS() {
  const context = useContext(HaulOSContext);
  if (!context) {
    throw new Error('useHaulOS must be used inside HaulOSProvider');
  }
  return context;
}
