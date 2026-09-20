import os
import time
import uuid
import re
import json
from typing import List, Dict, Any, Optional
import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- STEP A: Observability (Feature 4) ---
from advanced.observability import traced, TraceContext

# --- STEP B: Hybrid Search + Reranking (Feature 1) ---
from advanced.hybrid_search import HybridSearchEngine

# --- STEP C: Self-RAG Hallucination Guard (Feature 3) ---
from advanced.self_rag import grade_hallucination

# --- STEP D: Multi-Modal image handling (Feature 5) ---
from advanced.multimodal import process_whatsapp_image_message

# --- STEP E: Multi-Agent LangGraph (Feature 2) ---
from advanced.multi_agent_graph import build_fleet_graph

# Real workshop-manual / parts-inventory knowledge base. Replace/extend this
# list with your actual manual chunks and inventory as you get them —
# each entry keeps the SAME fields your old hardcoded if/elif returned, so
# nothing downstream (run_swarm, WhatsApp messages, frontend) needs to change.
PARTS_KNOWLEDGE_BASE = [
    {
        "id": "kb-overheat-tata",
        # NOTE: the part number is included INSIDE the searchable "text",
        # exactly like a real manual page would read — this is what lets
        # the hallucination guard confirm the recommended part is grounded
        # in an actual source document instead of invented by the LLM.
        "text": "Engine overheat, coolant temperature warning, radiator choke, "
                 "thermostat valve blockage TATA Prima Signa heavy commercial. "
                 "Recommended part: Heavy Duty Coolant Pump & Thermostat Assembly (Part #TATA-9942-OH).",
        "vector_match_score": 0.94,
        "referenced_manual": "Tata Prima / Signa Heavy Commercial Maintenance Manual v4.2",
        "diagnostic_summary": "Radiator core choke or thermostat valve blockage detected.",
        "recommended_part": "Heavy Duty Coolant Pump & Thermostat Assembly (Part #TATA-9942-OH)",
        "part_number": "TATA-9942-OH",
        "estimated_repair_time_hours": 3.5,
    },
    {
        "id": "kb-transmission-eicher",
        "text": "Transmission gear slip, hydraulic clutch booster pressure drop, "
                 "gear actuator slip Eicher Pro Series heavy duty. "
                 "Recommended part: Eicher Heavy Transmission Actuator Seal Kit (Part #EIC-8812-TR).",
        "vector_match_score": 0.91,
        "referenced_manual": "Eicher Pro Series Heavy Duty Transmission Guide",
        "diagnostic_summary": "Hydraulic clutch booster pressure drop or gear actuator slip.",
        "recommended_part": "Eicher Heavy Transmission Actuator Seal Kit (Part #EIC-8812-TR)",
        "part_number": "EIC-8812-TR",
        "estimated_repair_time_hours": 5.0,
    },
    {
        "id": "kb-general-fleet",
        "text": "General electrical harness fault, fuel line pressure fluctuation, "
                 "standard commercial fleet telemetry fault. "
                 "Recommended part: Universal Heavy Fleet Fuel Filter & Sensor Kit (Part #FL-GEN-01).",
        "vector_match_score": 0.88,
        "referenced_manual": "General Commercial Fleet Telemetry & Fault Guide",
        "diagnostic_summary": "Standard electrical harness or fuel line pressure fluctuation.",
        "recommended_part": "Universal Heavy Fleet Fuel Filter & Sensor Kit (Part #FL-GEN-01)",
        "part_number": "FL-GEN-01",
        "estimated_repair_time_hours": 2.0,
    },
]

# Built ONCE at startup (not per-request — rebuilding the BM25/vector index
# on every incident would be slow and pointless since the KB doesn't change
# between requests).
PARTS_SEARCH_ENGINE = HybridSearchEngine(documents=PARTS_KNOWLEDGE_BASE)

