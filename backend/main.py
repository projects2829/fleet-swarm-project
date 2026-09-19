import os
import time
import uuid
import re
from typing import List, Dict, Any, Optional
import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Hyper-Local Fleet Swarm Intelligence Engine", version="3.8.2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Fleet Unit ID to WhatsApp Number mapping dictionary
FLEET_WHATSAPP_MAPPING = {
    "BR01GP9621": "+916209313108",
    "BR01GM7465": "+916209313108",
    "BR01GP0756": "+916209313108",
    "BR01GP0757": "+916209313108",
    "BR01GP8148": "+916209313108"
}

# In-memory storage to track approval states for WhatsApp webhook sync
APPROVAL_STATES = {}

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("PHONE_NUMBER_ID", "1340284595815318")

# Meta Webhook Verify Token
VERIFY_TOKEN = "fleet_secret_token_2026"

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
    assigned_whatsapp_number: str
    approval_status: str
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
        raw_hubs = []
        if GOOGLE_MAPS_API_KEY:
            places_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
            location_query = self.incident.location.split(",")[0].strip()
            query_str = f"Tata commercial vehicle service center OR Eicher workshop near {location_query}, Patna"
            params = {"query": query_str, "key": GOOGLE_MAPS_API_KEY}
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

        if not raw_hubs:
            default_heavy_hubs = [
                "TATA.CARS Service Centre - Guinea Motors, Patliputra Industrial Area, Patna, Bihar (Rating: 3.9)",
                "Eicher Commercial Vehicles Workshop, NH-30 Bypass Road, Patna, Bihar (Rating: 4.2)",
                "Tata Motors Authorized Commercial Heavy Workshop, Zero Mile, Patna, Bihar (Rating: 4.1)",
                "Eicher Trucks & Buses Service Station, Fatuha Industrial Area, Patna, Bihar (Rating: 4.0)"
            ]
            for hub in default_heavy_hubs:
                raw_hubs.append({"display_str": hub, "coords": {}})

        closest_hub_str = raw_hubs[0]["display_str"]
        if GOOGLE_MAPS_API_KEY and len(raw_hubs) > 1 and raw_hubs[0]["coords"]:
            destinations = "|".join([f"{h['coords'].get('lat')},{h['coords'].get('lng')}" for h in raw_hubs if h['coords']])
            matrix_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
            matrix_params = {"origins": self.incident.location, "destinations": destinations, "key": GOOGLE_MAPS_API_KEY}
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

        cleaned_raw_strings = [re.sub(r'^\d+\.\s*', '', h["display_str"]) for h in raw_hubs]
        cleaned_closest = re.sub(r'^\d+\.\s*', '', closest_hub_str)
        if cleaned_closest in cleaned_raw_strings:
            cleaned_raw_strings.remove(cleaned_closest)
        cleaned_raw_strings.insert(0, cleaned_closest)

        numbered_hubs = [f"{idx}. {hub}" for idx, hub in enumerate(cleaned_raw_strings[:5], 1)]
        primary_hub = numbered_hubs[0]

        return {
            "corridor": self.incident.location,
            "hub": primary_hub,
            "all_detected_hubs": numbered_hubs
        }

    def run_swarm(self) -> TriageResponse:
        map_route = self._fetch_google_maps_route()
        service_intel = self._get_heavy_service_center_intelligence()
        detected_hubs = service_intel.get("all_detected_hubs", [])

        clean_vid = self.incident.vehicle_id.strip().upper()
        assigned_phone = FLEET_WHATSAPP_MAPPING.get(clean_vid, "+916209313108")

        APPROVAL_STATES[self.incident_id] = "PENDING_MANAGER_APPROVAL"

        # 1. Supervisor Agent
        self.step_counter += 1
        t_start = time.time()
        sup_dec = {
            "action_required": True,
            "target_vehicle": self.incident.vehicle_id,
            "mapped_whatsapp_number": assigned_phone,
            "breakdown_location": map_route["start_address"] if map_route else self.incident.location,
            "destination_workshop": service_intel["hub"],
            "all_nearby_service_centers": detected_hubs,
            "issue_detected": self.incident.issue_type,
            "hitl_status": "WAITING_FOR_WHATSAPP_INTERACTIVE_BUTTON"
        }
        self.traces.append(AgentTrace(step_name="Supervisor_Triage", agent_role="Supervisor Agent", status="SUCCESS", timestamp=round((time.time() - t_start) * 1000, 2), output_payload=sup_dec))

        # 2. Routing Agent
        self.step_counter += 1
        t_start = time.time()
        routing = {
            "total_distance": map_route["distance_text"] if map_route else "310 km",
            "estimated_travel_time": map_route["duration_text"] if map_route else "6 hours",
            "primary_route_status": "HEAVY_CORRIDOR_OPTIMIZED",
            "hyper_accurate_alternative_route": f"Optimized transit to {service_intel['hub'].split('—')[0]}"
        }
        self.traces.append(AgentTrace(step_name="Routing_Recalculation", agent_role="Routing Agent", status="SUCCESS", timestamp=round((time.time() - t_start) * 1000, 2), output_payload=routing))

        # 3. ERP Sync Agent
        self.step_counter += 1
        t_start = time.time()
        erp = {
            "erp_transaction_id": f"TXN-ERP-{uuid.uuid4().hex[:6].upper()}",
            "ledger_status": "PENDING_HITL_APPROVAL"
        }
        self.traces.append(AgentTrace(step_name="ERP_State_Commit", agent_role="ERP Sync Agent", status="SUCCESS", timestamp=round((time.time() - t_start) * 1000, 2), output_payload=erp))

        return TriageResponse(
            incident_id=self.incident_id,
            status="AWAITING_HITL_APPROVAL",
            execution_time_ms=round((time.time() - self.start_time) * 1000, 2),
            deterministic_steps_executed=self.step_counter,
            assigned_whatsapp_number=assigned_phone,
            approval_status=APPROVAL_STATES[self.incident_id],
            traces=self.traces,
            final_resolution={
                "vehicle_id": self.incident.vehicle_id,
                "assigned_whatsapp": assigned_phone,
                "origin": self.incident.location,
                "primary_nearest_hub": service_intel["hub"],
                "all_available_service_centers": detected_hubs,
                "mitigation_summary": f"Incident logged for {self.incident.vehicle_id}. Waiting for Operations Manager WhatsApp Interactive Approval.",
                "erp_ref": erp["erp_transaction_id"]
            }
        )

