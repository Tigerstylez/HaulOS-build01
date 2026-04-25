from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import heapq
import uuid
from typing import Dict, List, Optional, Tuple


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class RouteStatus(str, Enum):
    clean_legal = "clean_legal"
    legal_with_hazards = "legal_with_hazards"
    managed_passage_required = "managed_passage_required"
    no_workable_route = "no_workable_route"


class RouteClass(str, Enum):
    best_legal = "best_legal"
    fastest_compliant = "fastest_compliant"
    lowest_hazard = "lowest_hazard"
    contraflow_required = "contraflow_required"
    managed_passage = "managed_passage"


class LegalStatus(str, Enum):
    legal = "legal"
    legal_with_conditions = "legal_with_conditions"
    requires_controlled_movement = "requires_controlled_movement"
    not_legal_for_departure = "not_legal_for_departure"


class ApprovalStatus(str, Enum):
    cleared = "cleared"
    pending = "pending"
    rejected = "rejected"
    not_required = "not_required"


class MovementType(str, Enum):
    none = "none"
    contraflow = "contraflow"
    utility_line_lift = "utility_line_lift"
    controlled_movement = "controlled_movement"
    rtaa_reconfiguration = "rtaa_reconfiguration"


class ActionType(str, Enum):
    escort_coordination = "escort_coordination"
    traffic_guidance_scheme_compliance = "traffic_guidance_scheme_compliance"
    utility_line_lift = "utility_line_lift"
    permit_variation = "permit_variation"
    temporary_road_closure = "temporary_road_closure"
    lane_control_setup = "lane_control_setup"
    reconfigure_at_rtaa = "reconfigure_at_rtaa"


@dataclass(frozen=True)
class Vehicle:
    combination_type: str
    trailer_count: int
    platform_type: Optional[str]
    target_combination_type: Optional[str]
    target_trailer_count: Optional[int]
    route_direction: Optional[str]
    requires_rtaa_reconfiguration: bool
    rtaa_name: Optional[str]
    height_m: float
    width_m: float
    length_m: float
    gross_mass_t: float
    is_road_train: bool
    is_oversize: bool
    hazmat: bool
    permits_held: bool


@dataclass(frozen=True)
class Node:
    node_id: str
    label: str
    lat: float
    lon: float


@dataclass(frozen=True)
class Hazard:
    hazard_id: str
    category: str
    severity: Severity
    message: str
    delay_minutes: float = 0.0
    confidence_score: float = 0.8
    source: str = "system"
    reported_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class AuthorityAction:
    action_type: ActionType
    responsible_party: str
    reference_id: Optional[str] = None
    note: Optional[str] = None


@dataclass(frozen=True)
class ManagedTemplate:
    movement_type: MovementType
    title: str
    reason_key: str
    driver_message: str
    dispatcher_message: str
    approval_required: bool = True
    escort_required: bool = False
    temporary_traffic_control_required: bool = False
    intersection_control_required: bool = False
    utility_intervention_required: bool = False
    uses_opposing_lane: bool = False
    traffic_guidance_scheme_id: Optional[str] = None
    traffic_guidance_scheme_name: Optional[str] = None
    actions: Tuple[AuthorityAction, ...] = tuple()


@dataclass(frozen=True)
class Restriction:
    max_height_m: Optional[float] = None
    max_width_m: Optional[float] = None
    max_mass_t: Optional[float] = None
    road_trains_allowed: bool = True
    oversize_allowed: bool = True
    permit_required: bool = False
    managed_if_height_gt_m: Optional[float] = None
    managed_if_width_gt_m: Optional[float] = None
    managed_if_mass_gt_t: Optional[float] = None
    managed_template: Optional[ManagedTemplate] = None


@dataclass(frozen=True)
class Edge:
    edge_id: str
    from_node: str
    to_node: str
    road_name: str
    location_name: str
    distance_km: float
    travel_minutes: float
    restrictions: Restriction = field(default_factory=Restriction)
    hazards: Tuple[Hazard, ...] = tuple()
    local_roads_in_scope: Tuple[str, ...] = tuple()
    start_landmark: Optional[str] = None
    end_landmark: Optional[str] = None


@dataclass
class EdgeEval:
    allowed: bool
    travel_minutes: float
    distance_km: float
    hazard_penalty: float
    managed_penalty: float
    managed_reasons: List[str]
    managed_template: Optional[ManagedTemplate]
    departure_block: bool
    hazard_list: List[Hazard]
    issue_notes: List[str]