app = FastAPI(title="Autonomous Enterprise Fleet Agentic AI & RAG Engine", version="4.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Fleet Unit ID to WhatsApp Number mapping
FLEET_WHATSAPP_MAPPING = {
    "BR01GP9621": "+917858847385",
    "BR01GM7465": "+916209313108",
    "BR01GP0756": "+916209313108",
    "BR01GP0757": "+916209313108",
    "BR01GP8148": "+916209313108"
}

# In-memory storage for HITL approval states and active contexts
APPROVAL_STATES = {}
INCIDENT_CONTEXTS = {}   # phone -> incident_id
INCIDENT_DETAILS = {}    # incident_id -> full context dict (for AI replies)
ACTIVE_VEHICLE_BY_PHONE = {}

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("PHONE_NUMBER_ID", "1340284595815318")
VERIFY_TOKEN = "fleet_secret_token_2026"
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

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


def send_whatsapp_text_reply(to_phone: str, text: str):
    """Sends a plain text reply back on WhatsApp with automatic fallback simulation."""
    if not WHATSAPP_TOKEN or WHATSAPP_TOKEN == "YOUR_TOKEN":
        print(f"SIMULATED WHATSAPP TO [{to_phone}]: {text}")
        return {"status": "simulated_reply", "text": text}
    
    cleaned_to_phone = ''.join(filter(str.isdigit, to_phone))
    
    url = f"https://graph.facebook.com/v26.0/{WHATSAPP_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}", 
        "Content-Type": "application/json"
    }
    body = {
        "messaging_product": "whatsapp",
        "to": cleaned_to_phone,
        "type": "text",
        "text": {"body": text}
    }
    try:
        res = requests.post(url, json=body, headers=headers, timeout=10)
        print(f"DEBUG META WHATSAPP API RESPONSE [{res.status_code}]:", res.text)
        
        # Agar Meta API se error aaye, toh terminal par message print kar do taaki pata chale
        if res.status_code != 200:
            print(f"⚠️ Meta API Error: Could not deliver WhatsApp message to {cleaned_to_phone}. Check token or test number verification.")
            
        return {"status_code": res.status_code, "response": res.json() if res.content else {}}
    except Exception as e:
        print(f"DEBUG META API EXCEPTION: {str(e)}")
        return {"status": "error", "details": str(e)}

def call_ai_agent(manager_text: str, incident_ctx: dict) -> dict:
    """
    Har ek incoming message ko Gemini AI Agent ke paas bhejta hai,
    uska smart decision nikalta hai aur professional WhatsApp reply banata hai.
    """
    if not GEMINI_API_KEY:
        return _keyword_fallback(manager_text)

    system_prompt = (
        "You are an advanced Autonomous Enterprise Fleet Operations AI Agent for Beekay Infra & Logistics. "
        "A manager has sent a WhatsApp message about a vehicle breakdown incident. "
        "First, understand what the manager is ACTUALLY asking or instructing — do not give a generic "
        "'approved and dispatched' reply unless they are actually approving something. "
        "If they ask for a phone number, contact, or showroom number — give the exact hub_phone value "
        "provided in the context, do NOT say you'll 'share it shortly' if the number is already given to you. "
        "If they ask a factual question, answer it directly and specifically using the context given. "
        "If they give an approval/rejection/reroute instruction, classify it accordingly. "
        "Classify their decision into exactly one of: APPROVED_AND_DISPATCHED, APPROVED_LOCAL_MECHANIC_REROUTED, "
        "REJECTED_REROUTING, INFO_REQUEST_ANSWERED (for questions/requests for info like phone numbers), "
        "or CUSTOM_INSTRUCTION_LOGGED (for anything else specific).\n\n"
        "Write a short (1-2 sentence), specific, professional WhatsApp reply that directly addresses what "
        "they asked or said — using the real details from the context (hub name, phone number, part name) "
        "wherever relevant.\n\n"
        "Respond ONLY as valid JSON in this exact format without markdown code blocks: "
        "{\"decision\": \"...\", \"reply_text\": \"...\"}"
    )

    user_prompt = (
        f"Incident Context:\n"
        f"- Vehicle ID: {incident_ctx.get('vehicle_id')}\n"
        f"- Issue Type: {incident_ctx.get('issue_type')}\n"
        f"- Assigned Hub: {incident_ctx.get('hub')}\n"
        f"- Hub Phone Number: {incident_ctx.get('hub_phone')}\n"
        f"- RAG Suggested Part: {incident_ctx.get('recommended_part')}\n\n"
        f"Manager's WhatsApp Message: \"{manager_text}\""
    )

    for attempt_model in ["gemini-flash-latest", "gemini-flash-lite-latest"]:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{attempt_model}:generateContent"
            headers = {
                "x-goog-api-key": GEMINI_API_KEY,
                "Content-Type": "application/json"
            }
            payload = {
                "systemInstruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
                "generationConfig": {"temperature": 0.3, "response_mime_type": "application/json"}
            }
            res = requests.post(url, json=payload, headers=headers, timeout=15)
            print(f"DEBUG GEMINI RAW RESPONSE [{attempt_model}] ({res.status_code}): {res.text[:300]}")

            if res.status_code == 503:
                continue  # busy — try the next (lighter) model

            res.raise_for_status()
            data = res.json()
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            cleaned_content = content.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(cleaned_content)

            if parsed.get("decision") and parsed.get("reply_text"):
                return parsed
        except Exception as e:
            print(f"DEBUG GEMINI AI ERROR [{attempt_model}]: {str(e)}")
            continue

    return _keyword_fallback(manager_text)

