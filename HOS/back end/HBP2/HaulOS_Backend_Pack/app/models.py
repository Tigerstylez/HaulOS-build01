from __future__ import annotations

import uuid

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from .db import Base


class TimestampMixin:
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class VehicleProfile(TimestampMixin, Base):
    __tablename__ = "vehicle_profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    registration: Mapped[str | None] = mapped_column(String(40), nullable=True)
    configuration: Mapped[str | None] = mapped_column(String(80), nullable=True)
    load_type: Mapped[str | None] = mapped_column(String(80), nullable=True)

    combination_type: Mapped[str] = mapped_column(String(80), nullable=False)
    trailer_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    platform_type: Mapped[str | None] = mapped_column(String(80), nullable=True)

    target_combination_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    target_trailer_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    route_direction: Mapped[str | None] = mapped_column(String(80), nullable=True)
    requires_rtaa_reconfiguration: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rtaa_name: Mapped[str | None] = mapped_column(String(120), nullable=True)

    height_m: Mapped[float] = mapped_column(Float, nullable=False)
    width_m: Mapped[float] = mapped_column(Float, nullable=False)
    length_m: Mapped[float] = mapped_column(Float, nullable=False)
    gross_mass_t: Mapped[float] = mapped_column(Float, nullable=False)

    is_road_train: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_oversize: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    hazmat: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    permits_held: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    axle_group_masses_t: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    permit_ids: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    trips: Mapped[list["Trip"]] = relationship(back_populates="vehicle_profile")


class Trip(TimestampMixin, Base):
    __tablename__ = "trips"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status: Mapped[str] = mapped_column(String(40), default="draft", nullable=False)

    origin_label: Mapped[str] = mapped_column(String(255), nullable=False)
    origin_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    origin_lon: Mapped[float | None] = mapped_column(Float, nullable=True)

    destination_label: Mapped[str] = mapped_column(String(255), nullable=False)
    destination_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    destination_lon: Mapped[float | None] = mapped_column(Float, nullable=True)

    route_mode: Mapped[str] = mapped_column(String(40), default="managed_passage", nullable=False)
    route_preference: Mapped[str] = mapped_column(String(40), default="balanced", nullable=False)

    vehicle_profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("vehicle_profiles.id", ondelete="RESTRICT"),
        nullable=False,
    )

    vehicle_profile: Mapped["VehicleProfile"] = relationship(back_populates="trips")
    routes: Mapped[list["Route"]] = relationship(back_populates="trip", cascade="all, delete-orphan")
    hazards: Mapped[list["HazardReport"]] = relationship(back_populates="trip")
    comments: Mapped[list["DriverComment"]] = relationship(back_populates="trip")


class Route(TimestampMixin, Base):
    __tablename__ = "routes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False,
    )

    label: Mapped[str] = mapped_column(String(120), nullable=False)
    route_status: Mapped[str] = mapped_column(String(60), nullable=False)
    route_class: Mapped[str] = mapped_column(String(60), nullable=False)
    legal_status: Mapped[str] = mapped_column(String(60), nullable=False)
    approval_status: Mapped[str] = mapped_column(String(60), nullable=False)

    managed_passage_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    managed_passage_reasons: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    distance_km: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    eta_minutes: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    travel_time_minutes: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    hazard_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    restriction_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    managed_segment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    fuel_confidence: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    rest_confidence: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    pre_departure_briefing: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    upcoming_events: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    geom = mapped_column(
        Geometry(geometry_type="MULTILINESTRING", srid=4326, spatial_index=False),
        nullable=True,
    )

    trip: Mapped["Trip"] = relationship(back_populates="routes")
    segments: Mapped[list["RouteSegment"]] = relationship(back_populates="route", cascade="all, delete-orphan")
    stages: Mapped[list["RouteStage"]] = relationship(back_populates="route", cascade="all, delete-orphan")
    hazards: Mapped[list["HazardReport"]] = relationship(back_populates="route")


class RouteStage(TimestampMixin, Base):
    __tablename__ = "route_stages"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("routes.id", ondelete="CASCADE"),
        nullable=False,
    )

    stage_number: Mapped[int] = mapped_column(Integer, nullable=False)
    stage_type: Mapped[str] = mapped_column(String(80), nullable=False)
    start_location_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    end_location_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    start_combination_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    start_trailer_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_combination_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    end_trailer_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    action_required: Mapped[str | None] = mapped_column(String(120), nullable=True)
    action_status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    route: Mapped["Route"] = relationship(back_populates="stages")


