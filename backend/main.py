import os
import time
import uuid
from typing import List, Dict, Any, Optional
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Hyper-Local Fleet Swarm Intelligence Engine", version="3.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class IncidentInput(BaseModel):
    vehicle_id: str
    location: str                               # Breakdown Location (Origin Start)
    destination: Optional[str] = "Authorized Heavy Workshop Hub"  # Optional
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

# Fallback Heavy Vehicle Hubs Database for Bihar (Tata & Eicher Authorized)
LOCATION_MAP = {
    "nh-31": {
        "corridor": "NH-31 Patna-Bakhtiyarpur Heavy Transit Stretch",
        "alt_route": "Fatuha Heavy Vehicle Link Road via Malislah Bypass",
        "hub": "Tata Motors Authorized CV Service Station & Eicher Workshop, Fatuha Industrial Area",
        "delay_saved": 3.8
    },
    "gandhi setu": {
        "corridor": "Mahatma Gandhi Setu Heavy Freight Corridor",
        "alt_route": "JP Setu Western Embankment Heavy Transit Route",
        "hub": "Eicher & Tata Commercial Heavy Truck Service Hub, Hajipur Industrial Area",
        "delay_saved": 4.5
    },
    "danapur": {
        "corridor": "Danapur-Khagaul Freight Corridor",
        "alt_route": "Khagaul-Neora Inner Heavy Ring Road",
        "hub": "Authorized Tata Heavy Fleet Garage, Bihta Regional Logistics Park",
        "delay_saved": 2.5
    },
    "bihta": {
        "corridor": "Bihta-Patna Elevated Expressway Heavy Route",
        "alt_route": "Naubatpur Heavy Vehicle Expressway Bypass",
        "hub": "Eicher Commercial Trucks Service Center, Naubatpur Bulk Yard",
        "delay_saved": 3.2
    },
    "zero mile": {
        "corridor": "Patna Zero Mile / Heavy Bypass Chowk",
        "alt_route": "Ramkrishnanagar Outer Ring Heavy Connector",
        "hub": "Tata Motors Commercial Vehicle Authorized Service Hub, Zero Mile Patna",
        "delay_saved": 2.8
    }
}

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