@dataclass
class RouteResultInternal:
    path_nodes: List[str]
    path_edges: List[Edge]
    total_distance_km: float
    total_minutes: float
    hazard_count: int
    restriction_count: int
    managed_segment_count: int
    managed_reasons: List[str]
    briefings: List[dict]
    upcoming_events: List[dict]
    route_status: RouteStatus
    route_class: RouteClass
    legal_status: LegalStatus
    approval_status: ApprovalStatus
    score: float


class RoadNetwork:
    def __init__(self) -> None:
        self.nodes: Dict[str, Node] = {}
        self.adj: Dict[str, List[Edge]] = {}
        self.label_map: Dict[str, str] = {}

    def add_node(self, node: Node, aliases: Optional[List[str]] = None) -> None:
        self.nodes[node.node_id] = node
        self.adj.setdefault(node.node_id, [])
        for key in [node.label] + (aliases or []):
            self.label_map[key.strip().lower()] = node.node_id

    def add_edge(self, edge: Edge) -> None:
        self.adj.setdefault(edge.from_node, []).append(edge)

    def get_node_id(self, label: str) -> Optional[str]:
        return self.label_map.get(label.strip().lower())


class Router:
    def __init__(self, network: RoadNetwork) -> None:
        self.network = network

    def calculate(self, start_id: str, end_id: str, vehicle: Vehicle, preference: str) -> RouteResultInternal:
        queue: List[Tuple[float, int, str]] = []
        seq = 0
        heapq.heappush(queue, (0.0, seq, start_id))
        cost_so_far: Dict[str, float] = {start_id: 0.0}
        came_from: Dict[str, Tuple[str, Edge]] = {}

        while queue:
            _, _, current = heapq.heappop(queue)
            if current == end_id:
                break
            for edge in self.network.adj.get(current, []):
                ev = self._evaluate_edge(edge, vehicle)
                if not ev.allowed:
                    continue
                edge_cost = self._edge_score(ev, preference)
                new_cost = cost_so_far[current] + edge_cost
                if edge.to_node not in cost_so_far or new_cost < cost_so_far[edge.to_node]:
                    cost_so_far[edge.to_node] = new_cost
                    came_from[edge.to_node] = (current, edge)
                    seq += 1
                    heapq.heappush(queue, (new_cost, seq, edge.to_node))

        if end_id not in cost_so_far:
            return RouteResultInternal([], [], 0, 0, 0, 0, 0, [], [], [], RouteStatus.no_workable_route, RouteClass.managed_passage, LegalStatus.not_legal_for_departure, ApprovalStatus.rejected, 999999)

        path_nodes, path_edges = self._reconstruct(came_from, start_id, end_id)
        return self._summarize(path_nodes, path_edges, vehicle, preference, cost_so_far[end_id])

    def _edge_score(self, ev: EdgeEval, preference: str) -> float:
        if preference == "fastest":
            return ev.travel_minutes + (ev.hazard_penalty * 0.25) + (ev.managed_penalty * 0.4)
        if preference == "lowest_hazard":
            return (ev.travel_minutes * 0.8) + ev.hazard_penalty + ev.managed_penalty
        return ev.travel_minutes + ev.hazard_penalty + ev.managed_penalty

    def _evaluate_edge(self, edge: Edge, vehicle: Vehicle) -> EdgeEval:
        r = edge.restrictions
        hazard_penalty = sum(self._hazard_penalty(h) for h in edge.hazards)
        managed_penalty = 0.0
        managed_reasons: List[str] = []
        managed_template: Optional[ManagedTemplate] = None
        departure_block = False
        issue_notes: List[str] = []

        if vehicle.is_road_train and not r.road_trains_allowed:
            return EdgeEval(False, 0, 0, 0, 0, [], None, False, list(edge.hazards), ["road trains not allowed"])
        if vehicle.is_oversize and not r.oversize_allowed:
            return EdgeEval(False, 0, 0, 0, 0, [], None, False, list(edge.hazards), ["oversize not allowed"])

        def apply_managed(reason: str) -> None:
            nonlocal managed_penalty, managed_template, departure_block
            if r.managed_template is None:
                raise RuntimeError("Managed rule missing template")
            managed_penalty = max(managed_penalty, 40.0)
            managed_template = r.managed_template
            if r.managed_template.reason_key not in managed_reasons:
                managed_reasons.append(r.managed_template.reason_key)
            departure_block = True
            issue_notes.append(reason)

        if r.max_height_m is not None and vehicle.height_m > r.max_height_m:
            if r.managed_if_height_gt_m is not None and vehicle.height_m > r.managed_if_height_gt_m and r.managed_template:
                apply_managed(f"height {vehicle.height_m:.2f}m exceeds normal limit {r.max_height_m:.2f}m")
            else:
                return EdgeEval(False, 0, 0, 0, 0, [], None, False, list(edge.hazards), ["height blocked"])

        if r.max_width_m is not None and vehicle.width_m > r.max_width_m:
            if r.managed_if_width_gt_m is not None and vehicle.width_m > r.managed_if_width_gt_m and r.managed_template:
                apply_managed(f"width {vehicle.width_m:.2f}m exceeds normal limit {r.max_width_m:.2f}m")
            else:
                return EdgeEval(False, 0, 0, 0, 0, [], None, False, list(edge.hazards), ["width blocked"])

        if r.max_mass_t is not None and vehicle.gross_mass_t > r.max_mass_t:
            if r.managed_if_mass_gt_t is not None and vehicle.gross_mass_t > r.managed_if_mass_gt_t and r.managed_template:
                apply_managed(f"mass {vehicle.gross_mass_t:.2f}t exceeds normal limit {r.max_mass_t:.2f}t")
            else:
                return EdgeEval(False, 0, 0, 0, 0, [], None, False, list(edge.hazards), ["mass blocked"])

        if r.permit_required and not vehicle.permits_held:
            departure_block = True
            issue_notes.append("permit required before departure")
            if "permit_variation_required" not in managed_reasons:
                managed_reasons.append("permit_variation_required")
            managed_penalty = max(managed_penalty, 20.0)

        return EdgeEval(True, edge.travel_minutes, edge.distance_km, hazard_penalty, managed_penalty, managed_reasons, managed_template, departure_block, list(edge.hazards), issue_notes)

    def _hazard_penalty(self, hazard: Hazard) -> float:
        base = {Severity.low: 4.0, Severity.medium: 10.0, Severity.high: 20.0, Severity.critical: 35.0}[hazard.severity]
        return base + hazard.delay_minutes

    def _reconstruct(self, came_from: Dict[str, Tuple[str, Edge]], start_id: str, end_id: str) -> Tuple[List[str], List[Edge]]:
        nodes = [end_id]
        edges: List[Edge] = []
        current = end_id
        while current != start_id:
            prev_node, edge = came_from[current]
            nodes.append(prev_node)
            edges.append(edge)
            current = prev_node
        nodes.reverse()
        edges.reverse()
        return nodes, edges

    def _summarize(self, path_nodes: List[str], path_edges: List[Edge], vehicle: Vehicle, preference: str, score: float) -> RouteResultInternal:
        total_distance = 0.0
        total_minutes = 0.0
        hazard_count = 0
        restriction_count = 0
        managed_segment_count = 0
        managed_reasons: List[str] = []
        briefings: List[dict] = []
        upcoming_events: List[dict] = []
        km_cursor = 0.0

        for edge in path_edges:
            ev = self._evaluate_edge(edge, vehicle)
            total_distance += edge.distance_km
            total_minutes += edge.travel_minutes
            hazard_count += len(edge.hazards)

            if ev.managed_template is not None:
                managed_segment_count += 1
                restriction_count += 1
                if ev.managed_template.reason_key not in managed_reasons:
                    managed_reasons.append(ev.managed_template.reason_key)
                briefings.append({
                    "briefing_id": f"briefing_{edge.edge_id}",
                    "briefing_type": "managed_passage",
                    "title": ev.managed_template.title,
                    "location_name": edge.location_name,
                    "severity": "high",
                    "departure_allowed": False,
                    "driver_message": ev.managed_template.driver_message,
                    "dispatcher_actions": [a.action_type.value for a in ev.managed_template.actions],
                    "reference_ids": [x for x in [ev.managed_template.traffic_guidance_scheme_id] if x],
                })
                upcoming_events.append({
                    "event_id": f"evt_{edge.edge_id}",
                    "event_type": "managed_passage",
                    "event_subtype": ev.managed_template.movement_type.value,
                    "title": ev.managed_template.title,
                    "location_name": edge.location_name,
                    "distance_to_event_km": round(km_cursor + edge.distance_km, 1),
                    "trigger_distances_km": [20, 5, 1],
                    "requires_acknowledgement": True,
                    "driver_message": ev.managed_template.driver_message,
                    "dispatcher_message": ev.managed_template.dispatcher_message,
                    "voice_message": ev.managed_template.title,
                    "repeat": True,
                })

            for hz in edge.hazards:
                briefing_type = "hazard"
                if hz.category == "fuel_issue":
                    briefing_type = "fuel"
                elif hz.category == "rest_stop_capacity_issue":
                    briefing_type = "rest"
                briefings.append({
                    "briefing_id": f"briefing_{hz.hazard_id}",
                    "briefing_type": briefing_type,
                    "title": hz.message,
                    "location_name": edge.location_name,
                    "severity": hz.severity.value,
                    "departure_allowed": True,
                    "driver_message": hz.message,
                    "dispatcher_actions": [],
                    "reference_ids": [hz.hazard_id],
                })
                upcoming_events.append({
                    "event_id": hz.hazard_id,
                    "event_type": "hazard",
                    "event_subtype": hz.category,
                    "title": hz.message,
                    "location_name": edge.location_name,
                    "distance_to_event_km": round(km_cursor + edge.distance_km, 1),
                    "trigger_distances_km": [20, 10, 2] if hz.severity in {Severity.high, Severity.critical} else [10, 5, 1],
                    "requires_acknowledgement": hz.severity in {Severity.high, Severity.critical},
                    "driver_message": hz.message,
                    "dispatcher_message": None,
                    "voice_message": hz.message,
                    "repeat": True,
                })
            km_cursor += edge.distance_km

        if managed_segment_count > 0:
            route_status = RouteStatus.managed_passage_required
            legal_status = LegalStatus.requires_controlled_movement
            approval_status = ApprovalStatus.pending
            route_class = RouteClass.contraflow_required if "contraflow_required" in managed_reasons else RouteClass.managed_passage
        elif hazard_count > 0:
            route_status = RouteStatus.legal_with_hazards
            legal_status = LegalStatus.legal_with_conditions
            approval_status = ApprovalStatus.not_required
            route_class = {"balanced": RouteClass.best_legal, "fastest": RouteClass.fastest_compliant, "lowest_hazard": RouteClass.lowest_hazard}[preference]
        else:
            route_status = RouteStatus.clean_legal
            legal_status = LegalStatus.legal
            approval_status = ApprovalStatus.cleared
            route_class = {"balanced": RouteClass.best_legal, "fastest": RouteClass.fastest_compliant, "lowest_hazard": RouteClass.lowest_hazard}[preference]

        return RouteResultInternal(path_nodes, path_edges, round(total_distance, 1), round(total_minutes, 1), hazard_count, restriction_count, managed_segment_count, managed_reasons, briefings, upcoming_events, route_status, route_class, legal_status, approval_status, round(score, 2))


