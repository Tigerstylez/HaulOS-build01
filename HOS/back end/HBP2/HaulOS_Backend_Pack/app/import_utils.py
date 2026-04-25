from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from pydantic import ValidationError

from .schemas import BridgeColumnOverrideRequest


CSV_BRIDGE_COLUMN_ALIASES = {
    "asset_code": ["asset_code", "bridge_id", "bridgeid", "id", "code", "asset id", "assetid"],
    "name": ["name", "bridge_name", "bridge name", "structure_name", "structure name", "structname"],
    "road_name": ["road_name", "road name", "road", "rd_name", "route_name", "route name"],
    "locality": ["locality", "town", "suburb", "location_name", "location name", "place", "area", "township"],
    "clearance_height_m": ["clearance_height_m", "clearance height m", "clearance_height", "height_m", "height", "clrht", "vertical_clearance", "vertical clearance"],
    "clearance_width_m": ["clearance_width_m", "clearance width m", "clearance_width", "width_m", "width", "clrwd", "horizontal_clearance", "horizontal clearance"],
    "max_mass_t": ["max_mass_t", "mass_t", "masscap", "mass_limit_t", "mass limit t", "weight_t", "weight", "load_limit_t", "load limit t"],
    "lat": ["lat", "latitude", "y"],
    "lon": ["lon", "lng", "longitude", "x"],
    "notes": ["notes", "note", "comment", "comments", "remarks"],
    "source": ["source", "data_source", "data source"],
}

CANONICAL_BRIDGE_FIELDS = set(CSV_BRIDGE_COLUMN_ALIASES.keys())


def normalize_header(value: str) -> str:
    return value.strip().lower().replace("-", " ").replace("_", " ")


