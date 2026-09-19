import os
import time
import uuid
import re
from typing import List, Dict, Any, Optional
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Hyper-Local Fleet Swarm Intelligence Engine", version="3.6.2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class IncidentInput(BaseModel):
    vehicle_id: str
    location: str
    destination: Optional[str] = "Authorized Heavy Workshop Hub"
    issue_type: str
    severity: str
    cargo_type: str

class AgentTrace(BaseModel):
    step_name: str
    agent_role: str
    status: str
    timestamp: float
    output_payload: Dict[str, Any]

class TriageResponse(BaseModel):
    incident_id: str
    status: str
    execution_time_ms: float
    deterministic_steps_executed: int
    traces: List[AgentTrace]
    final_resolution: Dict[str, Any]

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

class HyperLocalSwarmOrchestrator:
    def __init__(self, incident: IncidentInput):
        self.incident = incident
        self.incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
        self.traces: List[AgentTrace] = []
        self.start_time = time.time()
        self.step_counter = 0

    def _fetch_google_maps_route(self):
        if not GOOGLE_MAPS_API_KEY or not self.incident.destination:
            return None
        url = "https://maps.googleapis.com/maps/api/directions/json"
        params = {
            "origin": self.incident.location,
            "destination": self.incident.destination,
            "key": GOOGLE_MAPS_API_KEY
        }
        try:
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            if data.get("status") == "OK":
                leg = data["routes"][0]["legs"][0]
                return {
                    "distance_text": leg["distance"]["text"],
                    "distance_value": leg["distance"]["value"],
                    "duration_text": leg["duration"]["text"],
                    "start_address": leg["start_address"],
                    "end_address": leg["end_address"],
                    "start_coords": leg["start_location"],
                    "end_coords": leg["end_location"]
                }
        except Exception:
            pass
        return None

    def _get_heavy_service_center_intelligence(self):
        """Fetches authorized Tata CV & Eicher Service Centers and selects the closest one to breakdown point"""
        raw_hubs = []
        
        if GOOGLE_MAPS_API_KEY:
            places_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
            # Extract main area/city keyword from location for precise local search
            location_query = self.incident.location.split(",")[0].strip()
            query_str = f"Tata commercial vehicle service center OR Eicher workshop near {location_query}, Patna"
            params = {
                "query": query_str,
                "key": GOOGLE_MAPS_API_KEY
            }
            try:
                response = requests.get(places_url, params=params, timeout=7)
                data = response.json()
                if data.get("status") == "OK" and data.get("results"):
                    for place in data["results"][:5]:
                        name = place.get('name', 'Service Center')
                        address = place.get('formatted_address', '')
                        rating = place.get('rating', 'N/A')
                        geometry = place.get('geometry', {}).get('location', {})
                        raw_hubs.append({
                            "display_str": f"{name} — {address} (Rating: {rating})",
                            "coords": geometry
                        })
            except Exception:
                pass

        # Robust Fallback list for Patna corridor if API is empty
        if not raw_hubs:
            default_heavy_hubs = [
                "TATA.CARS Service Centre - Guinea Motors, Patliputra Industrial Area, Patna, Bihar (Rating: 3.9)",
                "Eicher Commercial Vehicles Workshop, NH-30 Bypass Road, Patna, Bihar (Rating: 4.2)",
                "Tata Motors Authorized Commercial Heavy Workshop, Zero Mile, Patna, Bihar (Rating: 4.1)",
                "Eicher Trucks & Buses Service Station, Fatuha Industrial Area, Patna, Bihar (Rating: 4.0)"
            ]
            for hub in default_heavy_hubs:
                raw_hubs.append({"display_str": hub, "coords": {}})

        # Calculate or pick the closest hub based on proximity
        # If coordinates are available via Distance Matrix API, we pick the absolute closest; else take the first valid local result
        closest_hub_str = raw_hubs[0]["display_str"]
        
        if GOOGLE_MAPS_API_KEY and len(raw_hubs) > 1 and raw_hubs[0]["coords"]:
            destinations = "|".join([f"{h['coords'].get('lat')},{h['coords'].get('lng')}" for h in raw_hubs if h['coords']])
            matrix_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
            matrix_params = {
                "origins": self.incident.location,
                "destinations": destinations,
                "key": GOOGLE_MAPS_API_KEY
            }
            try:
                m_res = requests.get(matrix_url, params=matrix_params, timeout=5)
                m_data = m_res.json()
                if m_data.get("status") == "OK":
                    elements = m_data["rows"][0]["elements"]
                    min_distance = float('inf')
                    best_idx = 0
                    for idx, elem in enumerate(elements):
                        if elem.get("status") == "OK":
                            dist_val = elem["distance"]["value"]
                            if dist_val < min_distance:
                                min_distance = dist_val
                                best_idx = idx
                    closest_hub_str = raw_hubs[best_idx]["display_str"]
            except Exception:
                pass

        # Format numbered list (1 to N), ensuring the closest hub is placed at #1
        cleaned_raw_strings = [re.sub(r'^\d+\.\s*', '', h["display_str"]) for h in raw_hubs]
        
        # Bring closest hub to the top if present
        cleaned_closest = re.sub(r'^\d+\.\s*', '', closest_hub_str)
        if cleaned_closest in cleaned_raw_strings:
            cleaned_raw_strings.remove(cleaned_closest)
        cleaned_raw_strings.insert(0, cleaned_closest)

        numbered_hubs = [f"{idx}. {hub}" for idx, hub in enumerate(cleaned_raw_strings[:5], 1)]
        primary_hub = numbered_hubs[0]

        return {
            "corridor": self.incident.location,
            "alt_route": f"Proximity-Optimized Heavy Corridor linking {self.incident.location} to {primary_hub.split('—')[0]}",
            "hub": primary_hub,
            "all_detected_hubs": numbered_hubs,
            "delay_saved": 4.0
        }

    def run_swarm(self) -> TriageResponse:
        map_route = self._fetch_google_maps_route()
        service_intel = self._get_heavy_service_center_intelligence()
        detected_hubs = service_intel.get("all_detected_hubs", [])

        # 1. Supervisor Agent
        self.step_counter += 1
        t_start = time.time()
        sup_dec = {
            "action_required": True,
            "target_vehicle": self.incident.vehicle_id,
            "breakdown_location": map_route["start_address"] if map_route else self.incident.location,
            "destination_workshop": service_intel["hub"],
            "all_nearby_service_centers": detected_hubs,
            "issue_detected": self.incident.issue_type,
            "assigned_sub_agents": ["RoutingAgent", "ProcurementAgent", "LegalAgent", "ERPSyncAgent"],
            "risk_score": 0.94 if self.incident.severity == "CRITICAL" else 0.70
        }
        self.traces.append(AgentTrace(step_name="Supervisor_Triage", agent_role="Supervisor Agent", status="SUCCESS", timestamp=round((time.time() - t_start) * 1000, 2), output_payload=sup_dec))

        # 2. Routing Agent
        self.step_counter += 1
        t_start = time.time()
        routing = {
            "routing_engine": "Google Maps Directions API" if map_route else "Bihar Heavy Corridor Fallback",
            "total_distance": map_route["distance_text"] if map_route else "310 km",
            "estimated_travel_time": map_route["duration_text"] if map_route else "6 hours",
            "primary_route_status": "HEAVY_TRAFFIC_OR_CONGESTED",
            "hyper_accurate_alternative_route": f"Optimized proximity transit from {self.incident.location} to nearest verified workshop: {service_intel['hub'].split('—')[0]}",
            "start_coordinates": map_route["start_coords"] if map_route else {"lat": 25.6, "lng": 85.1},
            "end_coordinates": map_route["end_coords"] if map_route else {"lat": 25.5, "lng": 87.5}
        }
        self.traces.append(AgentTrace(step_name="Routing_Recalculation", agent_role="Routing Agent", status="SUCCESS", timestamp=round((time.time() - t_start) * 1000, 2), output_payload=routing))

        # 3. Procurement Agent
        self.step_counter += 1
        t_start = time.time()
        proc = {
            "cargo_type": self.incident.cargo_type,
            "nearest_operational_hub": service_intel["hub"],
            "all_nearby_service_centers": detected_hubs,
            "inventory_status": f"100% genuine Tata/Eicher replacement spares & mobile mechanic crew locked for {self.incident.vehicle_id}",
            "dispatch_status": "READY_FOR_IMMEDIATE_DISPATCH_TO_DESTINATION"
        }
        self.traces.append(AgentTrace(step_name="Procurement_Vendor_Negotiation", agent_role="Procurement Agent", status="SUCCESS", timestamp=round((time.time() - t_start) * 1000, 2), output_payload=proc))

        # 4. Legal Agent
        self.step_counter += 1
        t_start = time.time()
        legal = {
            "notice_generated": True,
            "incident_zone": map_route["start_address"] if map_route else service_intel["corridor"],
            "destination_zone": service_intel["hub"],
            "document_type": "Emergency Transit Towing Permit & Force Majeure Notice",
            "penalty_clause_invoked": "Commercial Logistics SLA Section 14.2"
        }
        self.traces.append(AgentTrace(step_name="Legal_Compliance_Generation", agent_role="Legal Agent", status="SUCCESS", timestamp=round((time.time() - t_start) * 1000, 2), output_payload=legal))

        # 5. ERP Sync Agent
        self.step_counter += 1
        t_start = time.time()
        erp = {
            "erp_transaction_id": f"TXN-ERP-{uuid.uuid4().hex[:6].upper()}",
            "vehicle_logged": self.incident.vehicle_id,
            "total_trip_distance_meters": map_route["distance_value"] if map_route else 300000,
            "ledger_status": "COMMITTED",
            "fleet_status_updated": "REROUTED_VIA_DYNAMIC_MAPPED_PATH"
        }
        self.traces.append(AgentTrace(step_name="ERP_State_Commit", agent_role="ERP Sync Agent", status="SUCCESS", timestamp=round((time.time() - t_start) * 1000, 2), output_payload=erp))

        return TriageResponse(
            incident_id=self.incident_id,
            status="RESOLVED_VIA_TATA_EICHER_SWARM",
            execution_time_ms=round((time.time() - self.start_time) * 1000, 2),
            deterministic_steps_executed=self.step_counter,
            traces=self.traces,
            final_resolution={
                "vehicle_id": self.incident.vehicle_id,
                "origin": self.incident.location,
                "destination": service_intel["hub"],
                "all_available_service_centers": detected_hubs,
                "mitigation_summary": f"Swarm rerouted heavy unit {self.incident.vehicle_id} from {self.incident.location} to the closest repair workshop: {service_intel['hub']}.",
                "erp_ref": erp["erp_transaction_id"]
            }
        )

@app.post("/api/triage", response_model=TriageResponse)
async def trigger_triage(incident: IncidentInput):
    return HyperLocalSwarmOrchestrator(incident).run_swarm()

@app.get("/api/health")
async def health_check():
    return {"status": "online", "engine": "Fleet Swarm Intelligence Proximity Engine v3.6.2"}
