from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class VehicleInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    registration: str | None = None
    configuration: str | None = None
    load_type: str | None = None

    combination_type: str
    trailer_count: int = Field(ge=1)
    platform_type: str | None = None

    target_combination_type: str | None = None
    target_trailer_count: int | None = Field(default=None, ge=1)
    route_direction: str | None = None
    requires_rtaa_reconfiguration: bool = False
    rtaa_name: str | None = None

    height_m: float = Field(gt=0)
    width_m: float = Field(gt=0)
    length_m: float = Field(gt=0)
    gross_mass_t: float = Field(gt=0)

    axle_group_masses_t: list[float] = Field(default_factory=list)
    permit_ids: list[str] = Field(default_factory=list)

    is_road_train: bool = False
    is_oversize: bool = False
    hazmat: bool = False
    permits_held: bool = False
    metadata_json: dict = Field(default_factory=dict)


class TripCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    originLabel: str
    destinationLabel: str
    vehicle: VehicleInput


class CalculateRouteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    trip_id: str
    mode: str = "managed_passage"
    preference: str = "balanced"


class HazardCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    trip_id: str | None = None
    route_id: str | None = None
    category: str
    severity: str
    road_name: str | None = None
    location_name: str | None = None
    lat: float | None = None
    lon: float | None = None
    message: str
    source: str = "driver"
    confidence_score: float = 0.8
    delay_minutes: float = 0.0
    extra_data: dict = Field(default_factory=dict)


class CommentCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    trip_id: str | None = None
    entity_type: str
    entity_id: str
    comment: str
    confidence_score: float = 0.8
    source: str = "driver"


class FuelReportCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    fuel_stop_id: str | None = None
    status: str
    queue_level: str | None = None
    comment: str | None = None
    source: str = "driver"


class RestReportCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rest_area_id: str | None = None
    status: str
    space_type: str | None = None
    comment: str | None = None
    source: str = "driver"


class BridgeAssetCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    asset_code: str | None = None
    name: str | None = None
    road_name: str | None = None
    locality: str | None = None
    clearance_height_m: float | None = None
    clearance_width_m: float | None = None
    max_mass_t: float | None = None
    notes: str | None = None
    source: str | None = None
    lat: float
    lon: float


class PowerlineAssetCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    asset_code: str | None = None
    owner_name: str | None = None
    line_name: str | None = None
    road_name: str | None = None
    locality: str | None = None
    clearance_height_m: float | None = None
    managed_action_default: str | None = "utility_line_lift"
    notes: str | None = None
    source: str | None = None
    wkt_linestring: str


class BridgeColumnOverrideRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_code: str | None = None
    name: str | None = None
    road_name: str | None = None
    locality: str | None = None
    clearance_height_m: str | None = None
    clearance_width_m: str | None = None
    max_mass_t: str | None = None
    lat: str | None = None
    lon: str | None = None
    notes: str | None = None
    source: str | None = None


class ImportProfileCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile_type: str = "bridge_csv"
    name: str
    description: str | None = None
    mapping_overrides: BridgeColumnOverrideRequest
    update_existing_default: bool = True
    source_vendor: str | None = None
    source_version: str | None = None


class ImportProfileUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    description: str | None = None
    mapping_overrides: BridgeColumnOverrideRequest | None = None
    update_existing_default: bool | None = None
    source_vendor: str | None = None
    source_version: str | None = None
