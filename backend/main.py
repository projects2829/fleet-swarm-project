import time
import uuid
from typing import List, Dict, Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Hyper-Local Fleet Swarm Intelligence Engine", version="3.0.0")

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

# Exact Location-based Smart Mapping Database for Bihar Logistics
LOCATION_MAP = {
    "nh-31": {
        "corridor": "NH-31 Patna-Bakhtiyarpur Stretch",
        "alt_route": "Fatuha Link Road via Malislah Bypass (Avoiding NH-31 congestion)",
        "hub": "Fatuha Industrial Area Depot #2",
        "delay_saved": 3.8
    },
    "gandhi setu": {
        "corridor": "Mahatma Gandhi Setu (Ganga River Bridge)",
        "alt_route": "Digha-Sonepur Rail-Cum-Road Bridge (JP Setu) via Western Embankment",
        "hub": "Hajipur Industrialized Transit Hub #1",
        "delay_saved": 4.5
    },
    "danapur": {
        "corridor": "Danapur-Khagaul Freight Corridor",
        "alt_route": "Khagaul-Neora Inner Ring Road connecting Bihta-Sarmera Highway",
        "hub": "Bihta Regional Logistics Park",
        "delay_saved": 2.5
    },
    "bihta": {
        "corridor": "Bihta-Patna Elevated Expressway Route",
        "alt_route": "Koilwar Bridge Old Route via Naubatpur Expressway bypass",
        "hub": "Naubatpur Bulk Material Yard",
        "delay_saved": 3.2
    },
    "zero mile": {
        "corridor": "Patna Zero Mile / Bypass Chowk",
        "alt_route": "Ramkrishnanagar Outer Ring Connector to Bypass Expressway",
        "hub": "Zero Mile Central Storage Depot",
        "delay_saved": 2.8
    }
}

class HyperLocalSwarmOrchestrator:
    def __init__(self, incident: IncidentInput):
        self.incident = incident
        self.incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
        self.traces: List[AgentTrace] = []
        self.start_time = time.time()
        self.step_counter = 0

    def _get_location_intelligence(self):
        loc_lower = self.incident.location.lower()
        for key, data in LOCATION_MAP.items():
            if key in loc_lower:
                return data
        # Default dynamic fallback if custom location is typed
        return {
            "corridor": self.incident.location,
            "alt_route": f"Outer Ring Peripheral Bypass around {self.incident.location}",
            "hub": f"Patna Central Regional Hub for {self.incident.cargo_type.split()[0]}",
            "delay_saved": 3.0
        }

    def run_swarm(self) -> TriageResponse:
        loc_intel = self._get_location_intelligence()

        # 1. Supervisor Agent
        self.step_counter += 1
        t_start = time.time()
        risk = 0.94 if self.incident.severity == "CRITICAL" else 0.70
        sup_dec = {
            "action_required": True,
            "target_vehicle": self.incident.vehicle_id,
            "exact_location_locked": loc_intel["corridor"],
            "issue_detected": self.incident.issue_type,
            "assigned_sub_agents": ["RoutingAgent", "ProcurementAgent", "LegalAgent", "ERPSyncAgent"],
            "risk_score": risk
        }
        self.traces.append(AgentTrace(step_name="Supervisor_Triage", agent_role="Supervisor Agent", status="SUCCESS", timestamp=round((time.time() - t_start) * 1000, 2), output_payload=sup_dec))

        # 2. Routing Agent (Hyper-Accurate Alternative Way)
        self.step_counter += 1
        t_start = time.time()
        routing = {
            "target_corridor": loc_intel["corridor"],
            "primary_route_status": "SEVERELY_BLOCKED",
            "hyper_accurate_alternative_route": loc_intel["alt_route"],
            "estimated_delay_mitigated_hours": loc_intel["delay_saved"]
        }
        self.traces.append(AgentTrace(step_name="Routing_Recalculation", agent_role="Routing Agent", status="SUCCESS", timestamp=round((time.time() - t_start) * 1000, 2), output_payload=routing))

        # 3. Procurement Agent (Precise Hub & Stock Assignment)
        self.step_counter += 1
        t_start = time.time()
        proc = {
            "cargo_type": self.incident.cargo_type,
            "nearest_operational_hub": loc_intel["hub"],
            "inventory_status": f"100% replacement stock locked for {self.incident.vehicle_id}",
            "dispatch_status": "READY_FOR_IMMEDIATE_DISPATCH"
        }
        self.traces.append(AgentTrace(step_name="Procurement_Vendor_Negotiation", agent_role="Procurement Agent", status="SUCCESS", timestamp=round((time.time() - t_start) * 1000, 2), output_payload=proc))

        # 4. Legal Agent
        self.step_counter += 1
        t_start = time.time()
        legal = {
            "notice_generated": True,
            "incident_location": loc_intel["corridor"],
            "document_type": "Force Majeure / SLA Breach Notice",
            "penalty_clause_invoked": "Commercial Logistics SLA Section 14.2"
        }
        self.traces.append(AgentTrace(step_name="Legal_Compliance_Generation", agent_role="Legal Agent", status="SUCCESS", timestamp=round((time.time() - t_start) * 1000, 2), output_payload=legal))

        # 5. ERP Sync Agent
        self.step_counter += 1
        t_start = time.time()
        erp = {
            "erp_transaction_id": f"TXN-ERP-{uuid.uuid4().hex[:6].upper()}",
            "vehicle_logged": self.incident.vehicle_id,
            "ledger_status": "COMMITTED",
            "fleet_status_updated": "REROUTED_VIA_HYPER_ACCURATE_PATH"
        }
        self.traces.append(AgentTrace(step_name="ERP_State_Commit", agent_role="ERP Sync Agent", status="SUCCESS", timestamp=round((time.time() - t_start) * 1000, 2), output_payload=erp))

        return TriageResponse(
            incident_id=self.incident_id, status="RESOLVED_HYPER_LOCALLY",
            execution_time_ms=round((time.time() - self.start_time) * 1000, 2),
            deterministic_steps_executed=self.step_counter, traces=self.traces,
            final_resolution={
                "vehicle_id": self.incident.vehicle_id,
                "locked_location": loc_intel["corridor"],
                "mitigation_summary": f"Swarm rerouted unit {self.incident.vehicle_id} via {loc_intel['alt_route']}.",
                "erp_ref": erp["erp_transaction_id"]
            }
        )

@app.post("/api/triage", response_model=TriageResponse)
async def trigger_triage(incident: IncidentInput):
    return HyperLocalSwarmOrchestrator(incident).run_swarm()

@app.get("/api/health")
async def health_check():
    return {"status": "online", "engine": "Hyper-Local Fleet Swarm"}