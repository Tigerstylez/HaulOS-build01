from __future__ import annotations

import json
import uuid
from typing import Any

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from geoalchemy2.functions import ST_AsGeoJSON
from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from .db import Base, engine, get_db
from .import_utils import (
    bridge_from_csv_row,
    bridge_from_geojson_feature,
    build_csv_header_map_with_overrides,
    build_header_diagnostics,
    csv_reader_from_text,
    decode_upload_bytes,
    parse_bridge_mapping_overrides,
    preview_bridge_action,
)
from .models import (
    BridgeAsset,
    DriverComment,
    FuelReport,
    HazardReport,
    ImportJob,
    ImportProfile,
    PowerlineAsset,
    RestReport,
    Route,
    RouteSegment,
    RouteStage,
    Trip,
    VehicleProfile,
)
from .routing_engine import calculate_route_plan, demo_locations, edge_linestring_wkt
from .schemas import (
    BridgeAssetCreateRequest,
    BridgeColumnOverrideRequest,
    CalculateRouteRequest,
    CommentCreateRequest,
    FuelReportCreateRequest,
    HazardCreateRequest,
    ImportProfileCreateRequest,
    ImportProfileUpdateRequest,
    PowerlineAssetCreateRequest,
    RestReportCreateRequest,
    TripCreateRequest,
)

app = FastAPI(title="HaulOS Backend", version="1.0.0")


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