def _keyword_fallback(text_body: str) -> dict:
    t = text_body.lower()
    if "local" in t or "fatuha" in t or "sasta" in t or "bypass" in t:
        return {
            "decision": "APPROVED_LOCAL_MECHANIC_REROUTED",
            "reply_text": "✅ Understood — the vehicle has been rerouted to the local mechanic."
        }
    elif "ok" in t or "haan" in t or "kardo" in t or "approve" in t:
        return {
            "decision": "APPROVED_AND_DISPATCHED",
            "reply_text": "✅ Repair approved, dispatch sequence has been initiated."
        }
    elif "cancel" in t or "reject" in t or "mat" in t:
        return {
            "decision": "REJECTED_REROUTING",
            "reply_text": "❌ Request rejected, vehicle rerouting initiated."
        }
    else:
        return {
            "decision": f"CUSTOM_INSTRUCTION_LOGGED: {text_body}",
            "reply_text": "📝 Your instruction has been recorded, the team will follow up."
        }


class EnterpriseAgenticRAGOrchestrator:
    def __init__(self, incident: IncidentInput):
        self.incident = incident
        self.incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
        self.traces: List[AgentTrace] = []
        self.start_time = time.time()
        self.step_counter = 0

    @traced("agentic_rag_diagnostics")
    def _run_agentic_rag_diagnostics(self):
        # STEP B: real Hybrid Search (BM25 + dense + rerank) instead of
        # the old hardcoded if/elif keyword matching.
        query = f"{self.incident.issue_type} {self.incident.cargo_type}"
        results = PARTS_SEARCH_ENGINE.search(query, top_k=1)

        if results:
            top = results[0]
            rag_result = {
                "vector_match_score": round(
                    top.get("rerank_score", top.get("fused_score", 0.0)), 3
                ),
                "referenced_manual": top["referenced_manual"],
                "diagnostic_summary": top["diagnostic_summary"],
                "recommended_part": top["recommended_part"],
                "estimated_repair_time_hours": top["estimated_repair_time_hours"],
            }
        else:
            # Safe fallback if the KB has no reasonable match at all —
            # keeps the same shape as before so nothing downstream breaks.
            rag_result = {
                "vector_match_score": 0.0,
                "referenced_manual": "General Commercial Fleet Telemetry & Fault Guide",
                "diagnostic_summary": "No confident match found — escalate to human mechanic review.",
                "recommended_part": "Manual inspection required",
                "estimated_repair_time_hours": 2.0,
            }

        # STEP C: Self-RAG hallucination guard — confirms the part number in
        # the result actually came from our KB and wasn't invented.
        hallucination_check = grade_hallucination(rag_result["recommended_part"], results)
        rag_result["hallucination_guard"] = hallucination_check
        if not hallucination_check["grounded"]:
            print(f"⚠️ HALLUCINATION GUARD TRIGGERED: ungrounded codes "
                  f"{hallucination_check['ungrounded_codes']} — escalating for human review.")
            rag_result["diagnostic_summary"] += " [FLAGGED: part number could not be verified against KB]"

        return rag_result

    @traced("fetch_google_maps_route")
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

    @traced("heavy_service_center_intelligence")
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
                            "coords": geometry,
                            "place_id": place.get("place_id")
                        })
            except Exception:
                pass

        if not raw_hubs:
            default_heavy_hubs = [
                {"display_str": "TATA.CARS Service Centre - Guinea Motors, Patliputra Industrial Area, Patna, Bihar (Rating: 3.9)", "place_id": None, "phone": "0612-2262244"},
                {"display_str": "Eicher Commercial Vehicles Workshop, NH-30 Bypass Road, Patna, Bihar (Rating: 4.2)", "place_id": None, "phone": "0612-2277311"},
                {"display_str": "Tata Motors Authorized Commercial Heavy Workshop, Zero Mile, Patna, Bihar (Rating: 4.1)", "place_id": None, "phone": "0612-2233890"},
                {"display_str": "Eicher Trucks & Buses Service Station, Fatuha Industrial Area, Patna, Bihar (Rating: 4.0)", "place_id": None, "phone": "0612-2299456"}
            ]
            for hub in default_heavy_hubs:
                raw_hubs.append({"display_str": hub["display_str"], "coords": {}, "place_id": None, "phone": hub["phone"]})

        closest_hub_str = raw_hubs[0]["display_str"]
        closest_hub_place_id = raw_hubs[0].get("place_id")
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
                    closest_hub_place_id = raw_hubs[best_idx].get("place_id")
            except Exception:
                pass

        # Fetch real phone number for the chosen hub
        hub_phone = "Contact number not available — team will call and share shortly"
        for h in raw_hubs:
            if h["display_str"] == closest_hub_str:
                if h.get("phone"):
                    hub_phone = h["phone"]
                elif h.get("place_id") and GOOGLE_MAPS_API_KEY:
                    try:
                        details_url = "https://maps.googleapis.com/maps/api/place/details/json"
                        details_params = {
                            "place_id": h["place_id"],
                            "fields": "formatted_phone_number,international_phone_number",
                            "key": GOOGLE_MAPS_API_KEY
                        }
                        d_res = requests.get(details_url, params=details_params, timeout=5)
                        d_data = d_res.json()
                        phone = d_data.get("result", {}).get("formatted_phone_number") or d_data.get("result", {}).get("international_phone_number")
                        if phone:
                            hub_phone = phone
                    except Exception:
                        pass
                break

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
            "hub_phone": hub_phone,
            "all_detected_hubs": numbered_hubs
        }

    @traced("run_swarm_full_incident")
    def run_swarm(self) -> TriageResponse:
        map_route = self._fetch_google_maps_route()
        service_intel = self._get_heavy_service_center_intelligence()
        rag_intel = self._run_agentic_rag_diagnostics()
        detected_hubs = service_intel.get("all_detected_hubs", [])

        clean_vid = self.incident.vehicle_id.strip().upper()
        assigned_phone = FLEET_WHATSAPP_MAPPING.get(clean_vid, "+916209313108")

        APPROVAL_STATES[self.incident_id] = "PENDING_MANAGER_APPROVAL"
        INCIDENT_CONTEXTS[assigned_phone] = self.incident_id
        INCIDENT_DETAILS[self.incident_id] = {
            "vehicle_id": self.incident.vehicle_id,
            "issue_type": self.incident.issue_type,
            "hub": service_intel["hub"],
            "hub_phone": service_intel["hub_phone"],
            "recommended_part": rag_intel["recommended_part"]
        }

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


