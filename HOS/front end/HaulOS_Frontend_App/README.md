# HaulOS Frontend App Shell

This is a driver-first Expo + TypeScript front-end shell wired to the HaulOS backend pack.

## What it includes
- backend health check
- trip setup for heavy combinations, RTAA reconfiguration, and platform types
- route option selection
- route briefing
- live trip screen with managed-passage / contra flow awareness
- hazard / fuel / rest / comment report forms
- admin tools screen for bridge import profiles and bridge assets

## Backend base URL
Create a `.env` file from `.env.example` and set:

```bash
EXPO_PUBLIC_API_BASE_URL=http://YOUR_BACKEND_IP:8000
```

For Android emulator against a local machine, `10.0.2.2` is usually the right default.

## Install
```bash
npm install
npx expo install @react-navigation/native @react-navigation/native-stack react-native-safe-area-context react-native-screens
npx expo start
```

If Expo complains about dependency versions, run:

```bash
npx expo install --fix
```

## Backend endpoints used
- `GET /v1/system/health`
- `GET /v1/demo/locations`
- `POST /v1/trips`
- `POST /v1/routes/calculate`
- `GET /v1/routes/{route_id}`
- `GET /v1/routes/{route_id}/briefing`
- `GET /v1/trips/{trip_id}/events/upcoming`
- `POST /v1/hazards`
- `POST /v1/fuel-reports`
- `POST /v1/rest-reports`
- `POST /v1/comments`
- `GET /v1/import-profiles/bridges`
- `GET /v1/bridges`

## Product choices baked into the UI shell
- managed-passage routes are shown, not hidden
- Mount Magnet contra flow is treated as a first-class managed movement in the briefing and live trip views
- combination type and platform type are separate fields
- RTAA reconfiguration is planned in trip setup and displayed as route stages
- reports are fast and simple enough for use on-road
