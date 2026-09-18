import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [vehicleId, setVehicleId] = useState("BK-18W-4021");
  const [location, setLocation] = useState("NH-31 Patna-Bakhtiyarpur Stretch");
  const [destination, setDestination] = useState("Patna Central Depot / Warehouse B");
  const [issueType, setIssueType] = useState("breakdown");
  const [severity, setSeverity] = useState("CRITICAL");
  const [cargoType, setCargoType] = useState("Grade-A Ordinary Portland Cement");
  
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);

  const handleRunSwarm = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResponse(null);

    const API_BASE = process.env.REACT_APP_API_URL || "https://fleet-swarm-backend.onrender.com";

    try {
      const res = await axios.post(`${API_BASE}/api/triage`, {
        vehicle_id: vehicleId, 
        location, 
        destination, 
        issue_type: issueType, 
        severity, 
        cargo_type: cargoType
      });
      setResponse(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Failed to connect API.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#020617', color: '#f8fafc', padding: '24px', fontFamily: 'sans-serif' }}>
      <header style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '20px', borderBottom: '1px solid #1e293b' }}>
        <div>
          <h1 style={{ fontSize: '20px', fontWeight: 'bold', margin: 0 }}>AUTONOMOUS FLEET SWARM COMMAND</h1>
          <p style={{ fontSize: '12px', color: '#94a3b8', margin: '4px 0 0 0' }}>Deterministic Multi-Agent Self-Healing Logistics Engine</p>
        </div>
        <div style={{ padding: '6px 12px', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: '20px', color: '#34d399', fontSize: '12px' }}>
          ● Swarm Cluster: Healthy
        </div>
      </header>

      <main style={{ maxWidth: '1200px', margin: '24px auto 0 auto', display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '24px' }}>
        <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '16px', padding: '24px' }}>
          <h2 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', color: '#f1f5f9' }}>Inject Bottleneck / Incident</h2>
          <form onSubmit={handleRunSwarm} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Heavy Fleet Unit ID</label>
              <input type="text" value={vehicleId} onChange={(e) => setVehicleId(e.target.value)} style={{ width: '100%', background: '#020617', border: '1px solid #334155', borderRadius: '8px', padding: '10px', color: '#fff', fontSize: '14px' }} required />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Highway / Current Location</label>
              <input type="text" value={location} onChange={(e) => setLocation(e.target.value)} style={{ width: '100%', background: '#020617', border: '1px solid #334155', borderRadius: '8px', padding: '10px', color: '#fff', fontSize: '14px' }} required />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Destination</label>
              <input type="text" value={destination} onChange={(e) => setDestination(e.target.value)} style={{ width: '100%', background: '#020617', border: '1px solid #334155', borderRadius: '8px', padding: '10px', color: '#fff', fontSize: '14px' }} required />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Issue Type</label>
                <select value={issueType} onChange={(e) => setIssueType(e.target.value)} style={{ width: '100%', background: '#020617', border: '1px solid #334155', borderRadius: '8px', padding: '10px', color: '#fff', fontSize: '14px' }}>
                  <option value="breakdown">Breakdown</option>
                  <option value="route_blockage">Blockage</option>
                  <option value="material_delay">Delay</option>
                </select>
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Severity</label>
                <select value={severity} onChange={(e) => setSeverity(e.target.value)} style={{ width: '100%', background: '#020617', border: '1px solid #334155', borderRadius: '8px', padding: '10px', color: '#fff', fontSize: '14px' }}>
                  <option value="CRITICAL">Critical</option>
                  <option value="MEDIUM">Medium</option>
                </select>
              </div>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Cargo Type</label>
              <input type="text" value={cargoType} onChange={(e) => setCargoType(e.target.value)} style={{ width: '100%', background: '#020617', border: '1px solid #334155', borderRadius: '8px', padding: '10px', color: '#fff', fontSize: '14px' }} required />
            </div>
            <button type="submit" disabled={loading} style={{ marginTop: '8px', width: '100%', padding: '12px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: '8px', fontWeight: 'bold', cursor: 'pointer' }}>
              {loading ? "Executing Swarm Triage..." : "Dispatch Agent Swarm"}
            </button>
          </form>
          {error && <div style={{ marginTop: '12px', padding: '10px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '8px', color: '#f87171', fontSize: '12px' }}>{error}</div>}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '14px' }}>
            <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', padding: '16px' }}>
              <p style={{ fontSize: '12px', color: '#94a3b8', margin: 0 }}>Incident Reference</p>
              <p style={{ fontSize: '16px', fontWeight: 'bold', color: '#fff', margin: '6px 0 0 0' }}>{response ? response.incident_id : "---"}</p>
            </div>
            <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', padding: '16px' }}>
              <p style={{ fontSize: '12px', color: '#94a3b8', margin: 0 }}>Deterministic Latency</p>
              <p style={{ fontSize: '16px', fontWeight: 'bold', color: '#60a5fa', margin: '6px 0 0 0' }}>{response ? `${response.execution_time_ms} ms` : "---"}</p>
            </div>
            <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', padding: '16px' }}>
              <p style={{ fontSize: '12px', color: '#94a3b8', margin: 0 }}>Validated Steps</p>
              <p style={{ fontSize: '16px', fontWeight: 'bold', color: '#34d399', margin: '6px 0 0 0' }}>{response ? response.deterministic_steps_executed : "---"}</p>
            </div>
          </div>

          <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '16px', padding: '24px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', color: '#f1f5f9' }}>Agent Execution Graph & Trace Logs</h3>
            {!response ? (
              <div style={{ textAlign: 'center', padding: '40px', border: '2px dashed #1e293b', borderRadius: '12px', color: '#64748b', fontSize: '14px' }}>
                No active swarm traces. Trigger an incident from the left panel.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {response.traces.map((trace, index) => (
                  <div key={index} style={{ background: '#020617', border: '1px solid #1e293b', borderRadius: '10px', padding: '14px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '13px' }}>
                      <span style={{ color: '#60a5fa', fontWeight: 'bold' }}>{trace.agent_role} - {trace.step_name}</span>
                      <span style={{ color: '#34d399' }}>{trace.timestamp} ms ({trace.status})</span>
                    </div>
                    <pre style={{ fontSize: '11px', color: '#94a3b8', background: '#0f172a', padding: '10px', borderRadius: '6px', overflowX: 'auto', margin: 0 }}>
                      {JSON.stringify(trace.output_payload, null, 2)}
                    </pre>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