NETWORK = RoadNetwork()


def build_demo_network() -> None:
    NETWORK.add_node(Node("perth", "Perth Depot", -31.952, 115.861), aliases=["perth"])
    NETWORK.add_node(Node("wubin", "Wubin RTAA", -30.110, 116.630), aliases=["wubin", "wubin rtaa"])
    NETWORK.add_node(Node("geraldton", "Geraldton", -28.777, 114.614), aliases=["geraldton"])
    NETWORK.add_node(Node("carnarvon", "Carnarvon RTAA", -24.880, 113.659), aliases=["carnarvon", "carnarvon rtaa"])
    NETWORK.add_node(Node("mount_magnet_n", "Mount Magnet Northbound Entry", -28.061, 117.842), aliases=["mount magnet", "mount magnet northbound entry"])
    NETWORK.add_node(Node("mount_magnet_s", "Mount Magnet South Exit", -28.070, 117.850), aliases=["mount magnet south exit"])
    NETWORK.add_node(Node("meekatharra", "Meekatharra", -26.611, 118.492), aliases=["meekatharra"])
    NETWORK.add_node(Node("newman", "Newman", -23.357, 119.731), aliases=["newman"])

    contraflow_template = ManagedTemplate(
        movement_type=MovementType.contraflow,
        title="Contra flow required",
        reason_key="contraflow_required",
        driver_message="Do not proceed until escort and traffic control are confirmed.",
        dispatcher_message="Arrange controlled contraflow movement through Mount Magnet townsite.",
        approval_required=True,
        escort_required=True,
        temporary_traffic_control_required=True,
        intersection_control_required=True,
        uses_opposing_lane=True,
        traffic_guidance_scheme_id="TGS RM0395-18-11",
        traffic_guidance_scheme_name="Great Northern Hwy - Northbound through Mount Magnet Townsite",
        actions=(
            AuthorityAction(ActionType.escort_coordination, "escort provider"),
            AuthorityAction(ActionType.traffic_guidance_scheme_compliance, "main roads wa", "TGS RM0395-18-11"),
            AuthorityAction(ActionType.lane_control_setup, "traffic control crew", "TGS RM0395-18-11"),
        ),
    )

    powerline_template = ManagedTemplate(
        movement_type=MovementType.utility_line_lift,
        title="Powerline lift required",
        reason_key="powerline_lift_required",
        driver_message="Do not proceed until utility clearance and line-lift are confirmed.",
        dispatcher_message="Coordinate utility line-lift before movement.",
        approval_required=True,
        temporary_traffic_control_required=True,
        utility_intervention_required=True,
        actions=(
            AuthorityAction(ActionType.utility_line_lift, "power utility"),
            AuthorityAction(ActionType.temporary_road_closure, "traffic control crew"),
        ),
    )

    NETWORK.add_edge(Edge("e1", "perth", "wubin", "Great Northern Highway", "Perth to Wubin", 250, 170, hazards=(Hazard("hz_debris_001", "debris", Severity.medium, "Debris reported left lane near Wubin", 5),)))
    NETWORK.add_edge(Edge("e2", "wubin", "mount_magnet_n", "Great Northern Highway", "Wubin to Mount Magnet", 310, 220, hazards=(Hazard("hz_fuel_001", "fuel_issue", Severity.medium, "Fuel reported low supply ahead", 0),)))
    NETWORK.add_edge(Edge("e3", "mount_magnet_n", "mount_magnet_s", "Great Northern Highway", "Great Northern Highway northbound through Mount Magnet townsite", 6, 15, restrictions=Restriction(max_width_m=6.5, managed_if_width_gt_m=6.5, managed_template=contraflow_template, permit_required=True), local_roads_in_scope=("Mt Magnet Leinster Road", "Richardson Street"), start_landmark="Mount Magnet Leinster Road intersection", end_landmark="Swagman Roadhouse access"))
    NETWORK.add_edge(Edge("e4", "mount_magnet_s", "meekatharra", "Great Northern Highway", "Mount Magnet to Meekatharra", 320, 230, hazards=(Hazard("hz_rest_001", "rest_stop_capacity_issue", Severity.low, "Next major rest stop reported nearly full", 0),)))
    NETWORK.add_edge(Edge("e5", "meekatharra", "newman", "Great Northern Highway", "Meekatharra to Newman", 420, 300, restrictions=Restriction(max_mass_t=80)))
    NETWORK.add_edge(Edge("e6", "perth", "geraldton", "Brand Highway", "Perth to Geraldton", 430, 320))
    NETWORK.add_edge(Edge("e7", "geraldton", "carnarvon", "North West Coastal Highway", "Geraldton to Carnarvon", 480, 350, restrictions=Restriction(max_height_m=5.0, managed_if_height_gt_m=5.0, managed_template=powerline_template), hazards=(Hazard("hz_power_001", "powerline_issue", Severity.high, "Low powerline clearance zone ahead", 10),)))


