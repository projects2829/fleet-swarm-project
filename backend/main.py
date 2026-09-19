import os
import time
import uuid
import re
from typing import List, Dict, Any, Optional
import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Autonomous Enterprise Fleet Agentic AI & RAG Engine", version="4.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Fleet Unit ID to WhatsApp Number mapping
FLEET_WHATSAPP_MAPPING = {
    "BR01GP9621": "+916209313108",
    "BR01GM7465": "+916209313108",
    "BR01GP0756": "+916209313108",
    "BR01GP0757": "+916209313108",
    "BR01GP8148": "+916209313108"
}

# In-memory storage for HITL approval states and active contexts
APPROVAL_STATES = {}
INCIDENT_CONTEXTS = {}

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("PHONE_NUMBER_ID", "1340284595815318")
VERIFY_TOKEN = "fleet_secret_token_2026"
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

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


class EnterpriseAgenticRAGOrchestrator:
    def __init__(self, incident: IncidentInput):
        self.incident = incident
        self.incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
        self.traces: List[AgentTrace] = []
        self.start_time = time.time()
        self.step_counter = 0

    def _run_agentic_rag_diagnostics(self):
        """
        Simulated Enterprise Agentic RAG Pipeline that queries heavy commercial 
        vehicle diagnostic vectors for exact parts and repair directives.
        """
        issue = self.incident.issue_type.lower()
        if "overheat" in issue or "temperature" in issue:
            return {
                "vector_match_score": 0.94,
                "referenced_manual": "Tata Prima / Signa Heavy Commercial Maintenance Manual v4.2",
                "diagnostic_summary": "Radiator core choke or thermostat valve blockage detected.",
                "recommended_part": "Heavy Duty Coolant Pump & Thermostat Assembly (Part #TATA-9942-OH)",
                "estimated_repair_time_hours": 3.5
            }
        elif "transmission" in issue or "gear" in issue:
            return {
                "vector_match_score": 0.91,
                "referenced_manual": "Eicher Pro Series Heavy Duty Transmission Guide",
                "diagnostic_summary": "Hydraulic clutch booster pressure drop or gear actuator slip.",
                "recommended_part": "Eicher Heavy Transmission Actuator Seal Kit (Part #EIC-8812-TR)",
                "estimated_repair_time_hours": 5.0
            }
        else:
            return {
                "vector_match_score": 0.88,
                "referenced_manual": "General Commercial Fleet Telemetry & Fault Guide",
                "diagnostic_summary": "Standard electrical harness or fuel line pressure fluctuation.",
                "recommended_part": "Universal Heavy Fleet Fuel Filter & Sensor Kit (Part #FL-GEN-01)",
                "estimated_repair_time_hours": 2.0
            }

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
                    "end_address": leg["end_address"]
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
        rag_intel = self.run_agentic_rag_diagnostics()
        detected_hubs = service_intel.get("all_detected_hubs", [])

        clean_vid = self.incident.vehicle_id.strip().upper()
        assigned_phone = FLEET_WHATSAPP_MAPPING.get(clean_vid, "+916209313108")

        APPROVAL_STATES[self.incident_id] = "PENDING_MANAGER_APPROVAL"
        INCIDENT_CONTEXTS[assigned_phone] = self.incident_id

        # 1. Supervisor Agent Trace
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
            "hitl_status": "WAITING_FOR_WHATSAPP_INTERACTIVE_BUTTON_OR_TEXT"
        }
        self.traces.append(AgentTrace(step_name="Supervisor_Triage", agent_role="Supervisor Agent", status="SUCCESS", timestamp=round((time.time() - t_start) * 1000, 2), output_payload=sup_dec))

        # 2. Agentic RAG Diagnostic Agent Trace
        self.step_counter += 1
        t_start = time.time()
        self.traces.append(AgentTrace(step_name="Agentic_RAG_Diagnostics", agent_role="Vector RAG Diagnostic Agent", status="SUCCESS", timestamp=round((time.time() - t_start) * 1000, 2), output_payload=rag_intel))

        # 3. Routing Agent Trace
        self.step_counter += 1
        t_start = time.time()
        routing = {
            "total_distance": map_route["distance_text"] if map_route else "310 km",
            "estimated_travel_time": map_route["duration_text"] if map_route else "6 hours",
            "primary_route_status": "HEAVY_CORRIDOR_OPTIMIZED",
            "hyper_accurate_alternative_route": f"Optimized transit to {service_intel['hub'].split('—')[0]}"
        }
        self.traces.append(AgentTrace(step_name="Routing_Recalculation", agent_role="Routing Agent", status="SUCCESS", timestamp=round((time.time() - t_start) * 1000, 2), output_payload=routing))

        # 4. ERP Sync Agent Trace
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
                "rag_diagnostic_part": rag_intel["recommended_part"],
                "mitigation_summary": f"Incident logged with Agentic RAG Part Match. Waiting for Manager WhatsApp response.",
                "erp_ref": erp["erp_transaction_id"]
            }
        )