def parse_uuid(value: str, field: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid {field}") from exc


def route_summary(route: Route) -> dict:
    return {
        "route_id": str(route.id),
        "label": route.label,
        "route_status": route.route_status,
        "route_class": route.route_class,
        "legal_status": route.legal_status,
        "approval_status": route.approval_status,
        "eta_minutes": route.eta_minutes,
        "distance_km": route.distance_km,
        "hazard_count": route.hazard_count,
        "restriction_count": route.restriction_count,
        "managed_passage_required": route.managed_passage_required,
        "managed_passage_reasons": route.managed_passage_reasons,
    }


def profile_to_dict(profile: ImportProfile) -> dict:
    return {
        "profile_id": str(profile.id),
        "profile_type": profile.profile_type,
        "name": profile.name,
        "description": profile.description,
        "mapping_overrides": profile.mapping_overrides or {},
        "update_existing_default": profile.update_existing_default,
        "source_vendor": profile.source_vendor,
        "source_version": profile.source_version,
        "created_at": profile.created_at.isoformat() if profile.created_at else None,
        "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
    }


def get_import_profile_or_404(db: Session, profile_id: str, expected_type: str | None = None) -> ImportProfile:
    profile_uuid = parse_uuid(profile_id, "profile_id")
    profile = db.get(ImportProfile, profile_uuid)
    if profile is None:
        raise HTTPException(status_code=404, detail="Import profile not found")
    if expected_type and profile.profile_type != expected_type:
        raise HTTPException(
            status_code=400,
            detail=f"Import profile type mismatch. Expected {expected_type}, got {profile.profile_type}",
        )
    return profile


def bridge_override_model_from_dict(data: dict | None) -> BridgeColumnOverrideRequest | None:
    if not data:
        return None
    return BridgeColumnOverrideRequest(**data)


def resolve_bridge_import_config(
    *,
    db: Session,
    profile_id: str | None,
    mapping_overrides_json: str | None,
    update_existing: bool | None,
) -> tuple[BridgeColumnOverrideRequest | None, bool, dict]:
    profile_dict: dict[str, Any] = {}
    profile_mapping_model: BridgeColumnOverrideRequest | None = None
    resolved_update_existing = True

    if profile_id:
        profile = get_import_profile_or_404(db, profile_id, expected_type="bridge_csv")
        profile_dict = profile_to_dict(profile)
        profile_mapping_model = bridge_override_model_from_dict(profile.mapping_overrides)
        resolved_update_existing = profile.update_existing_default

    request_mapping_model = parse_bridge_mapping_overrides(mapping_overrides_json)

    if request_mapping_model and profile_mapping_model:
        merged = {
            **profile_mapping_model.model_dump(exclude_none=True),
            **request_mapping_model.model_dump(exclude_none=True),
        }
        resolved_mapping_model = BridgeColumnOverrideRequest(**merged)
    elif request_mapping_model:
        resolved_mapping_model = request_mapping_model
    else:
        resolved_mapping_model = profile_mapping_model

    if update_existing is not None:
        resolved_update_existing = update_existing

    return resolved_mapping_model, resolved_update_existing, profile_dict


def record_import_job(
    db: Session,
    *,
    profile_id: str | None,
    profile_type: str,
    file_name: str | None,
    inserted_count: int,
    updated_count: int,
    skipped_count: int,
    error_count: int,
    result_payload: dict,
) -> None:
    profile_uuid = parse_uuid(profile_id, "profile_id") if profile_id else None
    job = ImportJob(
        profile_id=profile_uuid,
        profile_type=profile_type,
        file_name=file_name,
        status="completed",
        inserted_count=inserted_count,
        updated_count=updated_count,
        skipped_count=skipped_count,
        error_count=error_count,
        result_payload=result_payload,
    )
    db.add(job)


@app.get("/v1/system/health")
def system_health() -> dict:
    return {"status": "ok"}


@app.get("/v1/demo/locations")
def get_demo_locations() -> dict:
    return {"locations": demo_locations()}


@app.post("/v1/trips")
def create_trip(payload: TripCreateRequest, db: Session = Depends(get_db)) -> dict:
    vehicle = VehicleProfile(**payload.vehicle.model_dump())
    db.add(vehicle)
    db.flush()

    trip = Trip(
        origin_label=payload.originLabel,
        destination_label=payload.destinationLabel,
        vehicle_profile_id=vehicle.id,
        status="draft",
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return {"trip_id": str(trip.id), "status": trip.status}


@app.post("/v1/routes/calculate")
def calculate_routes(payload: CalculateRouteRequest, db: Session = Depends(get_db)) -> dict:
    trip_uuid = parse_uuid(payload.trip_id, "trip_id")
    trip = db.get(Trip, trip_uuid)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")

    vehicle = trip.vehicle_profile
    if vehicle is None:
        raise HTTPException(status_code=500, detail="Trip vehicle profile missing")

    vehicle_dict = {
        "combination_type": vehicle.combination_type,
        "trailer_count": vehicle.trailer_count,
        "platform_type": vehicle.platform_type,
        "target_combination_type": vehicle.target_combination_type,
        "target_trailer_count": vehicle.target_trailer_count,
        "route_direction": vehicle.route_direction,
        "requires_rtaa_reconfiguration": vehicle.requires_rtaa_reconfiguration,
        "rtaa_name": vehicle.rtaa_name,
        "height_m": vehicle.height_m,
        "width_m": vehicle.width_m,
        "length_m": vehicle.length_m,
        "gross_mass_t": vehicle.gross_mass_t,
        "is_road_train": vehicle.is_road_train,
        "is_oversize": vehicle.is_oversize,
        "hazmat": vehicle.hazmat,
        "permits_held": vehicle.permits_held,
    }

    options: list[Route] = []
    signatures: set[tuple[str, ...]] = set()

    for pref in ["balanced", "fastest", "lowest_hazard"]:
        route_payload = calculate_route_plan(
            origin_label=trip.origin_label,
            destination_label=trip.destination_label,
            vehicle_dict=vehicle_dict,
            preference=pref,
        )
        if route_payload is None:
            continue

        signature = tuple(seg.get("segment_id", "") for seg in route_payload.get("segments", []))
        if signature in signatures:
            continue
        signatures.add(signature)

        route_uuid = uuid.uuid4()
        route_payload["route_id"] = str(route_uuid)
        route_payload["trip_id"] = str(trip.id)
        summary = route_payload["summary"]

        route = Route(
            id=route_uuid,
            trip_id=trip.id,
            label=route_payload["label"],
            route_status=route_payload["route_status"],
            route_class=route_payload["route_class"],
            legal_status=route_payload["legal_status"],
            approval_status=route_payload["approval_status"],
            managed_passage_required=route_payload["managed_passage_required"],
            managed_passage_reasons=route_payload.get("managed_passage_reasons", []),
            distance_km=summary["distance_km"],
            eta_minutes=summary["eta_minutes"],
            travel_time_minutes=summary["travel_time_minutes"],
            hazard_count=summary["hazard_count"],
            restriction_count=summary["restriction_count"],
            managed_segment_count=summary["managed_segment_count"],
            fuel_confidence=summary["fuel_confidence"],
            rest_confidence=summary["rest_confidence"],
            score=summary["score"],
            payload=route_payload,
            pre_departure_briefing=route_payload.get("pre_departure_briefing", []),
            upcoming_events=route_payload.get("upcoming_events", []),
        )
        db.add(route)
        db.flush()

        for stage in route_payload.get("stages", []):
            db.add(RouteStage(
                route_id=route.id,
                stage_number=stage["stage_number"],
                stage_type=stage["stage_type"],
                start_location_name=stage.get("start_location_name"),
                end_location_name=stage.get("end_location_name"),
                start_combination_type=stage.get("start_combination_type"),
                start_trailer_count=stage.get("start_trailer_count"),
                end_combination_type=stage.get("end_combination_type"),
                end_trailer_count=stage.get("end_trailer_count"),
                action_required=stage.get("action_required"),
                action_status=stage.get("action_status", "pending"),
                notes=stage.get("notes"),
                payload=stage.get("payload", {}),
            ))

        for seg in route_payload.get("segments", []):
            segment = RouteSegment(
                route_id=route.id,
                sequence=seg["sequence"],
                edge_id=seg.get("segment_id"),
                stage_number=seg.get("stage_number"),
                road_name=seg["road_name"],
                direction_of_travel=seg.get("direction_of_travel"),
                location_name=seg["location_name"],
                start_landmark=seg.get("start_landmark"),
                end_landmark=seg.get("end_landmark"),
                distance_km=seg["distance_km"],
                estimated_travel_time_minutes=seg["estimated_travel_time_minutes"],
                local_roads_in_scope=seg.get("local_roads_in_scope", []),
                static_restrictions=seg.get("static_restrictions", []),
                live_hazards=seg.get("live_hazards", []),
                managed_movement=seg.get("managed_movement", {}),
                trigger_rules=seg.get("trigger_rules", {}),
                hazard_visibility=seg.get("hazard_visibility", {}),
            )
            wkt = edge_linestring_wkt(seg.get("segment_id"))
            if wkt:
                segment.geom = func.ST_GeomFromText(wkt, 4326)
            db.add(segment)

        db.flush()
        route.geom = db.scalar(
            select(func.ST_Multi(func.ST_Collect(RouteSegment.geom))).where(RouteSegment.route_id == route.id)
        )
        options.append(route)

    if not options:
        return {
            "recommended_route": {
                "route_id": None,
                "label": "No workable route",
                "route_status": "no_workable_route",
                "route_class": "managed_passage",
                "legal_status": "not_legal_for_departure",
                "approval_status": "rejected",
                "eta_minutes": 0,
                "distance_km": 0,
                "hazard_count": 0,
                "restriction_count": 0,
                "managed_passage_required": False,
                "managed_passage_reasons": [],
            },
            "alternate_routes": [],
        }

    trip.route_mode = payload.mode
    trip.route_preference = payload.preference
    db.commit()

    options.sort(key=lambda r: (1 if r.managed_passage_required else 0, r.score))
    return {
        "recommended_route": route_summary(options[0]),
        "alternate_routes": [route_summary(r) for r in options[1:]],
    }


@app.get("/v1/routes/{route_id}")
def get_route(route_id: str, db: Session = Depends(get_db)) -> dict:
    route = db.get(Route, parse_uuid(route_id, "route_id"))
    if route is None:
        raise HTTPException(status_code=404, detail="Route not found")
    return route.payload


@app.get("/v1/routes/{route_id}/briefing")
def get_route_briefing(route_id: str, db: Session = Depends(get_db)) -> dict:
    route = db.get(Route, parse_uuid(route_id, "route_id"))
    if route is None:
        raise HTTPException(status_code=404, detail="Route not found")
    return {"route_id": str(route.id), "pre_departure_briefing": route.pre_departure_briefing}


@app.get("/v1/trips/{trip_id}/events/upcoming")
def get_trip_events(trip_id: str, db: Session = Depends(get_db)) -> dict:
    trip = db.get(Trip, parse_uuid(trip_id, "trip_id"))
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    routes = list(trip.routes)
    if not routes:
        raise HTTPException(status_code=404, detail="No routes for this trip")
    routes.sort(key=lambda r: (1 if r.managed_passage_required else 0, r.score))
    best = routes[0]
    return {"trip_id": str(trip.id), "upcoming_events": best.upcoming_events}


@app.post("/v1/hazards")
def create_hazard(payload: HazardCreateRequest, db: Session = Depends(get_db)) -> dict:
    trip_uuid = parse_uuid(payload.trip_id, "trip_id") if payload.trip_id else None
    route_uuid = parse_uuid(payload.route_id, "route_id") if payload.route_id else None
    hazard = HazardReport(
        trip_id=trip_uuid,
        route_id=route_uuid,
        category=payload.category,
        severity=payload.severity,
        road_name=payload.road_name,
        location_name=payload.location_name,
        lat=payload.lat,
        lon=payload.lon,
        message=payload.message,
        source=payload.source,
        confidence_score=payload.confidence_score,
        delay_minutes=payload.delay_minutes,
        extra_data=payload.extra_data,
    )
    if payload.lat is not None and payload.lon is not None:
        hazard.geom = func.ST_SetSRID(func.ST_MakePoint(payload.lon, payload.lat), 4326)
    db.add(hazard)
    db.commit()
    db.refresh(hazard)
    return {"hazard_id": str(hazard.id), "status": hazard.status}


@app.post("/v1/comments")
def create_comment(payload: CommentCreateRequest, db: Session = Depends(get_db)) -> dict:
    trip_uuid = parse_uuid(payload.trip_id, "trip_id") if payload.trip_id else None
    comment = DriverComment(
        trip_id=trip_uuid,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        comment=payload.comment,
        confidence_score=payload.confidence_score,
        source=payload.source,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return {"comment_id": str(comment.id), "status": "created"}


@app.post("/v1/fuel-reports")
def create_fuel_report(payload: FuelReportCreateRequest, db: Session = Depends(get_db)) -> dict:
    fuel_uuid = parse_uuid(payload.fuel_stop_id, "fuel_stop_id") if payload.fuel_stop_id else None
    report = FuelReport(
        fuel_stop_id=fuel_uuid,
        status=payload.status,
        queue_level=payload.queue_level,
        comment=payload.comment,
        source=payload.source,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return {"fuel_report_id": str(report.id), "status": "created"}


@app.post("/v1/rest-reports")
def create_rest_report(payload: RestReportCreateRequest, db: Session = Depends(get_db)) -> dict:
    rest_uuid = parse_uuid(payload.rest_area_id, "rest_area_id") if payload.rest_area_id else None
    report = RestReport(
        rest_area_id=rest_uuid,
        status=payload.status,
        space_type=payload.space_type,
        comment=payload.comment,
        source=payload.source,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return {"rest_report_id": str(report.id), "status": "created"}


@app.post("/v1/bridges")
def create_bridge(payload: BridgeAssetCreateRequest, db: Session = Depends(get_db)) -> dict:
    fingerprint = (
        f"asset_code:{payload.asset_code.strip().lower()}" if payload.asset_code
        else f"bridge|{(payload.road_name or '').lower()}|{(payload.locality or '').lower()}|{payload.clearance_height_m or ''}|{payload.clearance_width_m or ''}|{payload.max_mass_t or ''}|{payload.lat:.6f}|{payload.lon:.6f}"
    )
    bridge = BridgeAsset(
        asset_code=payload.asset_code.strip().lower() if payload.asset_code else None,
        asset_fingerprint=fingerprint,
        name=payload.name,
        road_name=payload.road_name,
        locality=payload.locality,
        clearance_height_m=payload.clearance_height_m,
        clearance_width_m=payload.clearance_width_m,
        max_mass_t=payload.max_mass_t,
        notes=payload.notes,
        source=payload.source,
    )
    bridge.geom = func.ST_SetSRID(func.ST_MakePoint(payload.lon, payload.lat), 4326)
    db.add(bridge)
    db.commit()
    db.refresh(bridge)
    return {"bridge_id": str(bridge.id), "status": "created"}


@app.post("/v1/powerlines")
def create_powerline(payload: PowerlineAssetCreateRequest, db: Session = Depends(get_db)) -> dict:
    powerline = PowerlineAsset(
        asset_code=payload.asset_code,
        owner_name=payload.owner_name,
        line_name=payload.line_name,
        road_name=payload.road_name,
        locality=payload.locality,
        clearance_height_m=payload.clearance_height_m,
        managed_action_default=payload.managed_action_default,
        notes=payload.notes,
        source=payload.source,
    )
    powerline.geom = func.ST_GeomFromText(payload.wkt_linestring, 4326)
    db.add(powerline)
    db.commit()
    db.refresh(powerline)
    return {"powerline_id": str(powerline.id), "status": "created"}


@app.get("/v1/bridges")
def list_bridges(limit: int = 100, db: Session = Depends(get_db)) -> dict:
    rows = db.execute(select(BridgeAsset.id, BridgeAsset.asset_code, BridgeAsset.name, BridgeAsset.road_name, BridgeAsset.locality, BridgeAsset.clearance_height_m, BridgeAsset.clearance_width_m, BridgeAsset.max_mass_t, ST_AsGeoJSON(BridgeAsset.geom).label("geom_geojson")).limit(limit)).all()
    return {"bridges": [{"bridge_id": str(row.id), "asset_code": row.asset_code, "name": row.name, "road_name": row.road_name, "locality": row.locality, "clearance_height_m": row.clearance_height_m, "clearance_width_m": row.clearance_width_m, "max_mass_t": row.max_mass_t, "geom_geojson": row.geom_geojson} for row in rows]}


@app.get("/v1/routes/{route_id}/hazards/nearby")
def get_hazards_near_route(route_id: str, meters: float = 5000, db: Session = Depends(get_db)) -> dict:
    route = db.get(Route, parse_uuid(route_id, "route_id"))
    if route is None:
        raise HTTPException(status_code=404, detail="Route not found")
    if route.geom is None:
        raise HTTPException(status_code=400, detail="Route geometry missing")
    stmt = (select(HazardReport.id, HazardReport.category, HazardReport.severity, HazardReport.message, HazardReport.road_name, HazardReport.location_name, func.ST_Distance(func.Geography(HazardReport.geom), func.Geography(route.geom)).label("distance_m"), ST_AsGeoJSON(HazardReport.geom).label("geom_geojson")).where(HazardReport.geom.is_not(None)).where(func.ST_DWithin(func.Geography(HazardReport.geom), func.Geography(route.geom), meters)).order_by("distance_m"))
    rows = db.execute(stmt).all()
    return {"route_id": route_id, "meters": meters, "hazards": [{"hazard_id": str(row.id), "category": row.category, "severity": row.severity, "message": row.message, "road_name": row.road_name, "location_name": row.location_name, "distance_m": round(float(row.distance_m), 1) if row.distance_m is not None else None, "geom_geojson": row.geom_geojson} for row in rows]}


@app.get("/v1/routes/{route_id}/bridges/conflicts")
def get_bridge_conflicts(route_id: str, vehicle_height_m: float, vehicle_width_m: float, gross_mass_t: float, approach_buffer_m: float = 50, db: Session = Depends(get_db)) -> dict:
    route = db.get(Route, parse_uuid(route_id, "route_id"))
    if route is None:
        raise HTTPException(status_code=404, detail="Route not found")
    if route.geom is None:
        raise HTTPException(status_code=400, detail="Route geometry missing")
    stmt = (select(BridgeAsset.id, BridgeAsset.asset_code, BridgeAsset.name, BridgeAsset.road_name, BridgeAsset.locality, BridgeAsset.clearance_height_m, BridgeAsset.clearance_width_m, BridgeAsset.max_mass_t, func.ST_Distance(func.Geography(BridgeAsset.geom), func.Geography(route.geom)).label("distance_m"), ST_AsGeoJSON(BridgeAsset.geom).label("geom_geojson")).where(func.ST_DWithin(func.Geography(BridgeAsset.geom), func.Geography(route.geom), approach_buffer_m)).where(or_(BridgeAsset.clearance_height_m < vehicle_height_m, BridgeAsset.clearance_width_m < vehicle_width_m, BridgeAsset.max_mass_t < gross_mass_t)).order_by("distance_m"))
    rows = db.execute(stmt).all()

    def conflict_flags(row: Any) -> list[str]:
        flags = []
        if row.clearance_height_m is not None and row.clearance_height_m < vehicle_height_m:
            flags.append("bridge_height_limit")
        if row.clearance_width_m is not None and row.clearance_width_m < vehicle_width_m:
            flags.append("bridge_width_limit")
        if row.max_mass_t is not None and row.max_mass_t < gross_mass_t:
            flags.append("bridge_mass_limit")
        return flags

    return {"route_id": route_id, "bridge_conflicts": [{"bridge_id": str(row.id), "asset_code": row.asset_code, "name": row.name, "road_name": row.road_name, "locality": row.locality, "distance_m": round(float(row.distance_m), 1) if row.distance_m is not None else None, "clearance_height_m": row.clearance_height_m, "clearance_width_m": row.clearance_width_m, "max_mass_t": row.max_mass_t, "conflict_flags": conflict_flags(row), "geom_geojson": row.geom_geojson} for row in rows]}


@app.get("/v1/routes/{route_id}/powerlines/conflicts")
def get_powerline_conflicts(route_id: str, vehicle_height_m: float, crossing_buffer_m: float = 25, db: Session = Depends(get_db)) -> dict:
    route = db.get(Route, parse_uuid(route_id, "route_id"))
    if route is None:
        raise HTTPException(status_code=404, detail="Route not found")
    if route.geom is None:
        raise HTTPException(status_code=400, detail="Route geometry missing")
    stmt = (select(PowerlineAsset.id, PowerlineAsset.asset_code, PowerlineAsset.owner_name, PowerlineAsset.line_name, PowerlineAsset.road_name, PowerlineAsset.locality, PowerlineAsset.clearance_height_m, PowerlineAsset.managed_action_default, ST_AsGeoJSON(PowerlineAsset.geom).label("geom_geojson")).where(PowerlineAsset.geom.is_not(None)).where(or_(func.ST_Intersects(PowerlineAsset.geom, route.geom), func.ST_DWithin(func.Geography(PowerlineAsset.geom), func.Geography(route.geom), crossing_buffer_m))).where(or_(PowerlineAsset.clearance_height_m.is_(None), PowerlineAsset.clearance_height_m < vehicle_height_m)))
    rows = db.execute(stmt).all()
    return {"route_id": route_id, "powerline_conflicts": [{"powerline_id": str(row.id), "asset_code": row.asset_code, "owner_name": row.owner_name, "line_name": row.line_name, "road_name": row.road_name, "locality": row.locality, "clearance_height_m": row.clearance_height_m, "required_action": row.managed_action_default or "utility_line_lift", "conflict_flags": ["powerline_height_limit"], "geom_geojson": row.geom_geojson} for row in rows]}


@app.get("/v1/routes/{route_id}/constraints/check")
def get_route_constraint_summary(route_id: str, vehicle_height_m: float, vehicle_width_m: float, gross_mass_t: float, db: Session = Depends(get_db)) -> dict:
    bridges = get_bridge_conflicts(route_id, vehicle_height_m, vehicle_width_m, gross_mass_t, db=db)
    powerlines = get_powerline_conflicts(route_id, vehicle_height_m, db=db)
    hazards = get_hazards_near_route(route_id, meters=5000, db=db)
    reasons = []
    if bridges["bridge_conflicts"]:
        reasons.append("bridge_constraint_detected")
    if powerlines["powerline_conflicts"]:
        reasons.append("powerline_lift_required")
    if hazards["hazards"]:
        reasons.append("live_hazards_present")
    return {"route_id": route_id, "managed_passage_required": bool(bridges["bridge_conflicts"] or powerlines["powerline_conflicts"]), "managed_passage_reasons": reasons, "bridge_conflicts": bridges["bridge_conflicts"], "powerline_conflicts": powerlines["powerline_conflicts"], "nearby_hazards": hazards["hazards"]}


@app.post("/v1/import-profiles/bridges")
def create_bridge_import_profile(payload: ImportProfileCreateRequest, db: Session = Depends(get_db)) -> dict:
    profile = ImportProfile(profile_type=payload.profile_type, name=payload.name, description=payload.description, mapping_overrides=payload.mapping_overrides.model_dump(exclude_none=True), update_existing_default=payload.update_existing_default, source_vendor=payload.source_vendor, source_version=payload.source_version)
    db.add(profile)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Import profile with this type and name already exists") from exc
    db.refresh(profile)
    return profile_to_dict(profile)


@app.get("/v1/import-profiles/bridges")
def list_bridge_import_profiles(db: Session = Depends(get_db)) -> dict:
    rows = db.execute(select(ImportProfile).where(ImportProfile.profile_type == "bridge_csv").order_by(ImportProfile.name.asc())).scalars().all()
    return {"profiles": [profile_to_dict(row) for row in rows]}


@app.get("/v1/import-profiles/bridges/{profile_id}")
def get_bridge_import_profile(profile_id: str, db: Session = Depends(get_db)) -> dict:
    return profile_to_dict(get_import_profile_or_404(db, profile_id, expected_type="bridge_csv"))


@app.put("/v1/import-profiles/bridges/{profile_id}")
def update_bridge_import_profile(profile_id: str, payload: ImportProfileUpdateRequest, db: Session = Depends(get_db)) -> dict:
    profile = get_import_profile_or_404(db, profile_id, expected_type="bridge_csv")
    if payload.name is not None:
        profile.name = payload.name
    if payload.description is not None:
        profile.description = payload.description
    if payload.mapping_overrides is not None:
        profile.mapping_overrides = payload.mapping_overrides.model_dump(exclude_none=True)
    if payload.update_existing_default is not None:
        profile.update_existing_default = payload.update_existing_default
    if payload.source_vendor is not None:
        profile.source_vendor = payload.source_vendor
    if payload.source_version is not None:
        profile.source_version = payload.source_version
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Another import profile with this type and name already exists") from exc
    db.refresh(profile)
    return profile_to_dict(profile)


@app.delete("/v1/import-profiles/bridges/{profile_id}")
def delete_bridge_import_profile(profile_id: str, db: Session = Depends(get_db)) -> dict:
    profile = get_import_profile_or_404(db, profile_id, expected_type="bridge_csv")
    db.delete(profile)
    db.commit()
    return {"status": "deleted", "profile_id": profile_id}


@app.post("/v1/bridges/import/preview/csv")
async def preview_bridges_csv(file: UploadFile = File(...), max_preview_rows: int = Form(20), profile_id: str | None = Form(None), update_existing: bool | None = Form(None), mapping_overrides_json: str | None = Form(None), db: Session = Depends(get_db)) -> dict:
    filename = (file.filename or "").lower()
    if not filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Upload a .csv file")
    if max_preview_rows < 1:
        raise HTTPException(status_code=400, detail="max_preview_rows must be at least 1")

    text = decode_upload_bytes(await file.read())
    reader = csv_reader_from_text(text)
    resolved_mapping_model, resolved_update_existing, profile_dict = resolve_bridge_import_config(db=db, profile_id=profile_id, mapping_overrides_json=mapping_overrides_json, update_existing=update_existing)
    header_map = build_csv_header_map_with_overrides(reader.fieldnames, resolved_mapping_model)
    diagnostics = build_header_diagnostics(reader.fieldnames, header_map)

    required = ["lat", "lon"]
    missing_required = [field for field in required if field not in header_map]
    if missing_required:
        return {"status": "invalid_mapping", "file_name": file.filename, "profile": profile_dict, "resolved_update_existing": resolved_update_existing, "resolved_mapping_overrides": resolved_mapping_model.model_dump(exclude_none=True) if resolved_mapping_model else {}, "missing_required_mapped_columns": missing_required, **diagnostics, "summary": {"total_rows_seen": 0, "would_insert": 0, "would_update": 0, "would_skip_duplicate": 0, "errors": 0}, "preview_rows": []}

    total_rows_seen = 0
    would_insert = 0
    would_update = 0
    would_skip_duplicate = 0
    error_count = 0
    preview_rows: list[dict] = []
    errors: list[dict] = []

    for row_number, row in enumerate(reader, start=2):
        total_rows_seen += 1
        try:
            data = bridge_from_csv_row(row, header_map)
            existing = db.execute(select(BridgeAsset.id, BridgeAsset.asset_code, BridgeAsset.name, BridgeAsset.road_name, BridgeAsset.locality).where(BridgeAsset.asset_fingerprint == data["asset_fingerprint"])).first()
            action = preview_bridge_action(existing is not None, resolved_update_existing)
            if action == "would_insert":
                would_insert += 1
            elif action == "would_update":
                would_update += 1
            else:
                would_skip_duplicate += 1
            if len(preview_rows) < max_preview_rows:
                preview_rows.append({"row": row_number, "action": action, "parsed": data, "existing_match": ({"bridge_id": str(existing.id), "asset_code": existing.asset_code, "name": existing.name, "road_name": existing.road_name, "locality": existing.locality} if existing else None)})
        except Exception as exc:
            error_count += 1
            errors.append({"row": row_number, "error": str(exc), "row_data": row})
            if len(preview_rows) < max_preview_rows:
                preview_rows.append({"row": row_number, "action": "error", "error": str(exc), "row_data": row})

    return {"status": "preview_completed", "file_name": file.filename, "profile": profile_dict, "resolved_update_existing": resolved_update_existing, "resolved_mapping_overrides": resolved_mapping_model.model_dump(exclude_none=True) if resolved_mapping_model else {}, **diagnostics, "missing_required_mapped_columns": [], "summary": {"total_rows_seen": total_rows_seen, "would_insert": would_insert, "would_update": would_update, "would_skip_duplicate": would_skip_duplicate, "errors": error_count}, "preview_rows": preview_rows, "errors": errors[:100]}


@app.post("/v1/bridges/import/csv")
async def import_bridges_csv(file: UploadFile = File(...), profile_id: str | None = Form(None), update_existing: bool | None = Form(None), mapping_overrides_json: str | None = Form(None), db: Session = Depends(get_db)) -> dict:
    filename = (file.filename or "").lower()
    if not filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Upload a .csv file")

    text = decode_upload_bytes(await file.read())
    reader = csv_reader_from_text(text)
    resolved_mapping_model, resolved_update_existing, profile_dict = resolve_bridge_import_config(db=db, profile_id=profile_id, mapping_overrides_json=mapping_overrides_json, update_existing=update_existing)
    header_map = build_csv_header_map_with_overrides(reader.fieldnames, resolved_mapping_model)
    required = ["lat", "lon"]
    missing_required = [field for field in required if field not in header_map]
    if missing_required:
        raise HTTPException(status_code=400, detail=f"Missing required mapped columns: {missing_required}")

    inserted_count = 0
    updated_count = 0
    skipped_count = 0
    errors: list[dict] = []

    try:
        for row_number, row in enumerate(reader, start=2):
            try:
                data = bridge_from_csv_row(row, header_map)
                existing = db.execute(select(BridgeAsset.id).where(BridgeAsset.asset_fingerprint == data["asset_fingerprint"])).scalar_one_or_none()
                values = {
                    "asset_code": data["asset_code"],
                    "asset_fingerprint": data["asset_fingerprint"],
                    "name": data["name"],
                    "road_name": data["road_name"],
                    "locality": data["locality"],
                    "clearance_height_m": data["clearance_height_m"],
                    "clearance_width_m": data["clearance_width_m"],
                    "max_mass_t": data["max_mass_t"],
                    "notes": data["notes"],
                    "source": data["source"],
                    "geom": func.ST_SetSRID(func.ST_MakePoint(data["lon"], data["lat"]), 4326),
                }
                base_stmt = pg_insert(BridgeAsset).values(**values)
                if resolved_update_existing:
                    stmt = base_stmt.on_conflict_do_update(
                        constraint="uq_bridge_assets_asset_fingerprint",
                        set_={
                            "asset_code": base_stmt.excluded.asset_code,
                            "name": base_stmt.excluded.name,
                            "road_name": base_stmt.excluded.road_name,
                            "locality": base_stmt.excluded.locality,
                            "clearance_height_m": base_stmt.excluded.clearance_height_m,
                            "clearance_width_m": base_stmt.excluded.clearance_width_m,
                            "max_mass_t": base_stmt.excluded.max_mass_t,
                            "notes": base_stmt.excluded.notes,
                            "source": base_stmt.excluded.source,
                            "geom": base_stmt.excluded.geom,
                            "updated_at": func.now(),
                        },
                    )
                else:
                    stmt = base_stmt.on_conflict_do_nothing(constraint="uq_bridge_assets_asset_fingerprint")
                result = db.execute(stmt)
                if existing is None and result.rowcount == 1:
                    inserted_count += 1
                elif existing is not None and result.rowcount == 1:
                    updated_count += 1
                else:
                    skipped_count += 1
            except Exception as exc:
                errors.append({"row": row_number, "error": str(exc), "row_data": row})

        result_payload = {"file_name": file.filename, "profile": profile_dict, "resolved_update_existing": resolved_update_existing, "resolved_mapping_overrides": resolved_mapping_model.model_dump(exclude_none=True) if resolved_mapping_model else {}, "mapped_columns": header_map, "inserted_count": inserted_count, "updated_count": updated_count, "skipped_count": skipped_count, "error_count": len(errors), "errors": errors[:100]}
        record_import_job(db, profile_id=profile_id, profile_type="bridge_csv", file_name=file.filename, inserted_count=inserted_count, updated_count=updated_count, skipped_count=skipped_count, error_count=len(errors), result_payload=result_payload)
        db.commit()
        return {"status": "completed", **result_payload}
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc


@app.post("/v1/bridges/import/geojson")
async def import_bridges_geojson(file: UploadFile = File(...), update_existing: bool = Form(True), db: Session = Depends(get_db)) -> dict:
    filename = (file.filename or "").lower()
    if not (filename.endswith(".geojson") or filename.endswith(".json")):
        raise HTTPException(status_code=400, detail="Upload a .geojson or .json file")
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file")
    try:
        doc = json.loads(raw.decode("utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {exc}") from exc

    if doc.get("type") == "FeatureCollection":
        features = doc.get("features") or []
    elif doc.get("type") == "Feature":
        features = [doc]
    else:
        raise HTTPException(status_code=400, detail="GeoJSON must be a FeatureCollection or Feature")

    inserted_count = 0
    updated_count = 0
    skipped_count = 0
    errors: list[dict] = []

    try:
        for index, feature in enumerate(features, start=1):
            try:
                data = bridge_from_geojson_feature(feature)
                existing = db.execute(select(BridgeAsset.id).where(BridgeAsset.asset_fingerprint == data["asset_fingerprint"])).scalar_one_or_none()
                values = {
                    "asset_code": data["asset_code"],
                    "asset_fingerprint": data["asset_fingerprint"],
                    "name": data["name"],
                    "road_name": data["road_name"],
                    "locality": data["locality"],
                    "clearance_height_m": data["clearance_height_m"],
                    "clearance_width_m": data["clearance_width_m"],
                    "max_mass_t": data["max_mass_t"],
                    "notes": data["notes"],
                    "source": data["source"],
                    "geom": func.ST_GeomFromGeoJSON(json.dumps(data["geometry_fragment"])),
                }
                base_stmt = pg_insert(BridgeAsset).values(**values)
                if update_existing:
                    stmt = base_stmt.on_conflict_do_update(
                        constraint="uq_bridge_assets_asset_fingerprint",
                        set_={
                            "asset_code": base_stmt.excluded.asset_code,
                            "name": base_stmt.excluded.name,
                            "road_name": base_stmt.excluded.road_name,
                            "locality": base_stmt.excluded.locality,
                            "clearance_height_m": base_stmt.excluded.clearance_height_m,
                            "clearance_width_m": base_stmt.excluded.clearance_width_m,
                            "max_mass_t": base_stmt.excluded.max_mass_t,
                            "notes": base_stmt.excluded.notes,
                            "source": base_stmt.excluded.source,
                            "geom": base_stmt.excluded.geom,
                            "updated_at": func.now(),
                        },
                    )
                else:
                    stmt = base_stmt.on_conflict_do_nothing(constraint="uq_bridge_assets_asset_fingerprint")
                result = db.execute(stmt)
                if existing is None and result.rowcount == 1:
                    inserted_count += 1
                elif existing is not None and result.rowcount == 1:
                    updated_count += 1
                else:
                    skipped_count += 1
            except Exception as exc:
                errors.append({"feature_index": index, "error": str(exc)})

        result_payload = {"file_name": file.filename, "inserted_count": inserted_count, "updated_count": updated_count, "skipped_count": skipped_count, "error_count": len(errors), "errors": errors[:100]}
        record_import_job(db, profile_id=None, profile_type="bridge_geojson", file_name=file.filename, inserted_count=inserted_count, updated_count=updated_count, skipped_count=skipped_count, error_count=len(errors), result_payload=result_payload)
        db.commit()
        return {"status": "completed", **result_payload}
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc


@app.get("/v1/import-jobs")
def list_import_jobs(limit: int = 100, db: Session = Depends(get_db)) -> dict:
    rows = db.execute(select(ImportJob).order_by(ImportJob.created_at.desc()).limit(limit)).scalars().all()
    return {"jobs": [{"job_id": str(row.id), "profile_id": str(row.profile_id) if row.profile_id else None, "profile_type": row.profile_type, "file_name": row.file_name, "status": row.status, "inserted_count": row.inserted_count, "updated_count": row.updated_count, "skipped_count": row.skipped_count, "error_count": row.error_count, "created_at": row.created_at.isoformat() if row.created_at else None} for row in rows]}
