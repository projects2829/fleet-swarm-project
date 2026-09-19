import React, { useState } from 'react';
import './App.css';

function App() {
  const [formData, setFormData] = useState({
    vehicle_id: 'BR01GP9621',
    location: 'Atal Path, Patna, Bihar, India',
    destination: 'Pragati Path, Barmasia Rd, Katihar, Bihar 854105, India',
    issue_type: 'Engine Overheat & Transmission Breakdown',
    severity: 'CRITICAL',
    cargo_type: 'Heavy Construction Steel Rods'
  });

  const [loading, setLoading] = useState(false);
  const [responseResult, setResponseResult] = useState(null);
  const [error, setError] = useState(null);
  const [approvalStatus, setApprovalStatus] = useState('PENDING');

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResponseResult(null);
    setApprovalStatus('PENDING');

    const API_URL = process.env.REACT_APP_API_URL || 'https://fleet-swarm-backend.onrender.com';

    try {
      const res = await fetch(`${API_URL}/api/triage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      const data = await res.json();
      if (res.ok) {
        setResponseResult(data);
        setApprovalStatus(data.approval_status);
      } else {
        setError(data.detail || 'Validation error from backend.');
      }
    } catch (err) {
      setError('Failed to connect to backend server.');
    } finally {
      setLoading(false);
    }
  };

  const routingTrace = responseResult?.traces?.find(t => t.step_name === 'Routing_Recalculation')?.output_payload;
  const procurementTrace = responseResult?.traces?.find(t => t.step_name === 'Procurement_Vendor_Negotiation')?.output_payload;
  const supervisorTrace = responseResult?.traces?.find(t => t.step_name === 'Supervisor_Triage')?.output_payload;

  const nearestHub = procurementTrace?.nearest_operational_hub || supervisorTrace?.destination_workshop || 'Authorized Service Hub';
  const allNearbyHubs = supervisorTrace?.all_nearby_service_centers || responseResult?.final_resolution?.all_available_service_centers || [];

  const googleMapsRouteUrl = `https://www.google.com/maps/dir/?api=1&origin=${encodeURIComponent(formData.location)}&destination=${encodeURIComponent(formData.destination)}&waypoints=${encodeURIComponent(nearestHub)}&travelmode=driving`;
  const googleMapsHubPinUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(nearestHub)}`;

  // Trigger WhatsApp Interactive Buttons Dispatch
  const handleTriggerInteractiveApproval = async () => {
    if (!responseResult) return;
    const API_URL = process.env.REACT_APP_API_URL || 'https://fleet-swarm-backend.onrender.com';

    try {
      const res = await fetch(`${API_URL}/api/send-whatsapp-interactive`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          incident_id: responseResult.incident_id,
          phone: responseResult.assigned_whatsapp_number,
          vehicle_id: formData.vehicle_id,
          hub: nearestHub
        })
      });
      const data = await res.json();
      alert(`HITL Status: ${data.status}\nInteractive Approval Buttons sent to WhatsApp number: ${responseResult.assigned_whatsapp_number}`);
    } catch (err) {
      alert('Failed to trigger interactive WhatsApp message.');
    }
  };

  // Simulate Manager Clicking "Approve Repair" on WhatsApp
  const handleSimulateManagerApproval = () => {
    setApprovalStatus('APPROVED_AND_DISPATCHED');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 md:p-8 font-sans">
      <div className="max-w-5xl mx-auto space-y-8">
        
        {/* Header */}
        <header className="border-b border-slate-800 pb-5 text-center">
          <div className="inline-block bg-blue-500/10 text-blue-400 text-xs font-semibold px-3 py-1 rounded-full mb-2 border border-blue-500/20">
            ● Swarm Cluster: HITL Active
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white">Hyper-Local Fleet Swarm Intelligence</h1>
          <p className="text-slate-400 text-sm mt-1">Deterministic Multi-Agent Swarm with Human-in-the-Loop WhatsApp Interactive Gates</p>
        </header>

        {/* Input Form Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-2xl">
          <h2 className="text-lg font-semibold text-blue-400 mb-4 flex items-center gap-2">
            <span>⚡</span> Inject Fleet Incident & HITL Gate
          </h2>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Heavy Fleet Unit ID</label>
                <select name="vehicle_id" value={formData.vehicle_id} onChange={handleChange} className="w-full p-2.5 bg-slate-950 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500 font-mono">
                  <option value="BR01GP9621">BR01GP9621</option>
                  <option value="BR01GM7465">BR01GM7465</option>
                  <option value="BR01GP0756">BR01GP0756</option>
                  <option value="BR01GP0757">BR01GP0757</option>
                  <option value="BR01GP8148">BR01GP8148</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Severity Level</label>
                <select name="severity" value={formData.severity} onChange={handleChange} className="w-full p-2.5 bg-slate-950 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500">
                  <option value="CRITICAL">CRITICAL</option>
                  <option value="MODERATE">MODERATE</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Cargo Type</label>
                <input type="text" name="cargo_type" value={formData.cargo_type} onChange={handleChange} className="w-full p-2.5 bg-slate-950 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500" required />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Highway / Breakdown Location (Origin)</label>
                <input type="text" name="location" value={formData.location} onChange={handleChange} className="w-full p-2.5 bg-slate-950 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500" required />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Destination Workshop / Hub (End)</label>
                <input type="text" name="destination" value={formData.destination} onChange={handleChange} className="w-full p-2.5 bg-slate-950 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500" required />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Issue Type / Breakdown Details</label>
              <input type="text" name="issue_type" value={formData.issue_type} onChange={handleChange} className="w-full p-2.5 bg-slate-950 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500" required />
            </div>

            <button type="submit" disabled={loading} className="w-full bg-blue-600 hover:bg-blue-500 text-white font-medium py-3 rounded-lg transition duration-200 shadow-lg shadow-blue-600/20 disabled:opacity-50">
              {loading ? 'Executing Swarm & Setting HITL Gate...' : '🚀 Dispatch Swarm & Enable HITL Gate'}
            </button>
          </form>
        </div>

        {error && (
          <div className="bg-red-950/80 border border-red-800 text-red-200 p-4 rounded-xl text-sm">
            {String(error)}
          </div>
        )}

        {/* Execution Results & HITL Interactive Panel */}
        {responseResult && (
          <div className="space-y-6">
            
            <div className="bg-gradient-to-br from-slate-900 to-slate-950 border border-blue-500/30 rounded-xl p-6 shadow-2xl relative overflow-hidden">
              <div className="absolute top-0 right-0 bg-amber-600 text-white text-[10px] font-bold px-3 py-1 rounded-bl-xl uppercase tracking-wider">
                HITL Approval Gate Active
              </div>

              <h3 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
                <span>🛡️</span> Human-in-the-Loop WhatsApp Interactive Workflow
              </h3>

              {/* Approval Status Banner */}
              <div className={`p-4 rounded-lg mb-5 border flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 ${
                approvalStatus === 'APPROVED_AND_DISPATCHED' 
                  ? 'bg-emerald-950/50 border-emerald-500/40 text-emerald-300' 
                  : 'bg-amber-950/40 border-amber-500/30 text-amber-300'
              }`}>
                <div>
                  <span className="text-[10px] uppercase font-bold tracking-wider block opacity-80">Manager Approval Status</span>
                  <div className="text-sm font-bold mt-0.5">
                    {approvalStatus === 'APPROVED_AND_DISPATCHED' 
                      ? '✅ Approved by Manager (ERP State Committed & Mechanic Dispatched)' 
                      : '⏳ Pending Manager Approval (Waiting for WhatsApp Interactive Click)'}
                  </div>
                </div>

                <div className="flex gap-2 w-full sm:w-auto">
                  {approvalStatus !== 'APPROVED_AND_DISPATCHED' && (
                    <>
                      <button 
                        onClick={handleTriggerInteractiveApproval}
                        className="bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold py-2 px-3 rounded transition"
                      >
                        📲 Send Buttons to WhatsApp
                      </button>
                      <button 
                        onClick={handleSimulateManagerApproval}
                        className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold py-2 px-3 rounded transition"
                      >
                        ✅ Simulate "Approve" Click
                      </button>
                    </>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5">
                <div className="bg-slate-950/80 p-4 rounded-lg border border-slate-800">
                  <span className="text-xs text-slate-400 block uppercase tracking-wider mb-1">Total Distance & ETA</span>
                  <div className="text-xl font-extrabold text-blue-400">
                    {routingTrace?.total_distance || 'N/A'} <span className="text-sm font-normal text-slate-300">({routingTrace?.estimated_travel_time || 'N/A'})</span>
                  </div>
                </div>

                <div className="bg-slate-950/80 p-4 rounded-lg border border-slate-800 flex flex-col justify-between">
                  <div>
                    <span className="text-xs text-slate-400 block uppercase tracking-wider mb-1">Primary Nearest Hub</span>
                    <div className="text-sm font-bold text-emerald-400 truncate">
                      {nearestHub}
                    </div>
                  </div>
                  <a 
                    href={googleMapsHubPinUrl}
                    target="_blank" 
                    rel="noopener noreferrer" 
                    className="mt-3 text-center bg-slate-900 hover:bg-slate-800 text-emerald-400 border border-emerald-500/40 text-xs font-semibold py-1.5 px-3 rounded transition flex items-center justify-center gap-1.5"
                  >
                    <span>🎯</span> Pinpoint Hub on Google Maps
                  </a>
                </div>
              </div>

              {/* Numbered List */}
              <div className="bg-slate-900/90 p-4 rounded-lg border border-slate-800 mb-5">
                <strong className="text-white block mb-3 text-xs uppercase tracking-wider text-blue-400">
                  Detected Authorized Service Centers:
                </strong>
                <ul className="space-y-2.5 text-xs text-slate-300">
                  {allNearbyHubs.map((hubName, idx) => (
                    <li key={idx} className="bg-slate-950 p-3 rounded-lg border border-slate-800/80 font-mono flex items-start gap-3 shadow-inner">
                      <span className="text-emerald-400 font-bold text-sm bg-emerald-950/50 px-2 py-0.5 rounded border border-emerald-800/40">{idx + 1}</span>
                      <span className="text-slate-200 leading-relaxed self-center">{typeof hubName === 'string' ? hubName.replace(/^\d+\.\s*/, '') : JSON.stringify(hubName)}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <a 
                href={googleMapsRouteUrl} 
                target="_blank" 
                rel="noopener noreferrer" 
                className="block text-center w-full bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-3 px-4 rounded-lg transition shadow-lg shadow-emerald-600/20 text-sm flex items-center justify-center gap-2"
              >
                <span>🗺️</span> Open Full Route with Hub Waypoint in Google Maps
              </a>
            </div>

          </div>
        )}

      </div>
    </div>
  );
}

export default App;