@app.post("/api/triage", response_model=TriageResponse)
async def trigger_triage(incident: IncidentInput):
    return EnterpriseAgenticRAGOrchestrator(incident).run_swarm()

@app.get("/api/approval-status/{incident_id}")
async def get_approval_status(incident_id: str):
    current_status = APPROVAL_STATES.get(incident_id, "PENDING_MANAGER_APPROVAL")
    return {
        "incident_id": incident_id,
        "approval_status": current_status
    }

@app.post("/api/send-whatsapp-interactive")
async def send_whatsapp_interactive(payload: dict):
    incident_id = payload.get("incident_id")
    raw_phone = payload.get("phone", "")
    vehicle_id = payload.get("vehicle_id")
    hub = payload.get("hub")
    
    location = payload.get("location", "N/A")
    issue_type = payload.get("issue_type", "N/A")
    severity = payload.get("severity", "N/A")
    cargo_type = payload.get("cargo_type", "N/A")
    recommended_part = payload.get("recommended_part", "Standard Spare Kit")

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
                    "text": (
                        f"🚨 *AGENTIC RAG FLEET ALERT*\n\n"
                        f"🚜 *Vehicle:* {vehicle_id} | ⚡ *Sev:* {severity}\n"
                        f"📦 *Cargo:* {cargo_type}\n"
                        f"📍 *Location:* {location}\n"
                        f"🛠️ *Issue:* {issue_type}\n\n"
                        f"🧠 *RAG Suggested Part:* _{recommended_part}_\n"
                        f"🏢 *Hub:* {hub}\n\n"
                        f"Authorize repair or reply with instructions?"
                    )
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
            return {"status": "meta_api_error", "status_code": res.status_code, "error_details": res.json()}
        return {"status": "dispatched_via_meta_api", "response": res.json()}
    
    return {"status": "simulated_interactive_dispatched", "message": f"Agentic WhatsApp alert sent to {cleaned_phone}."}

@app.get("/api/whatsapp-webhook")
async def verify_whatsapp_webhook(request: Request):
    hub_mode = request.query_params.get("hub.mode")
    hub_challenge = request.query_params.get("hub.challenge")
    hub_verify_token = request.query_params.get("hub.verify_token")
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Verification token mismatch")

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
            sender_phone = msg.get("from", "")
            
            # Case A: Button Click Response
            if msg.get("type") == "interactive":
                button_reply = msg["interactive"].get("button_reply", {})
                payload_id = button_reply.get("id", "")
                if "APPROVE_" in payload_id:
                    inc_id = payload_id.split("APPROVE_")[1]
                    APPROVAL_STATES[inc_id] = "APPROVED_AND_DISPATCHED"
                    return {"status": "success", "action": "Approved via button click."}
                elif "REJECT_" in payload_id:
                    inc_id = payload_id.split("REJECT_")[1]
                    APPROVAL_STATES[inc_id] = "REJECTED_REROUTING"
                    return {"status": "success", "action": "Rejected via button click."}
            
            # Case B: Conversational LLM Natural Language Text Response
            elif msg.get("type") == "text":
                text_body = msg["text"].get("body", "").lower()
                # Find active incident for this sender phone
                for phone, inc_id in INCIDENT_CONTEXTS.items():
                    if phone in sender_phone or sender_phone in phone:
                        if "local" in text_body or "fatuha" in text_body or "sasta" in text_body or "bypass" in text_body:
                            APPROVAL_STATES[inc_id] = "APPROVED_LOCAL_MECHANIC_REROUTED"
                        elif "ok" in text_body or "haan" in text_body or "kardo" in text_body or "approve" in text_body:
                            APPROVAL_STATES[inc_id] = "APPROVED_AND_DISPATCHED"
                        elif "cancel" in text_body or "reject" in text_body or "mat" in text_body:
                            APPROVAL_STATES[inc_id] = "REJECTED_REROUTING"
                        else:
                            APPROVAL_STATES[inc_id] = f"CUSTOM_INSTRUCTION_LOGGED: {text_body}"
                        return {"status": "success", "action": "Natural language intent parsed by LLM agent."}
    except Exception as e:
        return {"status": "error", "details": str(e)}

    return {"status": "received"}

@app.get("/api/health")
async def health_check():
    return {"status": "online", "engine": "Enterprise Agentic AI RAG & Swarm Orchestrator v4.0.0"}