# --- STEP E: Multi-Agent LangGraph — NEW, ADDITIVE endpoint ---
# This does NOT replace /api/triage above. Both work side by side so the
# frontend keeps working unchanged while you test this separately (e.g. with
# curl/Postman) before ever switching the frontend to call /api/triage-v2.

def _maps_lookup_fn(location: str, destination: str):
    """Reuses the existing orchestrator's real Google Maps + workshop search
    logic instead of duplicating it, by spinning up a throwaway orchestrator
    just for this lookup."""
    temp_incident = IncidentInput(
        vehicle_id="N/A", location=location, destination=destination,
        issue_type="lookup", severity="Info", cargo_type="N/A",
    )
    temp_orchestrator = EnterpriseAgenticRAGOrchestrator(temp_incident)
    service_intel = temp_orchestrator._get_heavy_service_center_intelligence()
    return {"name": service_intel.get("hub"), "eta_minutes": None, "raw": service_intel}


# Built ONCE at startup — reuses the same PARTS_SEARCH_ENGINE from Step B.
FLEET_GRAPH = build_fleet_graph(
    hybrid_search_engine=PARTS_SEARCH_ENGINE,
    maps_lookup_fn=_maps_lookup_fn,
)


@app.post("/api/triage-v2")
async def trigger_triage_v2(incident: IncidentInput):
    incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
    config = {"configurable": {"thread_id": incident_id}}
    initial_state = {
        "incident_id": incident_id,
        "vehicle_id": incident.vehicle_id,
        "location": incident.location,
        "destination": incident.destination,
        "issue_type": incident.issue_type,
        "raw_error_log": incident.issue_type,
        "cargo_type": incident.cargo_type,
    }
    result = FLEET_GRAPH.invoke(initial_state, config)
    APPROVAL_STATES[incident_id] = "PENDING_MANAGER_APPROVAL"
    return {
        "incident_id": incident_id,
        "status": "AWAITING_HITL_APPROVAL",
        "severity": result.get("severity"),
        "matched_part_number": result.get("matched_part_number"),
        "nearest_workshop": result.get("nearest_workshop"),
        "traces": result.get("traces"),
    }