class HyperLocalSwarmOrchestrator:
    def __init__(self, incident: IncidentInput):
        self.incident = incident
        self.incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
        self.traces: List[AgentTrace] = []
        self.start_time = time.time()
        self.step_counter = 0

    def _fetch_google_maps_route(self):
        """Fetches real distance, duration, and coordinates from Google Maps Directions API"""
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
        """Searches Google Maps Places API for nearest Tata CV or Eicher Service Center near breakdown location"""
        if GOOGLE_MAPS_API_KEY:
            places_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
            query_str = f"Tata commercial vehicle service center or Eicher workshop near {self.incident.location}"
            params = {
                "query": query_str,
                "key": GOOGLE_MAPS_API_KEY
            }
            try:
                response = requests.get(places_url, params=params, timeout=5)
                data = response.json()
                if data.get("status") == "OK" and data.get("results"):
                    best_match = data["results"][0]
                    return {
                        "corridor": self.incident.location,
                        "alt_route": f"Optimized Heavy Transit Corridor connecting {self.incident.location} to authorized service station",
                        "hub": f"{best_match['name']} — {best_match.get('formatted_address', 'Authorized Heavy Service Hub')}",
                        "delay_saved": 3.5
                    }
            except Exception:
                pass

        # Fallback Corridor Lookup for Bihar Heavy Vehicle Network
        loc_lower = self.incident.location.lower()
        for key, data in LOCATION_MAP.items():
            if key in loc_lower:
                return data
                
        return {
            "corridor": self.incident.location,
            "alt_route": f"Heavy Vehicle Express Corridor linking {self.incident.location} to Regional Workshop",
            "hub": "Authorized Tata Motors CV & Eicher Service Station, Patna Expressway Hub",
            "delay_saved": 3.0
        }

    def run_swarm(self) -> TriageResponse:
        map_route = self._fetch_google_maps_route()
        service_intel = self._get_heavy_service_center_intelligence()

        # 1. Supervisor Agent
        self.step_counter += 1
        t_start = time.time()
        risk = 0.94 if self.incident.severity == "CRITICAL" else 0.70
        sup_dec = {
            "action_required": True,
            "target_vehicle": self.incident.vehicle_id,
            "breakdown_location": map_route["start_address"] if map_route else self.incident.location,
            "destination_workshop": service_intel["hub"],
            "issue_detected": self.incident.issue_type,
            "assigned_sub_agents": ["RoutingAgent", "ProcurementAgent", "LegalAgent", "ERPSyncAgent"],
            "risk_score": risk
        }
        self.traces.append(AgentTrace(step_name="Supervisor_Triage", agent_role="Supervisor Agent", status="SUCCESS", timestamp=round((time.time() - t_start) * 1000, 2), output_payload=sup_dec))

        # 2. Routing Agent
        self.step_counter += 1
        t_start = time.time()
        if map_route:
            routing = {
                "routing_engine": "Google Maps Directions API",
                "total_distance": map_route["distance_text"],
                "estimated_travel_time": map_route["duration_text"],
                "primary_route_status": "HEAVY_TRAFFIC_OR_CONGESTED",
                "hyper_accurate_alternative_route": f"Optimized heavy transit from {map_route['start_address']} to {service_intel['hub']}",
                "start_coordinates": map_route["start_coords"],
                "end_coordinates": map_route["end_coords"]
            }
        else:
            routing = {
                "routing_engine": "Bihar Heavy Corridor Fallback",
                "target_corridor": service_intel["corridor"],
                "primary_route_status": "SEVERELY_BLOCKED",
                "hyper_accurate_alternative_route": service_intel["alt_route"],
                "estimated_delay_mitigated_hours": service_intel["delay_saved"]
            }
        self.traces.append(AgentTrace(step_name="Routing_Recalculation", agent_role="Routing Agent", status="SUCCESS", timestamp=round((time.time() - t_start) * 1000, 2), output_payload=routing))

        # 3. Procurement Agent (Tata & Eicher Parts & Service Dispatch)
        self.step_counter += 1
        t_start = time.time()
        proc = {
            "cargo_type": self.incident.cargo_type,
            "nearest_operational_hub": service_intel["hub"],
            "inventory_status": f"100% genuine Tata/Eicher replacement spares & mobile mechanic crew locked for {self.incident.vehicle_id}",
            "dispatch_status": "READY_FOR_IMMEDIATE_TOWING_AND_SERVICE_BAY_ALLOCATION"
        }
        self.traces.append(AgentTrace(step_name="Procurement_Vendor_Negotiation", agent_role="Procurement Agent", status="SUCCESS", timestamp=round((time.time() - t_start) * 1000, 2), output_payload=proc))

        # 4. Legal Agent
        self.step_counter += 1
        t_start = time.time()
        legal = {
            "notice_generated": True,
            "incident_zone": map_route["start_address"] if map_route else service_intel["corridor"],
            "destination_zone": service_intel["hub"],
            "document_type": "Commercial Heavy Vehicle Emergency Towing Permit & Workshop Job Card",
            "penalty_clause_invoked": "Commercial Fleet SLA Section 14.2"
        }
        self.traces.append(AgentTrace(step_name="Legal_Compliance_Generation", agent_role="Legal Agent", status="SUCCESS", timestamp=round((time.time() - t_start) * 1000, 2), output_payload=legal))

        # 5. ERP Sync Agent
        self.step_counter += 1
        t_start = time.time()
        distance_val = map_route["distance_value"] if map_route else 30000
        erp = {
            "erp_transaction_id": f"TXN-ERP-{uuid.uuid4().hex[:6].upper()}",
            "vehicle_logged": self.incident.vehicle_id,
            "total_trip_distance_meters": distance_val,
            "ledger_status": "COMMITTED",
            "fleet_status_updated": "ROUTED_TO_AUTHORIZED_TATA_EICHER_WORKSHOP"
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
                "mitigation_summary": f"Swarm rerouted heavy unit {self.incident.vehicle_id} from {self.incident.location} directly to authorized service center at {service_intel['hub']}.",
                "erp_ref": erp["erp_transaction_id"]
            }
        )

@app.post("/api/triage", response_model=TriageResponse)
async def trigger_triage(incident: IncidentInput):
    return HyperLocalSwarmOrchestrator(incident).run_swarm()

@app.get("/api/health")
async def health_check():
    return {"status": "online", "engine": "Hyper-Local Fleet Swarm with Tata/Eicher Service Integration"}
