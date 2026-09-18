import React, { useState } from 'react';
import './App.css';

function App() {
  const [formData, setFormData] = useState({
    vehicle_id: 'TRUCK-BR-01-9922',
    location: 'Zero Mile, Patna',
    destination: 'Hajipur Industrial Area Workshop',
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
        let errDetail = data.detail;
        if (typeof errDetail === 'object') {
          errDetail = JSON.stringify(errDetail);
        }
        setError(errDetail || 'Validation error from backend (422).');
      }
    } catch (err) {
      setError('Failed to connect to backend server. Make sure Render is online.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-4xl mx-auto">
        <header className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-blue-400">Hyper-Local Fleet Swarm Intelligence</h1>
          <p className="text-gray-400 text-sm mt-1">Real-Time Google Maps Dynamic Routing & Multi-Agent Orchestration</p>
        </header>

        <form onSubmit={handleSubmit} className="bg-gray-800 p-6 rounded-lg shadow-xl space-y-4 mb-8 border border-gray-700">
          <h2 className="text-xl font-semibold text-blue-300 border-b border-gray-700 pb-2">Emergency Dispatch Incident Input</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-400">Vehicle ID</label>
              <input type="text" name="vehicle_id" value={formData.vehicle_id} onChange={handleChange} className="w-full mt-1 p-2 bg-gray-900 border border-gray-700 rounded text-sm" required />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-400">Severity Level</label>
              <select name="severity" value={formData.severity} onChange={handleChange} className="w-full mt-1 p-2 bg-gray-900 border border-gray-700 rounded text-sm">
                <option value="CRITICAL">CRITICAL</option>
                <option value="MODERATE">MODERATE</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-400">1. Breakdown Location (Origin Start)</label>
              <input type="text" name="location" value={formData.location} onChange={handleChange} placeholder="e.g., Zero Mile, Patna" className="w-full mt-1 p-2 bg-gray-900 border border-gray-700 rounded text-sm" required />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-400">2. Destination Workshop / Hub (End)</label>
              <input type="text" name="destination" value={formData.destination} onChange={handleChange} placeholder="e.g., Hajipur Industrial Area" className="w-full mt-1 p-2 bg-gray-900 border border-gray-700 rounded text-sm" required />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-400">Issue Type</label>
              <input type="text" name="issue_type" value={formData.issue_type} onChange={handleChange} className="w-full mt-1 p-2 bg-gray-900 border border-gray-700 rounded text-sm" required />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-400">Cargo Type</label>
              <input type="text" name="cargo_type" value={formData.cargo_type} onChange={handleChange} className="w-full mt-1 p-2 bg-gray-900 border border-gray-700 rounded text-sm" required />
            </div>
          </div>

          <button type="submit" disabled={loading} className="w-full bg-blue-600 hover:bg-blue-500 text-white font-medium py-2 rounded transition">
            {loading ? 'Orchestrating Swarm via Google Maps...' : 'Deploy Fleet Swarm Agents'}
          </button>
        </form>

        {error && (
          <div className="bg-red-900/50 border border-red-700 text-red-200 p-4 rounded mb-6 text-sm">
            {String(error)}
          </div>
        )}

        {responseResult && (
          <div className="bg-gray-800 p-6 rounded-lg shadow-xl border border-gray-700 space-y-6">
            <div className="flex justify-between items-center border-b border-gray-700 pb-3">
              <div>
                <h3 className="text-lg font-bold text-green-400">Swarm Execution Successful</h3>
                <p className="text-xs text-gray-400">Incident ID: {String(responseResult?.incident_id || '')}</p>
              </div>
              <div className="text-right">
                <span className="text-xs bg-blue-900 text-blue-200 px-2 py-1 rounded">Time: {String(responseResult?.execution_time_ms || 0)} ms</span>
              </div>
            </div>

            <div className="bg-gray-900 p-4 rounded border border-gray-700">
              <h4 className="text-sm font-semibold text-yellow-400 mb-2">Trip Summary & Mitigation</h4>
              <p className="text-sm text-gray-300">{String(responseResult?.final_resolution?.mitigation_summary || '')}</p>
              <p className="text-xs text-gray-500 mt-2">ERP Reference ID: {String(responseResult?.final_resolution?.erp_ref || '')}</p>
            </div>

            <div>
              <h4 className="text-sm font-semibold text-blue-300 mb-3">Multi-Agent Pipeline Steps</h4>
              <div className="space-y-3">
                {responseResult?.traces?.map((trace, idx) => (
                  <div key={idx} className="bg-gray-900/80 p-3 rounded border border-gray-800 text-xs">
                    <div className="flex justify-heading font-semibold text-gray-300 mb-1">
                      <span>{String(trace?.agent_role || '')} — ({String(trace?.step_name || '')})</span>
                      <span className="text-green-400">{String(trace?.status || '')} ({String(trace?.timestamp || 0)}ms)</span>
                    </div>
                    <pre className="text-gray-400 overflow-x-auto whitespace-pre-wrap mt-1">
                      {JSON.stringify(trace?.output_payload, null, 2)}
                    </pre>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
