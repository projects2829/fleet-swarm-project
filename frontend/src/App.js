import React, { useState, useEffect } from 'react';

const BACKEND_URL = "https://your-backend-service.onrender.com"; // Apni Render URL yahan dalein

function App() {
  const [vehicleId, setVehicleId] = useState("BR01GP9621");
  const [location, setLocation] = useState("Patliputra Industrial Area, Patna");
  const [issueType, setIssueType] = useState("Engine Overheating & Transmission Fault");
  
  const [incidentData, setIncidentData] = useState(null);
  const [approvalStatus, setApprovalStatus] = useState("PENDING_MANAGER_APPROVAL");
  const [loading, setLoading] = useState(false);

  // 1. Trigger Triage & Send WhatsApp Interactive Message
  const handleTriggerTriage = async () => {
    setLoading(true);
    try {
      const triageRes = await fetch(`${BACKEND_URL}/api/triage`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          vehicle_id: vehicleId,
          location: location,
          issue_type: issueType,
          severity: "HIGH",
          cargo_type: "Heavy Construction Material"
        })
      });
      const triageJson = await triageRes.json();
      setIncidentData(triageJson);
      setApprovalStatus(triageJson.approval_status);

      // Send WhatsApp Interactive Buttons to Manager
      const waRes = await fetch(`${BACKEND_URL}/api/send-whatsapp-interactive`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          incident_id: triageJson.incident_id,
          phone: triageJson.assigned_whatsapp_number,
          vehicle_id: vehicleId,
          hub: triageJson.final_resolution.primary_nearest_hub
        })
      });
      const waJson = await waRes.json();
      
      if (waJson.status === "meta_api_error") {
        alert(`Meta API Error:\n${JSON.stringify(waJson.error_details, null, 2)}`);
      } else {
        alert("WhatsApp Interactive Approval Request Dispatched Successfully to Manager!");
      }
    } catch (err) {
      console.error(err);
      alert("Error triggering workflow");
    } finally {
      setLoading(false);
    }
  };

  // 2. 🔄 Live Polling Effect for WhatsApp Button Click Response
  useEffect(() => {
    if (!incidentData || !incidentData.incident_id) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/approval-status/${incidentData.incident_id}`);
        const data = await res.json();

        if (data.approval_status) {
          setApprovalStatus(data.approval_status);

          // Stop polling once approved or rejected
          if (data.approval_status === "APPROVED_AND_DISPATCHED" || data.approval_status === "REJECTED_REROUTING") {
            clearInterval(interval);
          }
        }
      } catch (err) {
        console.error("Polling error:", err);
      }
    }, 3000); // Check every 3 seconds

    return () => clearInterval(interval);
  }, [incidentData]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <div className="max-w-3xl mx-auto space-y-6">
        
        <header className="border-b border-slate-800 pb-4">
          <h1 className="text-2xl font-bold text-cyan-400">⚡ Fleet Swarm Intelligence Dashboard</h1>
          <p className="text-sm text-slate-400">Real-time Human-In-The-Loop (HITL) WhatsApp Dispatch Command Center</p>
        </header>

        {/* Input Form */}
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl space-y-4">
          <h2 className="text-lg font-semibold text-slate-200">Log Breakdown Incident</h2>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-slate-400 block mb-1">Vehicle ID</label>
              <input 
                type="text" 
                value={vehicleId} 
                onChange={(e) => setVehicleId(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded p-2 text-sm text-white" 
              />
            </div>
            <div>
              <label className="text-xs text-slate-400 block mb-1">Location / Corridor</label>
              <input 
                type="text" 
                value={location} 
                onChange={(e) => setLocation(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded p-2 text-sm text-white" 
              />
            </div>
          </div>

          <button 
            onClick={handleTriggerTriage}
            disabled={loading}
            className="w-full bg-cyan-600 hover:bg-cyan-500 font-semibold py-2.5 rounded transition text-sm text-white cursor-pointer disabled:opacity-50"
          >
            {loading ? "Processing Swarm Triage..." : "🚨 Trigger Emergency Triage & Send WhatsApp Approval"}
          </button>
        </div>

        {/* Live Status Tracking Panel */}
        {incidentData && (
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl space-y-4">
            <h3 className="text-md font-semibold text-cyan-300">Incident Tracker: {incidentData.incident_id}</h3>
            
            <div className="p-4 bg-slate-800/80 rounded-lg border border-slate-700 flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-400">Assigned Manager WhatsApp:</p>
                <p className="text-sm font-mono font-bold text-slate-200">{incidentData.assigned_whatsapp_number}</p>
              </div>

              <div>
                <p className="text-xs text-slate-400 mb-1">Live Status:</p>
                {approvalStatus === "PENDING_MANAGER_APPROVAL" && (
                  <span className="px-3 py-1 bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 rounded-full text-xs animate-pulse font-medium">
                    ⏳ Waiting for WhatsApp Response...
                  </span>
                )}
                {approvalStatus === "APPROVED_AND_DISPATCHED" && (
                  <span className="px-3 py-1 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-full text-xs font-bold">
                    ✅ Approved & Mechanic Dispatched!
                  </span>
                )}
                {approvalStatus === "REJECTED_REROUTING" && (
                  <span className="px-3 py-1 bg-rose-500/20 text-rose-400 border border-rose-500/30 rounded-full text-xs font-bold">
                    ❌ Rejected — Rerouting Triggered
                  </span>
                )}
              </div>
            </div>

            <div className="text-xs text-slate-400 bg-slate-950 p-3 rounded border border-slate-800">
              <span className="font-semibold text-slate-300">Selected Workshop:</span> {incidentData.final_resolution.primary_nearest_hub}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

export default App;
