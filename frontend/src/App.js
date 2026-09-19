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

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResponseResult(null);

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
  
  const allNearbyHubs = procurementTrace?.all_nearby_service_centers || 
                        supervisorTrace?.all_nearby_service_centers || 
                        responseResult?.final_resolution?.all_available_service_centers || [];

  const googleMapsRouteUrl = `https://www.google.com/maps/dir/?api=1&origin=${encodeURIComponent(formData.location)}&destination=${encodeURIComponent(formData.destination)}&waypoints=${encodeURIComponent(nearestHub)}&travelmode=driving`;
  const googleMapsHubPinUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(nearestHub)}`;

  // WhatsApp Dispatch Handler
  const handleWhatsAppDispatch = () => {
    if (!responseResult) return;

    const targetPhone = responseResult.assigned_whatsapp_number.replace(/[^0-9]/g, '');
    
    let hubsText = allNearbyHubs.map((h) => `• ${h}`).join('\n');

    const whatsappMessage = 
      `🚨 *FLEET SWARM INCIDENT ALERT* 🚨\n\n` +
      `🚛 *Vehicle ID:* ${formData.vehicle_id}\n` +
      `📞 *Assigned WhatsApp Number:* ${responseResult.assigned_whatsapp_number}\n` +
      `⚠️ *Issue:* ${formData.issue_type} (${formData.severity})\n` +
      `📍 *Breakdown Location:* ${formData.location}\n\n` +
      `🎯 *Primary Nearest Hub:* \n${nearestHub}\n\n` +
      `📋 *Detected Authorized Service Centers (1 to N):*\n${hubsText}\n\n` +
      `🛣️ *Distance & ETA:* ${routingTrace?.total_distance || 'N/A'} (${routingTrace?.estimated_travel_time || 'N/A'})\n\n` +
      `🗺️ *Full Route Map with Waypoint:*\n${googleMapsRouteUrl}\n\n` +
      `_Managed via Beekay Infra & Logistics Swarm Engine_`;

    const whatsappUrl = `https://api.whatsapp.com/send?phone=${targetPhone}&text=${encodeURIComponent(whatsappMessage)}`;
    window.open(whatsappUrl, '_blank');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 md:p-8 font-sans">
      <div className="max-w-5xl mx-auto space-y-8">
        
        {/* Header */}
        <header className="border-b border-slate-800 pb-5 text-center">
          <div className="inline-block bg-blue-500/10 text-blue-400 text-xs font-semibold px-3 py-1 rounded-full mb-2 border border-blue-500/20">
            ● Swarm Cluster: Healthy & Active
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white">Hyper-Local Fleet Swarm Intelligence</h1>
          <p className="text-slate-400 text-sm mt-1">Deterministic Multi-Agent Self-Healing Logistics & WhatsApp Integration</p>
        </header>

        {/* Input Form Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-2xl">
          <h2 className="text-lg font-semibold text-blue-400 mb-4 flex items-center gap-2">
            <span>⚡</span> Inject Fleet Incident & Select Heavy Unit ID
          </h2>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Heavy Fleet Unit ID</label>
                <select name="vehicle_id" value={formData.vehicle_id} onChange={handleChange} className="w-full p-2.5 bg-slate-950 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500 font-mono">
                  <option value="BR01GP9621">BR01GP9621 (Driver 1)</option>
                  <option value="BR01GM7465">BR01GM7465 (Driver 2)</option>
                  <option value="BR01GP0756">BR01GP0756 (Driver 3)</option>
                  <option value="BR01GP0757">BR01GP0757 (Driver 4)</option>
                  <option value="BR01GP8148">BR01GP8148 (Driver 5)</option>
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
              {loading ? 'Dispatching Agent Swarm & Mapping WhatsApp...' : '🚀 Dispatch Agent Swarm & Map WhatsApp'}
            </button>
          </form>
        </div>

        {error && (
          <div className="bg-red-950/80 border border-red-800 text-red-200 p-4 rounded-xl text-sm">
            {String(error)}
          </div>
        )}

        {/* Execution Results & WhatsApp Dispatch Integration */}
        {responseResult && (
          <div className="space-y-6">
            
            <div className="bg-gradient-to-br from-slate-900 to-slate-950 border border-blue-500/30 rounded-xl p-6 shadow-2xl relative overflow-hidden">
              <div className="absolute top-0 right-0 bg-emerald-600 text-white text-[10px] font-bold px-3 py-1 rounded-bl-xl uppercase tracking-wider">
                WhatsApp Number Auto-Mapped
              </div>

              <h3 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
                <span>📍</span> Route & Nearby Authorized Service Centers (Proximity Matched)
              </h3>

              {/* Mapped WhatsApp Display Banner */}
              <div className="bg-emerald-950/40 border border-emerald-500/30 p-3.5 rounded-lg mb-5 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
                <div>
                  <span className="text-[10px] text-emerald-400 uppercase font-bold tracking-wider block">Target Unit & WhatsApp Mapping</span>
                  <div className="text-sm font-mono font-bold text-white flex items-center gap-2 mt-0.5">
                    <span>{responseResult.final_resolution.vehicle_id}</span>
                    <span className="text-slate-500">→</span>
                    <span className="text-emerald-300">{responseResult.assigned_whatsapp_number}</span>
                  </div>
                </div>
                <button 
                  onClick={handleWhatsAppDispatch}
                  className="w-full sm:w-auto bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-2 px-4 rounded-lg transition shadow-lg shadow-emerald-600/20 text-xs flex items-center justify-center gap-2 cursor-pointer"
                >
                  <span>💬</span> Send Complete Report to WhatsApp
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5">
                <div className="bg-slate-950/80 p-4 rounded-lg border border-slate-800">
                  <span className="text-xs text-slate-400 block uppercase tracking-wider mb-1">Total Distance & ETA</span>
                  <div className="text-xl font-extrabold text-blue-400">
                    {routingTrace?.total_distance || 'N/A'} <span className="text-sm font-normal text-slate-300">({routingTrace?.estimated_travel_time || 'N/A'})</span>
                  </div>
                  <p className="text-xs text-slate-400 mt-2">Status: <span className="text-emerald-400 font-medium">Proximity Optimized</span></p>
                </div>

                <div className="bg-slate-950/80 p-4 rounded-lg border border-slate-800 flex flex-col justify-between">
                  <div>
                    <span className="text-xs text-slate-400 block uppercase tracking-wider mb-1">Primary Nearest Hub (Closest to Breakdown)</span>
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
                    <span>🎯</span> Pinpoint Primary Hub on Google Maps
                  </a>
                </div>
              </div>

              {/* Numbered List of All Detected Service Centers */}
              <div className="bg-slate-900/90 p-4 rounded-lg border border-slate-800 mb-5">
                <strong className="text-white block mb-3 text-xs uppercase tracking-wider text-blue-400">
                  Detected Authorized Service Centers (Numbered List with Locations):
                </strong>
                {allNearbyHubs.length > 0 ? (
                  <ul className="space-y-2.5 text-xs text-slate-300">
                    {allNearbyHubs.map((hubName, idx) => (
                      <li key={idx} className="bg-slate-950 p-3 rounded-lg border border-slate-800/80 font-mono flex items-start gap-3 shadow-inner">
                        <span className="text-emerald-400 font-bold text-sm bg-emerald-950/50 px-2 py-0.5 rounded border border-emerald-800/40">{idx + 1}</span>
                        <span className="text-slate-200 leading-relaxed self-center">{typeof hubName === 'string' ? hubName.replace(/^\d+\.\s*/, '') : JSON.stringify(hubName)}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-xs text-slate-500 italic">No alternative service centers returned in this query batch.</p>
                )}
              </div>

              <a 
                href={googleMapsRouteUrl} 
                target="_blank" 
                rel="noopener noreferrer" 
                className="block text-center w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold py-3 px-4 rounded-lg transition shadow-lg shadow-blue-600/20 text-sm flex items-center justify-center gap-2"
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

/* lkflfk */