def normalize_text(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return " ".join(text.lower().split())


def to_float(value: object | None) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return float(text)


def build_csv_header_map(fieldnames: list[str] | None) -> dict[str, str]:
    if not fieldnames:
        return {}
    normalized_to_original = {normalize_header(name): name for name in fieldnames if name is not None}
    header_map: dict[str, str] = {}
    for canonical_field, aliases in CSV_BRIDGE_COLUMN_ALIASES.items():
        for alias in aliases:
            alias_norm = normalize_header(alias)
            if alias_norm in normalized_to_original:
                header_map[canonical_field] = normalized_to_original[alias_norm]
                break
    return header_map


def build_csv_header_map_with_overrides(fieldnames: list[str] | None, mapping_overrides: BridgeColumnOverrideRequest | None = None) -> dict[str, str]:
    header_map = build_csv_header_map(fieldnames)
    if not fieldnames:
        return header_map

    normalized_to_original = {normalize_header(name): name for name in fieldnames if name is not None}
    if mapping_overrides is None:
        return header_map

    for canonical_field, source_header in mapping_overrides.model_dump(exclude_none=True).items():
        if canonical_field not in CANONICAL_BRIDGE_FIELDS:
            continue
        source_norm = normalize_header(source_header)
        if source_norm not in normalized_to_original:
            raise HTTPException(
                status_code=400,
                detail=f"Mapping override for '{canonical_field}' points to missing source header '{source_header}'",
            )
        header_map[canonical_field] = normalized_to_original[source_norm]
    return header_map


def build_header_diagnostics(fieldnames: list[str] | None, header_map: dict[str, str]) -> dict[str, Any]:
    source_headers = fieldnames or []
    matched_source_headers = set(header_map.values())
    unmatched_source_headers = [h for h in source_headers if h not in matched_source_headers]
    return {
        "source_headers": source_headers,
        "mapped_columns": header_map,
        "unmatched_source_headers": unmatched_source_headers,
    }


def csv_value(row: dict, header_map: dict[str, str], field: str) -> object | None:
    original_header = header_map.get(field)
    if not original_header:
        return None
    return row.get(original_header)


def build_bridge_fingerprint(data: dict) -> str:
    asset_code = normalize_text(data.get("asset_code"))
    if asset_code:
        return f"asset_code:{asset_code}"

    road_name = normalize_text(data.get("road_name")) or ""
    locality = normalize_text(data.get("locality")) or ""
    height = data.get("clearance_height_m")
    width = data.get("clearance_width_m")
    mass = data.get("max_mass_t")
    lat = data.get("lat")
    lon = data.get("lon")

    lat_key = f"{lat:.6f}" if lat is not None else ""
    lon_key = f"{lon:.6f}" if lon is not None else ""
    height_key = f"{height:.3f}" if height is not None else ""
    width_key = f"{width:.3f}" if width is not None else ""
    mass_key = f"{mass:.3f}" if mass is not None else ""

    return "|".join(["bridge", road_name, locality, height_key, width_key, mass_key, lat_key, lon_key])


def bridge_from_csv_row(row: dict, header_map: dict[str, str]) -> dict:
    lat = to_float(csv_value(row, header_map, "lat"))
    lon = to_float(csv_value(row, header_map, "lon"))
    if lat is None or lon is None:
        raise ValueError("Missing lat/lon columns")

    data = {
        "asset_code": csv_value(row, header_map, "asset_code"),
        "name": csv_value(row, header_map, "name"),
        "road_name": csv_value(row, header_map, "road_name"),
        "locality": csv_value(row, header_map, "locality"),
        "clearance_height_m": to_float(csv_value(row, header_map, "clearance_height_m")),
        "clearance_width_m": to_float(csv_value(row, header_map, "clearance_width_m")),
        "max_mass_t": to_float(csv_value(row, header_map, "max_mass_t")),
        "notes": csv_value(row, header_map, "notes"),
        "source": csv_value(row, header_map, "source") or "csv_import",
        "lat": lat,
        "lon": lon,
    }
    data["asset_code"] = normalize_text(data["asset_code"])
    data["name"] = str(data["name"]).strip() if data["name"] is not None else None
    data["road_name"] = str(data["road_name"]).strip() if data["road_name"] is not None else None
    data["locality"] = str(data["locality"]).strip() if data["locality"] is not None else None
    data["notes"] = str(data["notes"]).strip() if data["notes"] is not None else None
    data["source"] = str(data["source"]).strip() if data["source"] is not None else "csv_import"
    data["asset_fingerprint"] = build_bridge_fingerprint(data)
    return data


def bridge_from_geojson_feature(feature: dict) -> dict:
    if feature.get("type") != "Feature":
        raise ValueError("GeoJSON item is not a Feature")
    geometry = feature.get("geometry")
    if not geometry:
        raise ValueError("Feature missing geometry")
    if geometry.get("type") != "Point":
        raise ValueError("Bridge GeoJSON must use Point geometry")

    coords = geometry.get("coordinates")
    if not isinstance(coords, list) or len(coords) < 2:
        raise ValueError("Invalid Point coordinates")

    lon = float(coords[0])
    lat = float(coords[1])
    props = feature.get("properties") or {}

    data = {
        "asset_code": normalize_text(props.get("asset_code") or props.get("bridge_id") or props.get("id") or props.get("code")),
        "name": props.get("name") or props.get("bridge_name"),
        "road_name": props.get("road_name") or props.get("road"),
        "locality": props.get("locality") or props.get("town") or props.get("suburb") or props.get("location_name"),
        "clearance_height_m": to_float(props.get("clearance_height_m") or props.get("height_m") or props.get("height")),
        "clearance_width_m": to_float(props.get("clearance_width_m") or props.get("width_m") or props.get("width")),
        "max_mass_t": to_float(props.get("max_mass_t") or props.get("mass_t") or props.get("mass_limit_t") or props.get("weight_t")),
        "notes": props.get("notes") or props.get("comment") or props.get("comments"),
        "source": props.get("source") or "geojson_import",
        "lat": lat,
        "lon": lon,
        "geometry_fragment": geometry,
    }
    data["asset_fingerprint"] = build_bridge_fingerprint(data)
    return data


def parse_bridge_mapping_overrides(mapping_overrides_json: str | None) -> BridgeColumnOverrideRequest | None:
    if not mapping_overrides_json:
        return None
    try:
        return BridgeColumnOverrideRequest.model_validate_json(mapping_overrides_json)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid mapping_overrides_json: {exc}") from exc


def preview_bridge_action(existing_present: bool, update_existing: bool) -> str:
    if not existing_present:
        return "would_insert"
    if update_existing:
        return "would_update"
    return "would_skip_duplicate"