class RouteSegment(TimestampMixin, Base):
    __tablename__ = "route_segments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("routes.id", ondelete="CASCADE"),
        nullable=False,
    )

    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    edge_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    stage_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    road_name: Mapped[str] = mapped_column(String(255), nullable=False)
    direction_of_travel: Mapped[str | None] = mapped_column(String(40), nullable=True)
    location_name: Mapped[str] = mapped_column(String(255), nullable=False)

    start_landmark: Mapped[str | None] = mapped_column(String(255), nullable=True)
    end_landmark: Mapped[str | None] = mapped_column(String(255), nullable=True)

    distance_km: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    estimated_travel_time_minutes: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    local_roads_in_scope: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    static_restrictions: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    live_hazards: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    managed_movement: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    trigger_rules: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    hazard_visibility: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    geom = mapped_column(
        Geometry(geometry_type="LINESTRING", srid=4326, spatial_index=False),
        nullable=True,
    )

    route: Mapped["Route"] = relationship(back_populates="segments")


class HazardReport(TimestampMixin, Base):
    __tablename__ = "hazard_reports"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("trips.id", ondelete="SET NULL"),
        nullable=True,
    )
    route_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("routes.id", ondelete="SET NULL"),
        nullable=True,
    )

    category: Mapped[str] = mapped_column(String(80), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)

    road_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)

    message: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(40), default="driver", nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.8, nullable=False)
    delay_minutes: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    extra_data: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    geom = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=False),
        nullable=True,
    )

    trip: Mapped["Trip | None"] = relationship(back_populates="hazards")
    route: Mapped["Route | None"] = relationship(back_populates="hazards")


class DriverComment(TimestampMixin, Base):
    __tablename__ = "driver_comments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("trips.id", ondelete="SET NULL"),
        nullable=True,
    )

    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(120), nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.8, nullable=False)
    source: Mapped[str] = mapped_column(String(40), default="driver", nullable=False)

    trip: Mapped["Trip | None"] = relationship(back_populates="comments")


class BridgeAsset(TimestampMixin, Base):
    __tablename__ = "bridge_assets"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)

    asset_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    asset_fingerprint: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    road_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    locality: Mapped[str | None] = mapped_column(String(255), nullable=True)

    clearance_height_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    clearance_width_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_mass_t: Mapped[float | None] = mapped_column(Float, nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(String(80), nullable=True)

    geom = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=False),
        nullable=False,
    )


class PowerlineAsset(TimestampMixin, Base):
    __tablename__ = "powerline_assets"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)

    asset_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    owner_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    line_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    road_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    locality: Mapped[str | None] = mapped_column(String(255), nullable=True)

    clearance_height_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    managed_action_default: Mapped[str | None] = mapped_column(String(80), nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(String(80), nullable=True)

    geom = mapped_column(
        Geometry(geometry_type="LINESTRING", srid=4326, spatial_index=False),
        nullable=False,
    )


class FuelStopAsset(TimestampMixin, Base):
    __tablename__ = "fuel_stop_assets"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    road_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    locality: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="available", nullable=False)
    queue_level: Mapped[str | None] = mapped_column(String(40), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    geom = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=False),
        nullable=False,
    )


class FuelReport(TimestampMixin, Base):
    __tablename__ = "fuel_reports"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fuel_stop_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("fuel_stop_assets.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    queue_level: Mapped[str | None] = mapped_column(String(40), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(40), default="driver", nullable=False)


class RestAreaAsset(TimestampMixin, Base):
    __tablename__ = "rest_area_assets"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    road_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    locality: Mapped[str | None] = mapped_column(String(255), nullable=True)
    area_type: Mapped[str] = mapped_column(String(40), default="rest_area", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="available", nullable=False)
    supports_road_train: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    geom = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=False),
        nullable=False,
    )


class RestReport(TimestampMixin, Base):
    __tablename__ = "rest_reports"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rest_area_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("rest_area_assets.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    space_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(40), default="driver", nullable=False)


class ImportProfile(TimestampMixin, Base):
    __tablename__ = "import_profiles"
    __table_args__ = (
        UniqueConstraint("profile_type", "name", name="uq_import_profiles_type_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_type: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    mapping_overrides: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    update_existing_default: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    source_vendor: Mapped[str | None] = mapped_column(String(120), nullable=True)
    source_version: Mapped[str | None] = mapped_column(String(80), nullable=True)


class ImportJob(TimestampMixin, Base):
    __tablename__ = "import_jobs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("import_profiles.id", ondelete="SET NULL"),
        nullable=True,
    )
    profile_type: Mapped[str] = mapped_column(String(40), nullable=False)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="completed", nullable=False)

    inserted_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    skipped_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    result_payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
