import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

// ====================================================================
// TATVA | Case File Initialization
// Stitch screen: e51101a195104961b26a638bab7f14a8
// Layout: Fixed TopNav + Fixed SideNav + Scrollable main
// Colors: Blue primary (#98cbff), Amber accent (#feb700)
// ====================================================================

export default function CaseFilePage() {
  const navigate = useNavigate()
  const [configs, setConfigs] = useState({
    anomaly: true,
    gnn: false,
    intel: true,
    temporal: true,
  })

  const toggleConfig = (key: keyof typeof configs) => {
    setConfigs(prev => ({ ...prev, [key]: !prev[key] }))
  }

  return (
    <div style={{ background: '#131314', color: '#e5e2e3', fontFamily: 'Geist, sans-serif', minHeight: '100vh' }}>

      {/* ── FIXED TOP NAV ── */}
      <header className="fixed top-0 z-50 w-full flex justify-between items-center h-16 border-b border-[#3f4852]/30"
        style={{ background: 'rgba(19,19,20,0.8)', backdropFilter: 'blur(16px)', padding: '0 32px' }}>
        <div className="flex items-center gap-8">
          <span
            className="font-black tracking-widest cursor-pointer"
            onClick={() => navigate('/')}
            style={{ fontFamily: 'Geist', fontSize: '40px', fontWeight: '900', color: '#feb700', letterSpacing: '0.1em' }}
          >
            TATVA
          </span>
          <nav className="hidden md:flex gap-6">
            {['Dashboard', 'Analytics', 'Reports', 'Logs'].map(l => (
              <a key={l} href="#" className="font-medium hover:text-[#ffdb9d] transition-colors duration-200"
                style={{ color: '#bec7d4', fontFamily: 'Geist', fontSize: '16px' }}>{l}</a>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-4">
          <div className="relative hidden lg:block">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[#bec7d4]">search</span>
            <input
              type="text"
              placeholder="Search case repository..."
              className="border border-[#3f4852]/30 rounded-lg pl-10 pr-4 py-1.5 focus:ring-1 focus:ring-[#feb700] focus:border-[#feb700] outline-none w-64 transition-all"
              style={{ background: '#1c1b1c', color: '#e5e2e3', fontFamily: 'Geist', fontSize: '14px' }}
            />
          </div>
          <button className="material-symbols-outlined hover:text-[#ffdb9d] transition-colors scale-95 active:scale-90" style={{ color: '#bec7d4' }}>notifications</button>
          <button className="material-symbols-outlined hover:text-[#ffdb9d] transition-colors scale-95 active:scale-90" style={{ color: '#bec7d4' }}>settings</button>
          <div className="h-8 w-8 rounded-full overflow-hidden border border-[#3f4852]">
            <img src="/assets/avatars/investigator-3.jpg" alt="Profile" className="w-full h-full object-cover" />
          </div>
        </div>
      </header>

      <div className="flex" style={{ minHeight: '100vh', paddingTop: '64px' }}>

        {/* ── FIXED SIDE NAV ── */}
        <aside className="fixed left-0 flex flex-col border-r border-[#3f4852]/20 hidden md:flex"
          style={{ top: '64px', height: 'calc(100vh - 64px)', width: '256px', background: 'rgba(28,27,28,0.9)', backdropFilter: 'blur(12px)', padding: '24px 0' }}>
          <div className="px-6 mb-8">
            <div className="flex items-center gap-3 mb-1">
              <span className="material-symbols-outlined" style={{ color: '#feb700', fontVariationSettings: "'FILL' 1" }}>security</span>
              <span style={{ fontFamily: 'Geist', fontSize: '24px', fontWeight: '600', color: '#e5e2e3' }}>Unit 01</span>
            </div>
            <p className="uppercase tracking-wider" style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#bec7d4' }}>Forensic Division</p>
          </div>

          <nav className="flex-1">
            <ul className="space-y-1">
              {[
                { icon: 'folder_open', label: 'Evidence Vault', path: '/evidence', active: false },
                { icon: 'hub', label: 'Entity Graph', path: '/investigation', active: false },
                { icon: 'description', label: 'Case Files', path: '/case/new', active: true },
                { icon: 'smart_card_reader', label: 'Digital Forensics', path: '/forensics', active: false },
                { icon: 'history', label: 'Timeline', path: '/reconstruction', active: false },
              ].map(item => (
                <li key={item.path}>
                  <a
                    href="#"
                    onClick={(e) => { e.preventDefault(); navigate(item.path) }}
                    className={`flex items-center gap-3 px-6 py-3 transition-all duration-300 ${item.active
                      ? 'border-r-4 border-[#feb700]'
                      : 'text-[#bec7d4] hover:text-[#e5e2e3]'
                    }`}
                    style={item.active ? { background: 'rgba(254,183,0,0.1)', color: '#ffdb9d' } : {}}
                  >
                    <span className="material-symbols-outlined">{item.icon}</span>
                    <span className="uppercase tracking-wider" style={{ fontFamily: 'JetBrains Mono', fontSize: '14px', fontWeight: '500' }}>{item.label}</span>
                  </a>
                </li>
              ))}
            </ul>
          </nav>

          <div className="px-6 mt-auto">
            <button
              onClick={() => navigate('/case/new')}
              className="w-full rounded-lg font-bold flex items-center justify-center gap-2 hover:opacity-90 transition-opacity mb-8 py-3"
              style={{ background: '#feb700', color: '#6b4b00' }}
            >
              <span className="material-symbols-outlined">add</span>
              <span>New Investigation</span>
            </button>
            <ul className="space-y-1 opacity-70">
              <li><a href="#" className="flex items-center gap-3 text-[#bec7d4] py-2 hover:text-[#e5e2e3] transition-colors">
                <span className="material-symbols-outlined">help</span><span style={{ fontSize: '12px' }}>Help Center</span></a></li>
              <li><a href="#" className="flex items-center gap-3 text-[#bec7d4] py-2 hover:text-[#e5e2e3] transition-colors">
                <span className="material-symbols-outlined">analytics</span><span style={{ fontSize: '12px' }}>System Status</span></a></li>
            </ul>
          </div>
        </aside>

        {/* ── MAIN SCROLLABLE CONTENT ── */}
        <main className="flex-1 md:ml-64" style={{ padding: '32px', background: 'linear-gradient(135deg, #0a0a0b 0%, transparent 40%), #131314' }}>
          {/* Page Header */}
          <header className="mb-10 flex justify-between items-end">
            <div>
              <h1 style={{ fontFamily: 'Geist', fontSize: '32px', fontWeight: '600', lineHeight: '40px', letterSpacing: '-0.01em', color: '#e5e2e3', marginBottom: '8px' }}>
                Initialize Case Core
              </h1>
              <div className="flex items-center gap-4 uppercase tracking-widest" style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#bec7d4' }}>
                <span className="flex items-center gap-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-[#ffdb9d]" /> SESSION: ACTIVE
                </span>
                <span>|</span>
                <span className="flex items-center gap-1">
                  <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>encrypted</span> ENCRYPTION: AES-256
                </span>
              </div>
            </div>
            <div className="flex gap-4">
              <button className="px-6 py-2 rounded border border-[#3f4852] text-[#e5e2e3] hover:bg-[#353436]/20 transition-all font-medium">
                DISCARD
              </button>
              <button
                onClick={() => navigate('/reconstruction')}
                className="px-8 py-2 rounded font-bold transition-all"
                style={{ background: '#98cbff', color: '#003354', boxShadow: '0 0 20px rgba(152,203,255,0.1)' }}
              >
                INITIALIZE UNIT
              </button>
            </div>
          </header>

          {/* 12-col Grid */}
          <div className="grid grid-cols-12 gap-4">

            {/* Left: 8 cols — Case Metadata + Evidence + Config */}
            <div className="col-span-12 lg:col-span-8 space-y-4">

              {/* ── Case Metadata Panel ── */}
              <section className="glass-panel p-6 rounded-xl relative overflow-hidden amber-glow">
                <div className="absolute top-4 right-4 opacity-40" style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#ffdb9d' }}>MDL-84.INTAKE</div>
                <h2 className="flex items-center gap-2 mb-6" style={{ fontFamily: 'Geist', fontSize: '24px', fontWeight: '600', color: '#feb700' }}>
                  <span className="material-symbols-outlined">fact_check</span> Metadata Parameters
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Case Name */}
                  <div className="space-y-1.5">
                    <label className="uppercase" style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#bec7d4' }}>Case Name</label>
                    <input
                      type="text"
                      placeholder="e.g., OPERATION_STORM_WATCH"
                      className="w-full border border-[#3f4852]/40 rounded px-4 py-2.5 focus:border-[#feb700] outline-none transition-all"
                      style={{ background: '#0e0e0f', color: '#e5e2e3', fontFamily: 'JetBrains Mono', fontSize: '14px', fontWeight: '500' }}
                    />
                  </div>

                  {/* Investigation Type */}
                  <div className="space-y-1.5">
                    <label className="uppercase" style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#bec7d4' }}>Investigation Type</label>
                    <select
                      className="w-full border border-[#3f4852]/40 rounded px-4 py-2.5 focus:border-[#feb700] outline-none transition-all"
                      style={{ background: '#0e0e0f', color: '#e5e2e3', fontFamily: 'JetBrains Mono', fontSize: '14px', fontWeight: '500' }}
                    >
                      <option>Cyber Forensics</option>
                      <option>Financial Audit</option>
                      <option>Network Intrusion</option>
                      <option>Threat Intelligence</option>
                    </select>
                  </div>

                  {/* Incident Date */}
                  <div className="space-y-1.5">
                    <label className="uppercase" style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#bec7d4' }}>Incident Date</label>
                    <input
                      type="date"
                      className="w-full border border-[#3f4852]/40 rounded px-4 py-2.5 focus:border-[#feb700] outline-none transition-all"
                      style={{ background: '#0e0e0f', color: '#e5e2e3', fontFamily: 'JetBrains Mono', fontSize: '14px', fontWeight: '500' }}
                    />
                  </div>

                  {/* Priority Level */}
                  <div className="space-y-1.5">
                    <label className="uppercase" style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#bec7d4' }}>Priority Level</label>
                    <div className="flex gap-2">
                      {['LOW', 'CRITICAL', 'IMMEDIATE'].map(level => (
                        <button
                          key={level}
                          className="flex-1 py-2 border rounded font-bold transition-all"
                          style={{
                            fontFamily: 'JetBrains Mono',
                            fontSize: '12px',
                            background: level === 'CRITICAL' ? 'rgba(254,183,0,0.1)' : 'transparent',
                            color: level === 'CRITICAL' ? '#ffdb9d' : '#bec7d4',
                            border: level === 'CRITICAL' ? '1px solid rgba(254,183,0,0.4)' : '1px solid rgba(63,72,82,0.4)',
                          }}
                        >
                          {level}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Investigator Notes */}
                  <div className="col-span-full space-y-1.5">
                    <label className="uppercase" style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#bec7d4' }}>Investigator Notes</label>
                    <textarea
                      rows={3}
                      placeholder="Entry technical observations or preliminary hypotheses..."
                      className="w-full border border-[#3f4852]/40 rounded px-4 py-2.5 focus:border-[#feb700] outline-none transition-all resize-none"
                      style={{ background: '#0e0e0f', color: '#e5e2e3', fontFamily: 'Geist', fontSize: '14px' }}
                    />
                  </div>
                </div>
              </section>

              {/* ── Evidence Upload Section ── */}
              <section className="glass-panel p-6 rounded-xl">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="flex items-center gap-2 mb-0" style={{ fontFamily: 'Geist', fontSize: '24px', fontWeight: '600', color: '#98cbff' }}>
                    <span className="material-symbols-outlined">cloud_upload</span> Evidence Intake
                  </h2>
                  <span className="px-3 py-1 rounded-full" style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#bec7d4', background: '#353436' }}>
                    SUPPORTED: CSV, JSON, PDF, JPG, LOG
                  </span>
                </div>

                {/* Drop Zone */}
                <div className="border-2 border-dashed border-[#3f4852]/30 rounded-xl p-10 flex flex-col items-center justify-center group hover:border-[#98cbff]/40 transition-all cursor-pointer"
                  style={{ background: 'rgba(28,27,28,0.3)' }}>
                  <span className="material-symbols-outlined mb-4 group-hover:text-[#98cbff] transition-colors" style={{ fontSize: '64px', color: '#3f4852' }}>move_to_inbox</span>
                  <p className="font-semibold mb-2" style={{ fontFamily: 'Geist', fontSize: '18px', color: '#e5e2e3' }}>Drop forensic payload here</p>
                  <p style={{ fontFamily: 'Geist', fontSize: '14px', color: '#bec7d4' }}>
                    or <span className="hover:underline cursor-pointer" style={{ color: '#98cbff' }}>browse files</span> for ingestion
                  </p>
                </div>

                {/* Progress Indicators */}
                <div className="mt-6 space-y-4">
                  {/* File 1 — Parsing */}
                  <div className="border border-[#3f4852]/20 rounded p-4 flex items-center gap-4" style={{ background: '#0e0e0f' }}>
                    <span className="material-symbols-outlined" style={{ color: '#ffdb9d' }}>database</span>
                    <div className="flex-1">
                      <div className="flex justify-between mb-1.5" style={{ fontFamily: 'JetBrains Mono', fontSize: '12px' }}>
                        <span className="font-bold">ENTITY_RELATION_DUMP.JSON</span>
                        <span style={{ color: '#ffdb9d' }}>PARSING... 84%</span>
                      </div>
                      <div className="w-full h-1 bg-[#353436] rounded-full overflow-hidden">
                        <div className="h-full animate-pulse" style={{ width: '84%', background: '#feb700' }} />
                      </div>
                    </div>
                    <span className="material-symbols-outlined cursor-pointer hover:text-[#ffb4ab]" style={{ color: '#bec7d4' }}>close</span>
                  </div>

                  {/* File 2 — Queued */}
                  <div className="border border-[#3f4852]/20 rounded p-4 flex items-center gap-4 opacity-60" style={{ background: '#0e0e0f' }}>
                    <span className="material-symbols-outlined" style={{ color: '#98cbff' }}>description</span>
                    <div className="flex-1">
                      <div className="flex justify-between mb-1.5" style={{ fontFamily: 'JetBrains Mono', fontSize: '12px' }}>
                        <span className="font-bold">SUSPECT_INTERVIEW_04.PDF</span>
                        <span style={{ color: '#bec7d4' }}>QUEUED</span>
                      </div>
                      <div className="w-full h-1 bg-[#353436] rounded-full" />
                    </div>
                    <span className="material-symbols-outlined cursor-pointer" style={{ color: '#bec7d4' }}>close</span>
                  </div>
                </div>
              </section>

              {/* ── Cognitive Configuration ── */}
              <section className="glass-panel p-6 rounded-xl">
                <h2 className="flex items-center gap-2 mb-6" style={{ fontFamily: 'Geist', fontSize: '24px', fontWeight: '600', color: '#e5e2e3' }}>
                  <span className="material-symbols-outlined">settings_input_component</span> Cognitive Configuration
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {[
                    { key: 'anomaly', label: 'Anomaly Detection', sub: 'Heuristic pattern mismatch trigger' },
                    { key: 'gnn', label: 'GNN Inference', sub: 'Graph Neural Network link prediction' },
                    { key: 'intel', label: 'Intel Matching', sub: 'Auto-cross-reference known records' },
                    { key: 'temporal', label: 'Temporal Recon', sub: '4D causality mapping of evidence' },
                  ].map(item => (
                    <label
                      key={item.key}
                      className="flex items-center justify-between p-4 border border-[#3f4852]/20 rounded hover:border-[#feb700]/30 transition-all cursor-pointer group"
                      style={{ background: '#1c1b1c' }}
                    >
                      <div className="flex flex-col">
                        <span className="font-semibold" style={{ fontFamily: 'Geist', fontSize: '16px', color: '#e5e2e3' }}>{item.label}</span>
                        <span style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#bec7d4' }}>{item.sub}</span>
                      </div>
                      <div className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          className="sr-only peer"
                          checked={configs[item.key as keyof typeof configs]}
                          onChange={() => toggleConfig(item.key as keyof typeof configs)}
                        />
                        <div
                          onClick={() => toggleConfig(item.key as keyof typeof configs)}
                          className="w-11 h-6 rounded-full relative transition-colors"
                          style={{ background: configs[item.key as keyof typeof configs] ? '#feb700' : '#353436' }}
                        >
                          <div
                            className="absolute top-0.5 h-5 w-5 rounded-full bg-white transition-transform"
                            style={{ left: '2px', transform: configs[item.key as keyof typeof configs] ? 'translateX(20px)' : 'translateX(0)' }}
                          />
                        </div>
                      </div>
                    </label>
                  ))}
                </div>
              </section>
            </div>

            {/* Right: 4 cols — Intelligence Hub */}
            <div className="col-span-12 lg:col-span-4 space-y-4">
              <section className="glass-panel p-6 rounded-xl h-full flex flex-col">
                <h2 className="flex items-center gap-2 mb-2" style={{ fontFamily: 'Geist', fontSize: '24px', fontWeight: '600', color: '#e5e2e3' }}>
                  <span className="material-symbols-outlined">auto_graph</span> Intelligence Hub
                </h2>
                <p className="uppercase tracking-widest border-b border-[#3f4852]/20 pb-4 mb-6" style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#bec7d4' }}>
                  Real-time Historical Correlation
                </p>

                <div className="space-y-6 overflow-y-auto custom-scrollbar" style={{ maxHeight: '800px' }}>
                  {/* Related Cases */}
                  <div className="group">
                    <h3 className="font-bold flex items-center justify-between mb-3" style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#ffdb9d' }}>
                      POTENTIAL RELATED CASES
                      <span className="material-symbols-outlined group-hover:rotate-45 transition-transform" style={{ fontSize: '16px' }}>north_east</span>
                    </h3>
                    <div className="space-y-3">
                      {/* Case 1 */}
                      <div className="p-4 border border-[#3f4852]/30 rounded hover:border-[#feb700]/50 transition-all cursor-pointer" style={{ background: '#0e0e0f' }}>
                        <div className="flex justify-between items-start mb-2">
                          <span className="font-bold" style={{ fontFamily: 'Geist', fontSize: '14px', color: '#e5e2e3' }}>CASE_#8922-GAMMA</span>
                          <span className="px-2 py-0.5 rounded font-bold" style={{ background: '#93000a', color: '#ffdad6', fontSize: '10px' }}>92% MATCH</span>
                        </div>
                        <p style={{ fontFamily: 'Geist', fontSize: '14px', color: '#bec7d4', marginBottom: '8px' }}>
                          Pattern: Repeated SQL injection via localized gateway #14.
                        </p>
                        <div className="flex gap-2">
                          <span className="px-1.5 py-0.5 border border-[#3f4852]/30" style={{ fontFamily: 'JetBrains Mono', fontSize: '10px', color: '#bec7d4' }}>TAG: NETWORK</span>
                          <span className="px-1.5 py-0.5 border border-[#3f4852]/30" style={{ fontFamily: 'JetBrains Mono', fontSize: '10px', color: '#bec7d4' }}>ID: AX-9</span>
                        </div>
                      </div>
                      {/* Case 2 */}
                      <div className="p-4 border border-[#3f4852]/30 rounded hover:border-[#feb700]/50 transition-all cursor-pointer" style={{ background: '#0e0e0f' }}>
                        <div className="flex justify-between items-start mb-2">
                          <span className="font-bold" style={{ fontFamily: 'Geist', fontSize: '14px', color: '#e5e2e3' }}>CASE_#1104-OMEGA</span>
                          <span className="px-2 py-0.5 rounded font-bold" style={{ background: 'rgba(254,183,0,0.2)', color: '#ffdb9d', fontSize: '10px' }}>45% MATCH</span>
                        </div>
                        <p style={{ fontFamily: 'Geist', fontSize: '14px', color: '#bec7d4' }}>Subject profile overlap in 'Encrypted Comm' sub-sector.</p>
                      </div>
                    </div>
                  </div>

                  {/* Known Entity Overlap */}
                  <div>
                    <h3 className="font-bold mb-3" style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#98cbff' }}>KNOWN ENTITY OVERLAP</h3>
                    <div className="flex flex-wrap gap-2">
                      {[
                        { label: 'IP_192.168.0.XX', color: '#98cbff', pulse: false },
                        { label: 'UID: "GHOST_R"', color: '#ffb4ab', pulse: true },
                        { label: 'MAC: FA-04-11', color: '#ffdb9d', pulse: false },
                      ].map(entity => (
                        <div key={entity.label} className="flex items-center gap-2 px-3 py-1.5 border border-[#3f4852]/30 rounded-full cursor-help"
                          style={{ background: '#2a2a2b' }}>
                          <div className={`w-2 h-2 rounded-full ${entity.pulse ? 'animate-pulse' : ''}`}
                            style={{ background: entity.color, boxShadow: `0 0 5px ${entity.color}80` }} />
                          <span style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#e5e2e3' }}>{entity.label}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Risk Heatmap */}
                  <div className="space-y-3">
                    <h3 className="uppercase font-bold mb-3" style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#bec7d4' }}>Regional Risk Heatmap</h3>
                    <div className="rounded-lg overflow-hidden border border-[#3f4852]/20 group relative cursor-crosshair" style={{ aspectRatio: '16/9' }}>
                      <img
                        src="/assets/risk-heatmap.jpg"
                        alt="City risk heatmap"
                        className="w-full h-full object-cover grayscale group-hover:grayscale-0 group-hover:scale-105 transition-all duration-700"
                        style={{ opacity: 0.6 }}
                      />
                      {/* Ping locator */}
                      <div className="absolute inset-0 flex items-center justify-center">
                        <div className="w-12 h-12 border border-[#feb700]/50 rounded-full flex items-center justify-center animate-ping" />
                        <div className="absolute w-12 h-12 border border-[#feb700]/20 rounded-full flex items-center justify-center">
                          <span className="material-symbols-outlined" style={{ color: '#feb700' }}>location_searching</span>
                        </div>
                      </div>
                      <div className="absolute bottom-2 left-2 px-2 py-1 rounded backdrop-blur" style={{ background: 'rgba(10,10,11,0.8)', fontFamily: 'JetBrains Mono', fontSize: '10px', color: '#ffdb9d' }}>
                        COORDS: 40.7128° N, 74.0060° W
                      </div>
                    </div>
                  </div>

                  {/* Risk Gauge */}
                  <div className="p-6 rounded-xl border border-[#feb700]/10 flex flex-col items-center" style={{ background: 'rgba(28,27,28,0.5)' }}>
                    <div className="relative w-32 h-32 flex items-center justify-center mb-4">
                      <svg className="w-full h-full -rotate-90">
                        <circle cx="64" cy="64" r="58" fill="transparent" stroke="#353436" strokeWidth="8" />
                        <circle
                          cx="64" cy="64" r="58" fill="transparent"
                          stroke="#feb700" strokeWidth="8"
                          strokeDasharray="364.4" strokeDashoffset="100"
                          style={{ filter: 'drop-shadow(0 0 10px rgba(254,183,0,0.5))' }}
                        />
                      </svg>
                      <div className="absolute inset-0 flex flex-col items-center justify-center">
                        <span className="font-bold" style={{ fontFamily: 'Geist', fontSize: '24px', fontWeight: '600', color: '#ffdb9d' }}>72</span>
                        <span style={{ fontFamily: 'JetBrains Mono', fontSize: '10px', color: '#bec7d4' }}>RISK INDEX</span>
                      </div>
                    </div>
                    <p className="text-center italic" style={{ fontFamily: 'Geist', fontSize: '14px', color: '#bec7d4' }}>
                      "Current parameters suggest elevated systemic volatility."
                    </p>
                  </div>
                </div>

                {/* View Intel Report */}
                <div className="mt-auto pt-6 border-t border-[#3f4852]/20">
                  <button
                    onClick={() => navigate('/investigation')}
                    className="w-full py-3 rounded border border-[#98cbff]/40 font-bold hover:bg-[#98cbff]/10 transition-all flex items-center justify-center gap-2"
                    style={{ color: '#98cbff', fontFamily: 'Geist', fontSize: '14px' }}
                  >
                    <span className="material-symbols-outlined">analytics</span> VIEW FULL INTEL REPORT
                  </button>
                </div>
              </section>
            </div>
          </div>
        </main>
      </div>

      {/* Mobile Nav */}
      <nav className="md:hidden fixed bottom-0 left-0 w-full h-16 border-t border-[#3f4852]/30 flex justify-around items-center px-4 z-50"
        style={{ background: 'rgba(28,27,28,0.95)', backdropFilter: 'blur(16px)' }}>
        {[
          { icon: 'dashboard', label: 'HOME' },
          { icon: 'description', label: 'CASES', active: true },
          { icon: 'hub', label: 'GRAPH' },
          { icon: 'person', label: 'PROFILE' },
        ].map(item => (
          <button key={item.label} className="flex flex-col items-center gap-1" style={{ color: item.active ? '#ffdb9d' : '#bec7d4' }}>
            <span className="material-symbols-outlined" style={item.active ? { fontVariationSettings: "'FILL' 1" } : {}}>{item.icon}</span>
            <span className="text-[10px] font-bold">{item.label}</span>
          </button>
        ))}
      </nav>
    </div>
  )
}
