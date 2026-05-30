import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useLogSimulator } from '../hooks/useLogSimulator'

// ====================================================================
// TATVA | Active Intelligence Reconstruction
// Stitch screen: 6e14101adf5349c5a93937eddb742a3c
// Color: Blue palette (#98cbff primary, #feb700 amber accent)
// Layout: Sidebar + 3-panel (pipeline left, graph center, logs right)
// overflow: hidden — fixed height
// ====================================================================

export default function ReconstructionPage() {
  const navigate = useNavigate()
  const [summary, setSummary] = useState<any>(null)
  useLogSimulator('logs-feed', 3000)

  useEffect(() => {
    fetch('http://localhost:8000/api/insights/summary')
      .then(res => res.json())
      .then(data => setSummary(data))
      .catch(err => console.error('Failed to fetch summary', err))

    const timer = setTimeout(() => {
      navigate('/investigation')
    }, 8000) // 8 seconds simulated loading time
    return () => clearTimeout(timer)
  }, [navigate])

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: '#0a0a0b', fontFamily: 'Geist, sans-serif', color: '#e5e2e3' }}>

      {/* ── LEFT SIDEBAR ── */}
      <aside className="flex flex-col h-full py-6 border-r border-[#3f4852]/20 w-64 transition-all duration-300 ease-in-out"
        style={{ background: 'rgba(28,27,28,0.9)', backdropFilter: 'blur(12px)' }}>
        <div className="px-6 mb-8">
          <h1 style={{ fontFamily: 'Geist', fontSize: '24px', fontWeight: '600', color: '#e5e2e3' }}>Unit 01</h1>
          <p className="uppercase tracking-widest opacity-60" style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#bec7d4' }}>Forensic Division</p>
        </div>

        {/* Nav Items */}
        <nav className="flex-grow space-y-1">
          {[
            { icon: 'folder_open', label: 'Evidence Vault', path: '/evidence', active: false },
            { icon: 'hub', label: 'Entity Graph', path: '/investigation', active: false },
            { icon: 'description', label: 'Case Files', path: '/case/new', active: false },
            { icon: 'smart_card_reader', label: 'Digital Forensics', path: '/forensics', active: false },
            { icon: 'history', label: 'Timeline', path: '/reconstruction', active: true },
          ].map(item => (
            <div
              key={item.path}
              onClick={() => navigate(item.path)}
              className={`flex items-center gap-3 px-4 py-3 cursor-pointer transition-all duration-300 ${item.active
                ? 'border-r-4 border-[#feb700]'
                : 'text-[#bec7d4] hover:text-[#e5e2e3]'
              }`}
              style={item.active ? { background: 'rgba(254,183,0,0.1)', color: '#ffdb9d' } : {}}
            >
              <span className="material-symbols-outlined">{item.icon}</span>
              <span className="uppercase tracking-wider" style={{ fontFamily: 'JetBrains Mono', fontSize: '14px', fontWeight: '500' }}>{item.label}</span>
            </div>
          ))}
        </nav>

        {/* Bottom */}
        <div className="px-4 mt-auto space-y-4">
          <button
            onClick={() => navigate('/case/new')}
            className="w-full py-3 rounded font-bold uppercase text-sm tracking-widest hover:brightness-110 active:scale-95 transition-transform"
            style={{ background: '#feb700', color: '#412d00' }}
          >
            New Investigation
          </button>
          <div className="space-y-1 pt-4 border-t border-[#3f4852]/20">
            <div className="flex items-center gap-3 text-[#bec7d4] px-2 py-2 text-xs">
              <span className="material-symbols-outlined text-sm">help</span>
              <span>Help Center</span>
            </div>
            <div className="flex items-center gap-3 text-[#bec7d4] px-2 py-2 text-xs">
              <span className="material-symbols-outlined text-sm">analytics</span>
              <span>System Status</span>
            </div>
          </div>
        </div>
      </aside>

      {/* ── MAIN CONTENT ── */}
      <main className="flex-grow flex flex-col relative overflow-hidden" style={{ background: '#131314' }}>

        {/* Top Navigation */}
        <header className="flex justify-between items-center w-full h-16 border-b border-[#3f4852]/30 z-20 px-8"
          style={{ background: 'rgba(19,19,20,0.8)', backdropFilter: 'blur(16px)' }}>
          <div className="flex items-center gap-8">
            <span
              className="font-black tracking-widest cursor-pointer"
              onClick={() => navigate('/')}
              style={{ fontFamily: 'Geist', fontSize: '40px', fontWeight: '900', color: '#feb700', letterSpacing: '0.1em', lineHeight: '48px' }}
            >
              TATVA
            </span>
            <nav className="hidden md:flex gap-6">
              <a href="#" onClick={(e) => { e.preventDefault(); navigate('/case/new') }} className="font-medium hover:text-[#ffdb9d] transition-colors duration-200" style={{ color: '#bec7d4', fontFamily: 'Geist', fontSize: '16px' }}>Dashboard</a>
            </nav>
          </div>
          <div className="flex items-center gap-6">
            <div className="relative">
              <input
                type="text"
                placeholder="Search evidence..."
                className="border border-[#3f4852] rounded-full px-4 py-1 text-sm focus:outline-none focus:border-[#98cbff] transition-all w-64"
                style={{ background: 'rgba(28,27,28,0.9)', color: '#e5e2e3', fontFamily: 'Geist' }}
              />
            </div>
            <div className="flex gap-4">
              <span className="material-symbols-outlined text-[#bec7d4] cursor-pointer hover:text-[#ffdb9d]">notifications</span>
              <span className="material-symbols-outlined text-[#bec7d4] cursor-pointer hover:text-[#ffdb9d]">settings</span>
            </div>
            <img src="/assets/avatars/investigator-1.jpg" alt="Profile" className="w-8 h-8 rounded-full border border-[#feb700]/30 object-cover" />
          </div>
        </header>

        {/* ── DYNAMIC RECONSTRUCTION LAYER ── */}
        <div className="flex-grow flex p-6 gap-6 relative">

          {/* Background grid */}
          <div className="absolute inset-0 z-0 opacity-20 pointer-events-none">
            <div className="w-full h-full scanline relative">
              <div className="absolute inset-0" style={{ backgroundImage: 'linear-gradient(rgba(152,203,255,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(152,203,255,0.05) 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
            </div>
          </div>

          {/* ── LEFT PANEL: Processing Pipeline ── */}
          <div className="w-72 glass-panel-blue rounded-xl p-4 flex flex-col z-10">
            <div className="flex justify-between items-center mb-6">
              <h3 className="uppercase tracking-widest" style={{ fontFamily: 'JetBrains Mono', fontSize: '14px', fontWeight: '500', color: '#98cbff' }}>Pipeline v.4.2</h3>
              <span className="px-2 py-0.5 border border-[#3f4852] opacity-50" style={{ fontFamily: 'JetBrains Mono', fontSize: '10px' }}>ACTIVE_STREAM</span>
            </div>

            <div className="space-y-4 flex-grow overflow-y-auto pr-2 custom-scrollbar">
              <PipelineStage color="#feb700" label="Parsing Evidence" sublabel="42.8 GB Raw Ingested" status="active" />
              <PipelineStage color="#98cbff" label="Extracting Entities" sublabel="Processing 1,240 nodes" status="processing" />
              <PipelineStage color="#88919d" label="Resolving Identities" sublabel="Pending Cross-Reference" status="pending" />
              <PipelineStage color="#88919d" label="Constructing Knowledge Graph" sublabel="" status="pending" />
              <PipelineStage color="#88919d" label="Running Graph Intelligence" sublabel="" status="pending" />
              <PipelineStage color="#88919d" label="Temporal Reconstruction" sublabel="" status="pending" />
              <PipelineStage color="#ffb4ab" label="Anomaly Detection" sublabel="" status="error" />
              <PipelineStage color="#88919d" label="Generating Intelligence Signals" sublabel="" status="pending" />
            </div>

            {/* Progress bar */}
            <div className="mt-4 pt-4 border-t border-[#3f4852]/20">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-1.5 h-1.5 bg-[#feb700] rounded-full animate-pulse" />
                <span className="uppercase tracking-widest" style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#feb700' }}>Reconstructing...</span>
              </div>
              <div className="h-1 bg-[#353436] rounded-full overflow-hidden">
                <div className="h-full w-[45%] transition-all duration-1000" style={{ background: '#feb700', boxShadow: '0 0 8px #feb700' }} />
              </div>
            </div>
          </div>

          {/* ── MIDDLE PANEL: Animated Graph Reconstruction ── */}
          <div className="flex-grow relative z-10 flex flex-col">
            {/* Status tags */}
            <div className="absolute top-4 right-4 flex gap-4 z-10">
              <div className="glass-panel-blue px-3 py-1 rounded" style={{ fontFamily: 'JetBrains Mono', fontSize: '10px', color: '#ffdb9d', border: '1px solid rgba(254,183,0,0.2)' }}>
                RECON_TYPE: MULTIDIMENSIONAL
              </div>
              <div className="glass-panel-blue px-3 py-1 rounded" style={{ fontFamily: 'JetBrains Mono', fontSize: '10px', color: '#98cbff', border: '1px solid rgba(152,203,255,0.2)' }}>
                STABILITY: 94.2%
              </div>
            </div>

            {/* Graph area */}
            <div className="flex-grow relative flex items-center justify-center pointer-events-none" id="graph-area">
              <div className="relative w-96 h-96">
                {/* Orbit rings */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-64 h-64 border-2 border-dashed border-[#feb700]/20 rounded-full" style={{ animation: 'spin 20s linear infinite' }} />
                  <div className="absolute w-80 h-80 border border-[#98cbff]/10 rounded-full" style={{ animation: 'spin 30s linear infinite reverse' }} />
                </div>

                {/* Floating Nodes */}
                <div className="absolute node-pulse" style={{ top: '25%', left: '25%' }}>
                  <div className="w-4 h-4 bg-[#98cbff] rounded-full" style={{ boxShadow: '0 0 12px #98cbff' }} />
                  <span className="absolute whitespace-nowrap -translate-x-1/2 left-1/2" style={{ top: '-24px', fontFamily: 'JetBrains Mono', fontSize: '10px', color: '#98cbff' }}>ENTITY_84A</span>
                </div>
                <div className="absolute node-pulse" style={{ bottom: '33%', right: '25%', animationDelay: '0.5s' }}>
                  <div className="w-3 h-3 bg-[#feb700] rounded-full" style={{ boxShadow: '0 0 10px #feb700' }} />
                  <span className="absolute whitespace-nowrap -translate-x-1/2 left-1/2" style={{ bottom: '-24px', fontFamily: 'JetBrains Mono', fontSize: '10px', color: '#feb700' }}>TRANS_ID_981</span>
                </div>
                <div className="absolute node-pulse" style={{ top: '50%', right: '33%', animationDelay: '1.2s' }}>
                  <div className="w-5 h-5 bg-[#ffb4ab] rounded-full" style={{ boxShadow: '0 0 15px #ffb4ab' }} />
                  <span className="absolute whitespace-nowrap -translate-x-1/2 left-1/2" style={{ top: '-32px', fontFamily: 'JetBrains Mono', fontSize: '10px', color: '#ffb4ab' }}>ANOMALY_ERR</span>
                </div>

                {/* Central Hub */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-16 h-16 rounded-full blur-xl animate-pulse" style={{ background: 'linear-gradient(135deg, rgba(254,183,0,0.4), rgba(152,203,255,0.4))' }} />
                  <span className="material-symbols-outlined absolute text-4xl text-[#e5e2e3]">hub</span>
                </div>
              </div>
            </div>

            {/* ── Bottom Metric Cards ── */}
            <div className="grid grid-cols-4 gap-4 mt-auto">
              <MetricCard label="Entities Extracted" value={summary ? summary.total_entities.toLocaleString() : 'Loading...'} color="#98cbff" />
              <MetricCard label="Relationships Mapped" value={summary ? summary.total_relations.toLocaleString() : 'Loading...'} color="#ffdb9d" />
              <MetricCard label="Suspicious Clusters" value={summary ? summary.total_alerts.toString() : 'Loading...'} color="#ff6e68" />
              <MetricCard label="Max Risk Actor" value={summary ? summary.max_risk_suspect : 'Loading...'} color="#ffb4ab" />
            </div>
          </div>

          {/* ── RIGHT PANEL: Live Intelligence Logs ── */}
          <div className="w-80 glass-panel-blue rounded-xl flex flex-col z-10 overflow-hidden">
            <div className="p-4 bg-[#201f20] border-b border-[#3f4852]/30 flex justify-between items-center">
              <h3 className="uppercase tracking-widest" style={{ fontFamily: 'JetBrains Mono', fontSize: '14px', fontWeight: '500' }}>Intelligence Logs</h3>
              <div className="flex gap-1">
                <span className="w-1 h-1 bg-[#98cbff] rounded-full" />
                <span className="w-1 h-1 bg-[#98cbff] rounded-full opacity-50" />
                <span className="w-1 h-1 bg-[#98cbff] rounded-full opacity-20" />
              </div>
            </div>

            {/* Log Feed */}
            <div
              id="logs-feed"
              className="flex-grow p-3 space-y-2 log-container overflow-y-auto"
              style={{ fontFamily: 'JetBrains Mono', fontSize: '11px' }}
            >
              <div className="flex gap-2"><span style={{ color: '#bec7d4' }}>[14:02:11]</span><span style={{ color: '#98cbff' }}>INIT</span><span>Knowledge extraction phase 4...</span></div>
              <div className="flex gap-2"><span style={{ color: '#bec7d4' }}>[14:02:12]</span><span style={{ color: '#feb700' }}>LINK</span><span>Entity ID #8410 connected to Root Cluster</span></div>
              <div className="flex gap-2"><span style={{ color: '#bec7d4' }}>[14:02:15]</span><span style={{ color: '#ffb3ae' }}>RESOLVE</span><span>Multiple alias detected for Node_Beta</span></div>
              <div className="flex gap-2 p-1 border-l-2 border-[#ffb4ab]" style={{ background: 'rgba(255,180,171,0.1)' }}>
                <span style={{ color: '#bec7d4' }}>[14:02:18]</span><span style={{ color: '#ffb4ab', fontWeight: 'bold' }}>ALERT</span><span>Circularity detected in Transaction Flow A-01</span>
              </div>
              <div className="flex gap-2"><span style={{ color: '#bec7d4' }}>[14:02:20]</span><span style={{ color: '#98cbff' }}>INFO</span><span>Temporal reconstruction stabilized (T+4h)</span></div>
              <div className="flex gap-2"><span style={{ color: '#bec7d4' }}>[14:02:22]</span><span style={{ color: '#feb700' }}>GEO</span><span>Mapping location data from Metadata Packets</span></div>
              <div className="flex gap-2"><span style={{ color: '#bec7d4' }}>[14:02:25]</span><span style={{ color: '#98cbff' }}>INIT</span><span>Parsing encrypted buffer 0x4F...</span></div>
              <div className="flex gap-2"><span style={{ color: '#bec7d4' }}>[14:02:28]</span><span style={{ color: '#feb700' }}>MATCH</span><span>Biometric signature overlap (98.2%)</span></div>
              <div className="flex gap-2"><span style={{ color: '#bec7d4' }}>[14:02:30]</span><span style={{ color: '#98cbff' }}>STREAM</span><span>Processing packet stream 184-B...</span></div>
              <div className="flex gap-2"><span style={{ color: '#bec7d4' }}>[14:02:32]</span><span style={{ color: '#feb700' }}>ENTITY</span><span>Discovered hidden sub-group: 'NEXUS'</span></div>
            </div>

            {/* Mini Radar */}
            <div className="h-32 bg-[#1c1b1c] border-t border-[#3f4852]/30 relative overflow-hidden p-2">
              <div className="w-full h-full border border-[#98cbff]/20 rounded-lg relative overflow-hidden flex items-center justify-center">
                <div className="w-full h-px bg-[#98cbff]/20 absolute top-1/2" />
                <div className="h-full w-px bg-[#98cbff]/20 absolute left-1/2" />
                <div className="w-24 h-24 border border-[#98cbff]/10 rounded-full absolute" />
                <div className="w-16 h-16 border border-[#98cbff]/10 rounded-full absolute" />
                <div className="w-1.5 h-1.5 bg-[#ffb4ab] rounded-full absolute animate-pulse" style={{ top: '25%', left: '33%' }} />
                <div className="w-1 h-1 bg-[#feb700] rounded-full absolute" style={{ bottom: '25%', right: '25%' }} />
                <div className="absolute inset-0 bg-gradient-to-t from-[#0a0a0b] to-transparent opacity-40" />
              </div>
            </div>
          </div>
        </div>

        {/* ── FOOTER STATUS BAR ── */}
        <footer className="h-8 border-t border-[#3f4852]/10 px-6 flex items-center justify-between uppercase tracking-widest z-20"
          style={{ background: '#0e0e0f', fontFamily: 'JetBrains Mono', fontSize: '10px', color: '#bec7d4' }}>
          <div className="flex gap-6">
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 bg-[#feb700] rounded-full" /> RECONSTRUCTION ENGINE: STABLE
            </span>
            <span>CPU LOAD: 42%</span>
            <span>GPU UTIL: 89%</span>
          </div>
          <div className="flex gap-4">
            <span>ENCRYPTION: AES-256-GCM</span>
            <span style={{ color: '#98cbff' }}>SESSION_ID: TATVA-01-RECON</span>
          </div>
        </footer>
      </main>
    </div>
  )
}

function PipelineStage({ color, label, sublabel, status }: { color: string; label: string; sublabel: string; status: 'active' | 'processing' | 'pending' | 'error' }) {
  return (
    <div className={`flex items-start gap-3 ${status !== 'active' ? 'opacity-50' : ''}`}>
      <div className="mt-1 w-2 h-2 rounded-full flex-shrink-0"
        style={{ background: color, boxShadow: status === 'active' ? `0 0 8px ${color}` : 'none' }} />
      <div className="flex-grow border-l border-[#3f4852]/30 pl-4 pb-4">
        <p style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: status === 'error' ? '#ffb4ab' : status === 'active' ? color : '#e5e2e3' }}>{label}</p>
        {sublabel && <span style={{ fontFamily: 'JetBrains Mono', fontSize: '10px', color: '#bec7d4' }}>{sublabel}</span>}
      </div>
    </div>
  )
}

function MetricCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="glass-panel-blue p-4 rounded-xl" style={{ borderLeft: `2px solid ${color}` }}>
      <p className="uppercase" style={{ fontFamily: 'JetBrains Mono', fontSize: '10px', color: '#bec7d4' }}>{label}</p>
      <h4 className="mt-1" style={{ fontFamily: 'Geist', fontSize: '24px', fontWeight: '600', color }}>{value}</h4>
    </div>
  )
}