build_demo_network()
ROUTER = Router(NETWORK)


def edge_linestring_wkt(edge_id: str) -> str | None:
    for edge_list in NETWORK.adj.values():
        for edge in edge_list:
            if edge.edge_id == edge_id:
                start = NETWORK.nodes[edge.from_node]
                end = NETWORK.nodes[edge.to_node]
                return f"LINESTRING({start.lon} {start.lat}, {end.lon} {end.lat})"
    return None


def build_vehicle(data: dict) -> Vehicle:
    return Vehicle(
        combination_type=data["combination_type"],
        trailer_count=data["trailer_count"],
        platform_type=data.get("platform_type"),
        target_combination_type=data.get("target_combination_type"),
        target_trailer_count=data.get("target_trailer_count"),
        route_direction=data.get("route_direction"),
        requires_rtaa_reconfiguration=data.get("requires_rtaa_reconfiguration", False),
        rtaa_name=data.get("rtaa_name"),
        height_m=data["height_m"],
        width_m=data["width_m"],
        length_m=data["length_m"],
        gross_mass_t=data["gross_mass_t"],
        is_road_train=data.get("is_road_train", False),
        is_oversize=data.get("is_oversize", False),
        hazmat=data.get("hazmat", False),
        permits_held=data.get("permits_held", False),
    )