@app.post("/api/triage-v2/{incident_id}/approve")
async def approve_triage_v2(incident_id: str):
    config = {"configurable": {"thread_id": incident_id}}
    FLEET_GRAPH.update_state(config, {"approval_status": "approved"})
    result = FLEET_GRAPH.invoke(None, config)
    APPROVAL_STATES[incident_id] = "APPROVED_AND_DISPATCHED"
    return {"incident_id": incident_id, "final_status": result.get("final_status")}


@app.post("/api/triage-v2/{incident_id}/reject")
async def reject_triage_v2(incident_id: str):
    config = {"configurable": {"thread_id": incident_id}}
    FLEET_GRAPH.update_state(config, {"approval_status": "rejected"})
    result = FLEET_GRAPH.invoke(None, config)
    APPROVAL_STATES[incident_id] = "REJECTED_REROUTING"
    return {"incident_id": incident_id, "final_status": result.get("final_status")}

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
    token = WHATSAPP_TOKEN
    phone_id = WHATSAPP_PHONE_ID

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
        print("DEBUG WEBHOOK RECEIVED:", json.dumps(data, indent=2))
        
        entry = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if messages:
            msg = messages[0]
            raw_sender_phone = msg.get("from", "")
            sender_10_digit = ''.join(filter(str.isdigit, raw_sender_phone))[-10:]
            print(f"DEBUG: Sender 10-digit extracted: {sender_10_digit}")
            
            # Case A: Manager Button Click Response (Approve / Reject)
            if msg.get("type") == "interactive":
                button_reply = msg["interactive"].get("button_reply", {})
                payload_id = button_reply.get("id", "")
                print(f"DEBUG: Button clicked with ID: {payload_id}")
                
                if "APPROVE_" in payload_id:
                    inc_id = payload_id.split("APPROVE_")[1]
                    APPROVAL_STATES[inc_id] = "APPROVED_AND_DISPATCHED"
                    
                    # 1. Sabse pehle Manager ko confirmation bhejo ki approval mil gaya hai
                    send_whatsapp_text_reply(raw_sender_phone, "✅ Repair approved successfully by management. Dispatch sequence is active.")
                    
                    # 2. AB GAARI SE MAPPED DRIVER KO ALERT BHEJO (Jaise BR01GP9621 ke liye 7858847385)
                    incident_ctx = INCIDENT_DETAILS.get(inc_id, {})
                    vehicle_id = incident_ctx.get("vehicle_id")
                    hub = incident_ctx.get("hub")
                    recommended_part = incident_ctx.get("recommended_part")
                    
                    driver_phone = FLEET_WHATSAPP_MAPPING.get(vehicle_id)
                    if driver_phone:
                        # Driver ko active context mein register karo taaki woh AI agent se baat kar sake
                        cleaned_driver_10 = ''.join(filter(str.isdigit, driver_phone))[-10:]
                        INCIDENT_CONTEXTS[cleaned_driver_10] = inc_id
                        ACTIVE_VEHICLE_BY_PHONE[cleaned_driver_10] = vehicle_id
                        
                        # Driver ko official dispatch message bhejo
                        driver_msg = (
                            f"🚨 *OFFICIAL FLEET DISPATCH ALERT*\n\n"
                            f"🚜 *Vehicle:* {vehicle_id}\n"
                            f"Status: Repair *APPROVED* by Management.\n"
                            f"🛠️ *Assigned Workshop:* {hub}\n"
                            f"⚙️ *Required Part:* {recommended_part}\n\n"
                            f"You can now reply directly on this chat with your live updates or issues for the AI Operations Agent."
                        )
                        send_whatsapp_text_reply(driver_phone, driver_msg)
                        print(f"DEBUG: Manager approved. Dispatched notification to driver at {driver_phone} for vehicle {vehicle_id}")

                    return {"status": "success", "action": "Approved by manager and driver notified."}

                elif "REJECT_" in payload_id:
                    inc_id = payload_id.split("REJECT_")[1]
                    APPROVAL_STATES[inc_id] = "REJECTED_REROUTING"
                    send_whatsapp_text_reply(raw_sender_phone, "❌ Repair rejected — vehicle rerouting has been initiated.")
                    return {"status": "success", "action": "Rejected via button click."}
            
            # Case D (STEP D): Driver sends a PHOTO of the damaged part
            elif msg.get("type") == "image":
                media_id = msg["image"]["id"]
                print(f"DEBUG: Image received from {sender_10_digit}, media_id={media_id}")

                vehicle_id = ACTIVE_VEHICLE_BY_PHONE.get(sender_10_digit)
                vision_result = process_whatsapp_image_message(media_id, vehicle_id=vehicle_id)

                if vision_result.get("suggested_search_query"):
                    # Feed the vision description into the SAME hybrid search
                    # engine used for text-based diagnostics (Step B) — vision
                    # only ever describes what it sees, never invents a part
                    # number itself (that stays grounded via Step C).
                    search_results = PARTS_SEARCH_ENGINE.search(
                        vision_result["suggested_search_query"], top_k=1
                    )
                    if search_results:
                        top = search_results[0]
                        reply_text = (
                            f"📸 Photo analyzed.\n"
                            f"Observed: {vision_result.get('visible_damage', 'damage detected')}\n"
                            f"🔧 Likely part: {top['recommended_part']}\n"
                            f"📖 Reference: {top['referenced_manual']}"
                        )
                    else:
                        reply_text = (
                            f"📸 Photo analyzed: {vision_result.get('visible_damage', 'damage detected')}. "
                            f"Could not confidently match a part — a mechanic will review manually."
                        )
                else:
                    reply_text = "📸 Photo received, but I couldn't analyze it clearly. Please also describe the issue in text."

                send_whatsapp_text_reply(raw_sender_phone, reply_text)
                return {"status": "success", "action": "Image analyzed and replied.", "vision_result": vision_result}

            # Case B: Free Text Message (Chahe Manager ho ya Mapped Driver) -> Handled by Gemini AI Agent
            elif msg.get("type") == "text":
                text_body = msg["text"].get("body", "")
                print(f"DEBUG: Text message received for AI: {text_body} from {sender_10_digit}")
                
                matched_inc_id = None
                for phone, inc_id in INCIDENT_CONTEXTS.items():
                    reg_10_digit = ''.join(filter(str.isdigit, phone))[-10:]
                    if reg_10_digit == sender_10_digit:
                        matched_inc_id = inc_id
                        break
                
                if not matched_inc_id and INCIDENT_CONTEXTS:
                    matched_inc_id = list(INCIDENT_CONTEXTS.values())[-1]
                
                if matched_inc_id:
                    incident_ctx = INCIDENT_DETAILS.get(matched_inc_id, {})
                    # Add vehicle context if it's the driver
                    if sender_10_digit in ACTIVE_VEHICLE_BY_PHONE:
                        incident_ctx["current_chatter"] = f"Driver of {ACTIVE_VEHICLE_BY_PHONE[sender_10_digit]}"
                    
                    # Call Gemini AI Agent to generate smart contextual response
                    ai_result = call_ai_agent(text_body, incident_ctx)
                    resp = send_whatsapp_text_reply(raw_sender_phone, ai_result["reply_text"])
                    print("DEBUG AI AGENT SMART REPLY SENT TO CHATTER:", resp)
                    return {"status": "success", "action": "Smart AI agent replied to chatter.", "decision": ai_result["decision"]}
                else:
                    send_whatsapp_text_reply(raw_sender_phone, "⚠️ No active fleet incident context found for your session.")
                    return {"status": "error", "action": "No active incident context found."}
                    
    except Exception as e:
        print("DEBUG WEBHOOK ERROR:", str(e))
        return {"status": "error", "details": str(e)}

    return {"status": "received"}

@app.get("/api/health")
async def health_check():
    return {"status": "online", "engine": "Enterprise Agentic AI RAG & Swarm Orchestrator v4.1.0"}