@app.post("/api/triage", response_model=TriageResponse)
async def trigger_triage(incident: IncidentInput):
    return HyperLocalSwarmOrchestrator(incident).run_swarm()

# 🔍 NEW: Live Approval Status Polling Endpoint for Frontend
@app.get("/api/approval-status/{incident_id}")
async def get_approval_status(incident_id: str):
    current_status = APPROVAL_STATES.get(incident_id, "PENDING_MANAGER_APPROVAL")
    return {
        "incident_id": incident_id,
        "approval_status": current_status
    }

# Endpoint to trigger WhatsApp Interactive Buttons via Meta Cloud API
@app.post("/api/send-whatsapp-interactive")
async def send_whatsapp_interactive(payload: dict):
    incident_id = payload.get("incident_id")
    raw_phone = payload.get("phone", "")
    vehicle_id = payload.get("vehicle_id")
    hub = payload.get("hub")

    cleaned_phone = re.sub(r'\D', '', raw_phone)

    token = os.getenv("WHATSAPP_TOKEN")
    phone_id = os.getenv("PHONE_NUMBER_ID", "1340284595815318")

    if token and token != "YOUR_TOKEN":
        url = f"https://graph.facebook.com/v26.0/{phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        body = {
            "messaging_product": "whatsapp",
            "to": cleaned_phone,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": f"🚨 *HITL APPROVAL REQUEST* \nVehicle: *{vehicle_id}*\nNearest Hub:\n{hub}\n\nAuthorize immediate repair & dispatch?"
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": f"APPROVE_{incident_id}",
                                "title": "Approve Repair ✅"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": f"REJECT_{incident_id}",
                                "title": "Reject & Reroute ❌"
                            }
                        }
                    ]
                }
            }
        }
        res = requests.post(url, json=body, headers=headers)
        
        if res.status_code != 200:
            return {
                "status": "meta_api_error",
                "status_code": res.status_code,
                "error_details": res.json()
            }
        
        return {"status": "dispatched_via_meta_api", "response": res.json()}
    
    return {
        "status": "simulated_interactive_dispatched",
        "message": f"WhatsApp interactive buttons sent successfully to {cleaned_phone} for incident {incident_id}."
    }

# ==========================================
# WHATSAPP WEBHOOK VERIFICATION (GET)
# ==========================================
@app.get("/api/whatsapp-webhook")
async def verify_whatsapp_webhook(request: Request):
    hub_mode = request.query_params.get("hub.mode")
    hub_challenge = request.query_params.get("hub.challenge")
    hub_verify_token = request.query_params.get("hub.verify_token")
    
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)
    
    raise HTTPException(status_code=403, detail="Verification token mismatch")

# ==========================================
# INCOMING BUTTON CLICK HANDLER (POST)
# ==========================================
@app.post("/api/whatsapp-webhook")
async def whatsapp_webhook(request: Request):
    try:
        data = await request.json()
        entry = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if messages:
            msg = messages[0]
            if msg.get("type") == "interactive":
                button_reply = msg["interactive"].get("button_reply", {})
                payload_id = button_reply.get("id", "")
                
                if "APPROVE_" in payload_id:
                    inc_id = payload_id.split("APPROVE_")[1]
                    APPROVAL_STATES[inc_id] = "APPROVED_AND_DISPATCHED"
                    return {"status": "success", "action": "ERP state committed, mechanic dispatched."}
                elif "REJECT_" in payload_id:
                    inc_id = payload_id.split("REJECT_")[1]
                    APPROVAL_STATES[inc_id] = "REJECTED_REROUTING"
                    return {"status": "success", "action": "Rerouting triggered."}
    except Exception as e:
        return {"status": "error", "details": str(e)}

    return {"status": "received"}

@app.get("/api/health")
async def health_check():
    return {"status": "online", "engine": "HITL Swarm Orchestrator v3.8.2"}