def default_rtaa_for_vehicle(vehicle: Vehicle) -> Optional[str]:
    if vehicle.target_trailer_count == 3 or vehicle.trailer_count == 3:
        if vehicle.route_direction == "inland_north":
            return "Wubin RTAA"
        if vehicle.route_direction == "coastal_north":
            return "Carnarvon RTAA"
    return vehicle.rtaa_name


def should_use_rtaa_reconfiguration(vehicle: Vehicle, origin_label: str) -> bool:
    if not origin_label.lower().startswith("perth"):
        return False
    if vehicle.requires_rtaa_reconfiguration:
        return True
    if vehicle.target_trailer_count == 3 and vehicle.trailer_count < 3:
        return True
    return False


def location_to_node_id(label: str) -> Optional[str]:
    return NETWORK.get_node_id(label)


def serialize_managed(template: Optional[ManagedTemplate]) -> dict:
    if template is None:
        return {
            "movement_type": "none",
            "managed_passage_required": False,
            "contraflow_required": False,
            "uses_opposing_lane": False,
            "traffic_guidance_scheme_id": None,
            "traffic_guidance_scheme_name": None,
            "approval_required": False,
            "escort_required": False,
            "temporary_traffic_control_required": False,
            "intersection_control_required": False,
            "utility_intervention_required": False,
            "driver_departure_block": False,
            "driver_message": "",
            "dispatcher_message": "",
            "authority_actions_required": [],
        }
    return {
        "movement_type": template.movement_type.value,
        "managed_passage_required": True,
        "contraflow_required": template.reason_key == "contraflow_required",
        "uses_opposing_lane": template.uses_opposing_lane,
        "traffic_guidance_scheme_id": template.traffic_guidance_scheme_id,
        "traffic_guidance_scheme_name": template.traffic_guidance_scheme_name,
        "approval_required": template.approval_required,
        "escort_required": template.escort_required,
        "temporary_traffic_control_required": template.temporary_traffic_control_required,
        "intersection_control_required": template.intersection_control_required,
        "utility_intervention_required": template.utility_intervention_required,
        "driver_departure_block": template.approval_required,
        "driver_message": template.driver_message,
        "dispatcher_message": template.dispatcher_message,
        "authority_actions_required": [{"action_type": a.action_type.value, "responsible_party": a.responsible_party, "reference_id": a.reference_id, "status": "pending", "note": a.note} for a in template.actions],
    }


def calculate_route_plan(origin_label: str, destination_label: str, vehicle_dict: dict, preference: str = "balanced") -> dict | None:
    vehicle = build_vehicle(vehicle_dict)
    start_id = location_to_node_id(origin_label)
    end_id = location_to_node_id(destination_label)
    if start_id is None or end_id is None:
        raise ValueError("Unknown origin or destination")

    stages = []
    stage_results = []
    stage_number = 1

    if should_use_rtaa_reconfiguration(vehicle, origin_label):
        rtaa_label = default_rtaa_for_vehicle(vehicle)
        rtaa_id = location_to_node_id(rtaa_label or "")
        if rtaa_id and rtaa_id != end_id:
            res1 = ROUTER.calculate(start_id, rtaa_id, vehicle, preference)
            if res1.route_status == RouteStatus.no_workable_route:
                return None
            stage_results.append((stage_number, res1))
            stages.append({"stage_number": stage_number, "stage_type": "linehaul", "start_location_name": origin_label, "end_location_name": rtaa_label, "start_combination_type": vehicle.combination_type, "start_trailer_count": vehicle.trailer_count, "end_combination_type": vehicle.combination_type, "end_trailer_count": vehicle.trailer_count, "action_required": None, "action_status": "not_required", "notes": "Travel to RTAA using starting combination."})
            stage_number += 1
            stages.append({"stage_number": stage_number, "stage_type": "rtaa_reconfiguration", "start_location_name": rtaa_label, "end_location_name": rtaa_label, "start_combination_type": vehicle.combination_type, "start_trailer_count": vehicle.trailer_count, "end_combination_type": vehicle.target_combination_type or vehicle.combination_type, "end_trailer_count": vehicle.target_trailer_count or vehicle.trailer_count, "action_required": "attach_third_trailer" if (vehicle.target_trailer_count or vehicle.trailer_count) > vehicle.trailer_count else "detach_trailer", "action_status": "pending", "notes": "RTAA reconfiguration required before departure on next stage.", "payload": {"location_type": "rtaa", "location_name": rtaa_label, "driver_message": f"Reconfigure at {rtaa_label} before continuing.", "dispatcher_message": f"RTAA combination change planned at {rtaa_label}."}})
            stage_number += 1
            stage2_vehicle = Vehicle(vehicle.target_combination_type or vehicle.combination_type, vehicle.target_trailer_count or vehicle.trailer_count, vehicle.platform_type, vehicle.target_combination_type, vehicle.target_trailer_count, vehicle.route_direction, vehicle.requires_rtaa_reconfiguration, vehicle.rtaa_name, vehicle.height_m, vehicle.width_m, vehicle.length_m, vehicle.gross_mass_t, True if (vehicle.target_trailer_count or 0) >= 3 else vehicle.is_road_train, vehicle.is_oversize, vehicle.hazmat, vehicle.permits_held)
            res2 = ROUTER.calculate(rtaa_id, end_id, stage2_vehicle, preference)
            if res2.route_status == RouteStatus.no_workable_route:
                return None
            stage_results.append((stage_number, res2))
            stages.append({"stage_number": stage_number, "stage_type": "linehaul", "start_location_name": rtaa_label, "end_location_name": destination_label, "start_combination_type": stage2_vehicle.combination_type, "start_trailer_count": stage2_vehicle.trailer_count, "end_combination_type": stage2_vehicle.combination_type, "end_trailer_count": stage2_vehicle.trailer_count, "action_required": None, "action_status": "not_required", "notes": "Travel using post-RTAA combination."})
        else:
            res = ROUTER.calculate(start_id, end_id, vehicle, preference)
            if res.route_status == RouteStatus.no_workable_route:
                return None
            stage_results.append((stage_number, res))
            stages.append({"stage_number": stage_number, "stage_type": "linehaul", "start_location_name": origin_label, "end_location_name": destination_label, "start_combination_type": vehicle.combination_type, "start_trailer_count": vehicle.trailer_count, "end_combination_type": vehicle.combination_type, "end_trailer_count": vehicle.trailer_count, "action_required": None, "action_status": "not_required", "notes": "Direct route used."})
    else:
        res = ROUTER.calculate(start_id, end_id, vehicle, preference)
        if res.route_status == RouteStatus.no_workable_route:
            return None
        stage_results.append((stage_number, res))
        stages.append({"stage_number": stage_number, "stage_type": "linehaul", "start_location_name": origin_label, "end_location_name": destination_label, "start_combination_type": vehicle.combination_type, "start_trailer_count": vehicle.trailer_count, "end_combination_type": vehicle.combination_type, "end_trailer_count": vehicle.trailer_count, "action_required": None, "action_status": "not_required", "notes": "Direct route used."})

    all_edges = []
    all_briefings = []
    all_events = []
    managed_reasons = []
    total_distance = 0.0
    total_minutes = 0.0
    hazard_count = 0
    restriction_count = 0
    managed_segment_count = 0
    path_nodes = []

    for stage_no, res in stage_results:
        if not path_nodes:
            path_nodes.extend(res.path_nodes)
        else:
            path_nodes.extend(res.path_nodes[1:])
        total_distance += res.total_distance_km
        total_minutes += res.total_minutes
        hazard_count += res.hazard_count
        restriction_count += res.restriction_count
        managed_segment_count += res.managed_segment_count
        all_edges.extend([(stage_no, e) for e in res.path_edges])
        for x in res.briefings:
            x = dict(x)
            x["stage_number"] = stage_no
            all_briefings.append(x)
        for x in res.upcoming_events:
            x = dict(x)
            x["stage_number"] = stage_no
            all_events.append(x)
        for reason in res.managed_reasons:
            if reason not in managed_reasons:
                managed_reasons.append(reason)

    if any(s["stage_type"] == "rtaa_reconfiguration" for s in stages):
        all_briefings.append({"briefing_id": f"briefing_rtaa_{uuid.uuid4().hex[:8]}", "briefing_type": "managed_passage", "title": "RTAA reconfiguration required", "location_name": default_rtaa_for_vehicle(vehicle), "severity": "high", "departure_allowed": False, "driver_message": f"Reconfigure combination at {default_rtaa_for_vehicle(vehicle)} before continuing.", "dispatcher_actions": ["reconfigure_at_rtaa"], "reference_ids": [], "stage_number": 2})
        all_events.insert(0, {"event_id": f"evt_rtaa_{uuid.uuid4().hex[:8]}", "event_type": "managed_passage", "event_subtype": "rtaa_reconfiguration", "title": "RTAA reconfiguration ahead", "location_name": default_rtaa_for_vehicle(vehicle), "distance_to_event_km": stage_results[0][1].total_distance_km if stage_results else 0, "trigger_distances_km": [50, 10, 2], "requires_acknowledgement": True, "driver_message": f"RTAA reconfiguration required at {default_rtaa_for_vehicle(vehicle)}.", "dispatcher_message": f"Combination change planned at {default_rtaa_for_vehicle(vehicle)}.", "voice_message": "RTAA reconfiguration ahead", "repeat": True, "stage_number": 2})

    if managed_segment_count > 0 or any(s["stage_type"] == "rtaa_reconfiguration" for s in stages):
        route_status = RouteStatus.managed_passage_required
        legal_status = LegalStatus.requires_controlled_movement
        approval_status = ApprovalStatus.pending
        route_class = RouteClass.contraflow_required if "contraflow_required" in managed_reasons else RouteClass.managed_passage
    elif hazard_count > 0:
        route_status = RouteStatus.legal_with_hazards
        legal_status = LegalStatus.legal_with_conditions
        approval_status = ApprovalStatus.not_required
        route_class = {"balanced": RouteClass.best_legal, "fastest": RouteClass.fastest_compliant, "lowest_hazard": RouteClass.lowest_hazard}[preference]
    else:
        route_status = RouteStatus.clean_legal
        legal_status = LegalStatus.legal
        approval_status = ApprovalStatus.cleared
        route_class = {"balanced": RouteClass.best_legal, "fastest": RouteClass.fastest_compliant, "lowest_hazard": RouteClass.lowest_hazard}[preference]

    return {
        "route_id": f"route_{uuid.uuid4().hex[:8]}",
        "label": {"balanced": "Best legal route", "fastest": "Fastest compliant route", "lowest_hazard": "Lowest hazard route"}.get(preference, "Best legal route"),
        "route_status": route_status.value,
        "route_class": route_class.value,
        "legal_status": legal_status.value,
        "approval_status": approval_status.value,
        "managed_passage_required": route_status == RouteStatus.managed_passage_required,
        "managed_passage_reasons": managed_reasons,
        "summary": {"distance_km": round(total_distance, 1), "eta_minutes": round(total_minutes, 1), "travel_time_minutes": round(total_minutes, 1), "hazard_count": hazard_count, "restriction_count": restriction_count, "managed_segment_count": managed_segment_count + (1 if any(s["stage_type"] == "rtaa_reconfiguration" for s in stages) else 0), "fuel_confidence": "medium", "rest_confidence": "medium", "score": round(total_minutes + hazard_count * 8 + managed_segment_count * 40, 2), "recommended_label": {"balanced": "Best legal route", "fastest": "Fastest compliant route", "lowest_hazard": "Lowest hazard route"}.get(preference, "Best legal route")},
        "vehicle_combination": {"current_configuration": vehicle.combination_type, "current_trailer_count": vehicle.trailer_count, "target_configuration": vehicle.target_combination_type, "target_trailer_count": vehicle.target_trailer_count, "platform_type": vehicle.platform_type, "route_direction": vehicle.route_direction, "requires_reconfiguration": should_use_rtaa_reconfiguration(vehicle, origin_label)},
        "stages": stages,
        "segments": [{"segment_id": edge.edge_id, "sequence": i + 1, "stage_number": stage_no, "road_name": edge.road_name, "direction_of_travel": "northbound", "location_name": edge.location_name, "local_roads_in_scope": list(edge.local_roads_in_scope), "start_landmark": edge.start_landmark, "end_landmark": edge.end_landmark, "distance_km": edge.distance_km, "estimated_travel_time_minutes": edge.travel_minutes, "geometry_ref": edge.edge_id, "static_restrictions": [], "live_hazards": [{"hazard_id": hz.hazard_id, "category": hz.category, "severity": hz.severity.value, "status": "active", "message": hz.message, "reported_at": hz.reported_at.isoformat(), "source": hz.source, "confidence_score": hz.confidence_score, "delay_minutes": hz.delay_minutes, "show_to_driver": True, "comments_count": 0} for hz in edge.hazards], "managed_movement": serialize_managed(ROUTER._evaluate_edge(edge, vehicle).managed_template), "trigger_rules": {"route_must_include_all": list(edge.local_roads_in_scope), "permit_required": edge.restrictions.permit_required, "vehicle_width_m_gt": edge.restrictions.managed_if_width_gt_m, "vehicle_height_m_gt": edge.restrictions.managed_if_height_gt_m, "gross_mass_t_gt": edge.restrictions.managed_if_mass_gt_t}, "hazard_visibility": {"show_to_driver": True, "show_to_dispatcher": True, "show_in_pre_departure_briefing": True, "show_in_live_alerts": True}} for i, (stage_no, edge) in enumerate(all_edges)],
        "pre_departure_briefing": all_briefings,
        "upcoming_events": all_events,
        "path_nodes": path_nodes,
        "generated_at": datetime.utcnow().isoformat(),
    }


def demo_locations() -> list[str]:
    return sorted(node.label for node in NETWORK.nodes.values())
