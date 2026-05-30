import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

// ====================================================================
// TATVA | Investigation Analysis Console
// Stitch screen: 874c9b67e93441d9b66890e4075bba9a
// Layout: TopNav + SideNav (Left 288px) + Graph (Center) + Right Panel (384px)
// overflow: hidden — full viewport
// ====================================================================

import ForceGraphKnowledgeGraph from '../components/ForceGraphKnowledgeGraph'

type TabType = 'EXPLAINABILITY' | 'TIMELINE' | 'ASSISTANT'

export default function InvestigationPage() {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<TabType>('EXPLAINABILITY')
  const [suspects, setSuspects] = useState<any[]>([])
  const [selectedEntity, setSelectedEntity] = useState<any>(null)

  useEffect(() => {
    fetch('http://localhost:8000/api/insights/suspects')
      .then(res => res.json())
      .then(data => setSuspects(data))
      .catch(err => console.error('Failed to fetch suspects', err))
  }, [])

  return (
    <div className="scanline-grid overflow-hidden" style={{ background: '#0a0a0b', color: '#e5e2e3', fontFamily: 'Geist, sans-serif', height: '100vh', display: 'flex', flexDirection: 'column' }}>

      {/* ── TOP NAV BAR ── */}
      <header className="flex justify-between items-center w-full h-16 border-b border-[#3f4852]/30 z-50 flex-shrink-0"
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
            <a href="#" className="font-medium hover:text-[#ffdb9d] transition-colors duration-200" style={{ color: '#bec7d4', fontFamily: 'Geist', fontSize: '16px' }}>Dashboard</a>
            <a href="#" className="font-bold border-b-2 border-[#feb700] pb-1 transition-colors duration-200" style={{ color: '#ffdb9d', fontFamily: 'Geist', fontSize: '16px' }}>Analytics</a>
            <a href="#" className="font-medium hover:text-[#ffdb9d] transition-colors duration-200" style={{ color: '#bec7d4', fontFamily: 'Geist', fontSize: '16px' }}>Reports</a>
            <a href="#" className="font-medium hover:text-[#ffdb9d] transition-colors duration-200" style={{ color: '#bec7d4', fontFamily: 'Geist', fontSize: '16px' }}>Logs</a>
          </nav>
        </div>
        <div className="flex items-center gap-4">
          <div className="relative group">
            <span className="material-symbols-outlined cursor-pointer hover:text-[#ffdb9d] transition-transform scale-95 active:scale-90" style={{ color: '#bec7d4' }}>notifications</span>
            <div className="absolute top-0 right-0 w-2 h-2 bg-[#ffb4ab] rounded-full border-2 border-[#131314]" />
          </div>
          <span className="material-symbols-outlined cursor-pointer hover:text-[#ffdb9d] transition-transform scale-95 active:scale-90" style={{ color: '#bec7d4' }}>settings</span>
          <div className="flex items-center gap-2 pl-4 border-l border-[#3f4852]/30">
            <img src="/assets/avatars/investigator-2.jpg" alt="Profile" className="w-8 h-8 rounded-full border border-[#feb700]/30 object-cover" />
            <span className="hidden lg:block" style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#bec7d4' }}>ID-9422 // AGENT</span>
          </div>
        </div>
      </header>

      {/* ── MAIN WORKSPACE ── */}
      <div className="flex flex-1 overflow-hidden" style={{ height: 'calc(100vh - 64px)' }}>

        {/* ── LEFT SIDEBAR: Entity Navigator ── */}
        <aside className="w-72 flex flex-col border-r border-[#3f4852]/20 z-40 flex-shrink-0"
          style={{ background: 'rgba(28,27,28,0.9)', backdropFilter: 'blur(12px)', padding: '24px 0' }}>
          <div className="px-6 mb-8">
            <div className="flex items-center gap-3 mb-2">
              <span className="material-symbols-outlined text-[#e5e2e3]">shield</span>
              <div>
                <div style={{ fontFamily: 'Geist', fontSize: '24px', fontWeight: '600', color: '#e5e2e3' }}>Unit 01</div>
                <div style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#bec7d4' }} className="uppercase">Forensic Division</div>
              </div>
            </div>
            <button
              onClick={() => navigate('/case/new')}
              className="w-full mt-6 border border-[#feb700]/30 py-3 flex items-center justify-center gap-2 transition-all duration-300 hover:bg-[#feb700]/10"
              style={{ color: '#ffdb9d', background: 'rgba(254,183,0,0.05)' }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>add</span>
              <span style={{ fontFamily: 'JetBrains Mono', fontSize: '14px', fontWeight: '500' }} className="uppercase tracking-wider">New Investigation</span>
            </button>
          </div>

          {/* Search */}
          <div className="flex-1 overflow-y-auto space-y-1">
            <div className="px-6 py-2">
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[#bec7d4]" style={{ fontSize: '18px' }}>search</span>
                <input
                  type="text"
                  placeholder="SEARCH ENTITIES..."
                  className="w-full bg-[#353436]/50 border-none outline-none py-2 pl-10 text-[#e5e2e3] placeholder:text-[#bec7d4]/50 focus:ring-1 focus:ring-[#feb700]/50"
                  style={{ fontFamily: 'JetBrains Mono', fontSize: '12px' }}
                />
              </div>
            </div>

            {/* Nav Items */}
            {[
              { icon: 'hub', label: 'Entity Graph', path: '/investigation', active: true, badge: 'LIVE' },
              { icon: 'groups', label: 'People', path: '/people', active: false },
              { icon: 'account_balance', label: 'Accounts', path: '/accounts', active: false },
              { icon: 'location_on', label: 'Locations', path: '/locations', active: false },
              { icon: 'devices', label: 'Devices', path: '/devices', active: false },
            ].map(item => (
              <a
                key={item.path}
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
                {item.badge && (
                  <span className="ml-auto px-1.5 py-0.5 rounded-sm text-[10px] font-bold" style={{ background: '#feb700', color: '#412d00' }}>
                    {item.badge}
                  </span>
                )}
              </a>
            ))}
          </div>

          {/* Footer links */}
          <div className="mt-auto pt-4 border-t border-[#3f4852]/20">
            <a href="#" className="flex items-center gap-3 text-[#bec7d4] px-6 py-2 hover:text-[#e5e2e3] transition-colors">
              <span className="material-symbols-outlined text-sm">help</span>
              <span style={{ fontFamily: 'JetBrains Mono', fontSize: '12px' }} className="uppercase tracking-widest">Help Center</span>
            </a>
            <a href="#" className="flex items-center gap-3 text-[#bec7d4] px-6 py-2 hover:text-[#e5e2e3] transition-colors">
              <span className="material-symbols-outlined text-sm">analytics</span>
              <span style={{ fontFamily: 'JetBrains Mono', fontSize: '12px' }} className="uppercase tracking-widest">System Status</span>
            </a>
          </div>
        </aside>

        {/* ── CENTER: 3D Knowledge Graph Space ── */}
        <main className="flex-1 relative overflow-hidden scanline-grid">
          {/* 3D Force Knowledge Graph — data from GET /graph/render */}
          <div className="absolute inset-0 z-0">
            <ForceGraphKnowledgeGraph onNodeClick={(node) => setSelectedEntity(node)} />
          </div>

          {/* ── Temporal Controls (Bottom) ── */}
          <div className="absolute left-1/2 -translate-x-1/2 glass-panel rounded-xl flex items-center gap-6 border-[#feb700]/20 z-10" style={{ bottom: '40px', padding: '16px', width: '75%', maxWidth: '672px', backdropFilter: 'blur(12px)' }}>
            <div className="flex items-center gap-3">
              <button className="material-symbols-outlined hover:scale-110 transition-transform" style={{ color: '#ffdb9d' }}>play_arrow</button>
              <span style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#ffdb9d' }}>00:00:00:00</span>
            </div>
            <div className="flex-1 h-1 bg-[#353436] rounded-full relative overflow-hidden">
              <div className="absolute inset-y-0 left-0 w-1/3 bg-[#feb700]" />
            </div>
            <div className="flex items-center gap-4">
              <span style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#bec7d4' }}>T-MINUS: 14D 02H</span>
              <button className="material-symbols-outlined hover:text-[#ffdb9d]" style={{ color: '#bec7d4' }}>settings_ethernet</button>
            </div>
          </div>

          {/* ── HUD Overlays ── */}
          <div className="absolute top-8 left-8 glass-panel p-3 rounded flex flex-col gap-1 z-10">
            <div className="flex justify-between items-center gap-10">
              <span className="uppercase" style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#bec7d4' }}>Spatial Lock</span>
              <span style={{ fontFamily: 'JetBrains Mono', fontSize: '10px', color: '#ffdb9d' }}>SYS-884</span>
            </div>
            <div style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: 'rgba(255,219,157,0.7)', letterSpacing: '-0.03em' }}>LAT: 34.0522° N</div>
            <div style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: 'rgba(255,219,157,0.7)', letterSpacing: '-0.03em' }}>LNG: 118.2437° W</div>
          </div>

          <div className="absolute top-8 right-8 glass-panel p-3 rounded flex flex-col gap-1 z-10" style={{ border: '1px solid rgba(255,180,171,0.1)' }}>
            <div className="flex justify-between items-center gap-10">
              <span className="uppercase" style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#ffb4ab' }}>Anomaly Detect</span>
              <span style={{ fontFamily: 'JetBrains Mono', fontSize: '10px', color: '#ffb4ab' }}>ALRT-02</span>
            </div>
            <div style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: 'rgba(255,180,171,0.7)' }}>CROSS-NODE TRAFFIC SPIKE</div>
          </div>
        </main>

        {/* ── RIGHT PANEL: Intelligence & Explainability ── */}
        <aside className="w-96 glass-panel border-l border-[#3f4852]/30 flex flex-col z-40 overflow-hidden flex-shrink-0">
          {/* Tabs */}
          <div className="flex border-b border-[#3f4852]/30 flex-shrink-0">
            {(['EXPLAINABILITY', 'TIMELINE', 'ASSISTANT'] as TabType[]).map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`flex-1 py-4 uppercase tracking-wider transition-all ${activeTab === tab
                  ? 'border-b-2 border-[#feb700]'
                  : 'hover:bg-[#353436]/20'
                }`}
                style={{
                  fontFamily: 'JetBrains Mono',
                  fontSize: '14px',
                  fontWeight: '500',
                  color: activeTab === tab ? '#ffdb9d' : '#bec7d4',
                  background: activeTab === tab ? 'rgba(254,183,0,0.05)' : 'transparent'
                }}
              >
                {tab}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-6">
            {activeTab === 'EXPLAINABILITY' && (
              <>
                {/* Selected Node Details or Generic Intelligence Summary */}
                {selectedEntity ? (
                  <div className="glass-panel p-4 rounded-lg relative overflow-hidden mb-6" style={{ border: '1px solid rgba(254,183,0,0.2)' }}>
                    <div className="flex items-center gap-2 mb-3">
                      <span className="material-symbols-outlined text-sm" style={{ color: '#feb700' }}>info</span>
                      <span className="uppercase" style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#feb700' }}>Entity Details</span>
                      <span className="ml-auto px-1.5 py-0.5 rounded text-[10px] font-bold" style={{ background: '#feb700', color: '#412d00' }}>
                        {selectedEntity.type}
                      </span>
                    </div>
                    <h4 style={{ fontFamily: 'Geist', fontSize: '18px', fontWeight: 'bold', color: '#e5e2e3', marginBottom: '8px' }}>
                      {selectedEntity.name}
                    </h4>
                    <p style={{ fontFamily: 'JetBrains Mono', fontSize: '11px', color: '#bec7d4', marginBottom: '12px', wordBreak: 'break-all' }}>
                      ID: {selectedEntity.id} <br />
                      Value: {selectedEntity.val}
                    </p>
                    {suspects.find(s => s.master_id === selectedEntity.id) && (
                      <div className="mt-4 border-t border-[#3f4852]/30 pt-3">
                        <div style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#ffb4ab', fontWeight: 'bold', marginBottom: '4px' }}>
                          Risk Score: {suspects.find(s => s.master_id === selectedEntity.id).risk_score}%
                        </div>
                        <ul className="list-disc pl-4 space-y-1 mt-2 text-xs text-[#bec7d4] font-sans">
                          {suspects.find(s => s.master_id === selectedEntity.id).reasons.map((reason: string, ri: number) => (
                            <li key={ri}>{reason}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="glass-panel p-4 rounded-lg relative overflow-hidden" style={{ border: '1px solid rgba(152,203,255,0.2)' }}>
                    <div className="flex items-center gap-2 mb-3">
                      <span className="material-symbols-outlined text-sm" style={{ color: '#98cbff' }}>psychology</span>
                      <span className="uppercase" style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#98cbff' }}>Intelligence Summary</span>
                      <span className="ml-auto" style={{ fontFamily: 'JetBrains Mono', fontSize: '10px', color: '#bec7d4' }}>MDL-84</span>
                    </div>
                    <p style={{ fontFamily: 'Geist', fontSize: '14px', color: '#bec7d4', lineHeight: '20px' }}>
                      Select any node in the knowledge graph to query real-time spatial properties, transaction history, centralities, and custom intelligence details.
                    </p>
                    <div className="mt-4 flex gap-2">
                      <span className="text-[10px] px-2 py-0.5 rounded" style={{ background: 'rgba(152,203,255,0.1)', border: '1px solid rgba(152,203,255,0.2)', color: '#98cbff' }}>INTERACTIVE</span>
                      <span className="text-[10px] px-2 py-0.5 rounded" style={{ background: 'rgba(254,183,0,0.1)', border: '1px solid rgba(254,183,0,0.2)', color: '#ffdb9d' }}>REAL-TIME GRAPH</span>
                    </div>
                  </div>
                )}

                {/* Evidence Hierarchy */}
                <div className="space-y-4">
                  <h3 className="uppercase tracking-widest border-b border-[#3f4852]/20 pb-2" style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#bec7d4' }}>
                    Evidence Hierarchy
                  </h3>

                  {/* Evidence Item 1 */}
                  <div className="group flex gap-4 p-3 rounded hover:bg-[#353436]/20 transition-all cursor-pointer">
                    <div className="w-1 bg-[#ffdb9d] rounded-full transition-all group-hover:w-2" />
                    <div>
                      <div style={{ fontFamily: 'JetBrains Mono', fontSize: '14px', fontWeight: '500', color: '#e5e2e3' }}>Digital Fingerprint Match</div>
                      <div className="font-mono mb-1" style={{ fontSize: '10px', color: '#bec7d4' }}>0.98 Match Probability // Log-ID: 88291</div>
                      <div className="flex items-center gap-2">
                        <span className="material-symbols-outlined" style={{ fontSize: '12px', color: '#bec7d4' }}>attachment</span>
                        <span className="underline" style={{ fontSize: '10px', color: '#98cbff' }}>FORENSIC_DUMP_01.LOG</span>
                      </div>
                    </div>
                  </div>

                  {/* Evidence Item 2 */}
                  <div className="group flex gap-4 p-3 rounded hover:bg-[#353436]/20 transition-all cursor-pointer">
                    <div className="w-1 bg-[#ffb4ab] rounded-full transition-all group-hover:w-2" />
                    <div>
                      <div style={{ fontFamily: 'JetBrains Mono', fontSize: '14px', fontWeight: '500', color: '#e5e2e3' }}>IP Geolocation Divergence</div>
                      <div className="font-mono mb-1" style={{ fontSize: '10px', color: '#bec7d4' }}>Conflict Found // Region: South-East Asia</div>
                      <div className="flex items-center gap-2">
                        <span className="material-symbols-outlined" style={{ fontSize: '12px', color: '#bec7d4' }}>history</span>
                        <span style={{ fontSize: '10px', color: '#bec7d4' }}>PREVIOUS: NORTH AMERICA</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Suspects List Section */}
                {activeTab === 'EXPLAINABILITY' && suspects.length > 0 && (
                  <div className="mt-6">
                    <h3 className="uppercase tracking-widest border-b border-[#3f4852]/20 pb-2 mb-4" style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#bec7d4' }}>Suspect Profiles</h3>
                    <div className="space-y-3">
                      {suspects.map((s, i) => (
                        <div 
                          key={i} 
                          onClick={() => setSelectedEntity({ id: s.master_id, name: s.name, type: 'PERSON', val: s.identifiers[0] })}
                          className={`p-3 rounded border transition-all cursor-pointer ${
                            selectedEntity?.id === s.master_id 
                              ? 'bg-[#feb700]/10 border-[#feb700]' 
                              : 'bg-[#201f20]/40 border-[#3f4852]/30 hover:border-[#feb700]/50'
                          }`}
                        >
                          <div className="flex justify-between items-center mb-1">
                            <span style={{ fontFamily: 'Geist', fontSize: '14px', fontWeight: '600', color: '#e5e2e3' }}>{s.name}</span>
                            <span style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#ffb4ab', fontWeight: 'bold' }}>{s.risk_score}% RISK</span>
                          </div>
                          <p style={{ fontFamily: 'JetBrains Mono', fontSize: '10px', color: '#bec7d4' }}>Centrality: {s.degree_centrality}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}

            {activeTab === 'TIMELINE' && (
              <TimelineTab selectedEntityId={selectedEntity?.id} />
            )}

            {activeTab === 'ASSISTANT' && (
              <AssistantTab selectedEntity={selectedEntity} />
            )}
          </div>

          {/* Action Area */}
          <div className="p-6 border-t border-[#3f4852]/30 space-y-3 flex-shrink-0">
            <button
              onClick={() => alert(JSON.stringify(selectedEntity || suspects, null, 2))}
              className="w-full py-4 rounded-lg flex items-center justify-center gap-2 hover:brightness-110 active:scale-[0.98] transition-all"
              style={{ background: '#feb700', color: '#412d00', fontFamily: 'Geist', fontSize: '24px', fontWeight: '600', boxShadow: 'inset 0 0 10px rgba(152,203,255,0.1)' }}
            >
              <span className="material-symbols-outlined">send</span>
              <span style={{ fontSize: '18px' }}>Export Findings</span>
            </button>
            <button
              className="w-full py-3 rounded-lg hover:text-[#e5e2e3] transition-all border border-[#3f4852]/30 uppercase tracking-widest"
              style={{ background: '#2a2a2b', color: '#bec7d4', fontFamily: 'JetBrains Mono', fontSize: '14px', fontWeight: '500' }}
            >
              Request Agency Peer Review
            </button>
          </div>
        </aside>
      </div>
    </div>
  )
}

function TimelineTab({ selectedEntityId }: { selectedEntityId?: string }) {
  const [timeline, setTimeline] = useState<any[]>([]);

  useEffect(() => {
    fetch('http://localhost:8000/api/timeline')
      .then(res => res.json())
      .then(data => {
        if (selectedEntityId) {
          // Filter timeline events containing selected entity
          setTimeline(data.filter((e: any) => e.source_id === selectedEntityId || e.target_id === selectedEntityId));
        } else {
          setTimeline(data.slice(0, 15)); // Default to first 15 events chronologically
        }
      })
      .catch(err => console.error('Failed to fetch timeline', err));
  }, [selectedEntityId]);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 justify-between">
        <h3 className="uppercase tracking-widest border-b border-[#3f4852]/20 pb-2 flex-grow" style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#bec7d4' }}>
          {selectedEntityId ? 'Filtered Intel Timeline' : 'Global Temporal Sequence'}
        </h3>
      </div>
      {timeline.length === 0 ? (
        <div className="text-center py-8 text-[#bec7d4]/50 text-xs font-mono">No chronological activities found for this node.</div>
      ) : (
        <div className="relative border-l-2 border-[#3f4852]/50 pl-4 ml-2 space-y-6">
          {timeline.map((event, index) => (
            <div key={index} className="relative group">
              {/* Bullet node indicator */}
              <div 
                className="absolute -left-[22px] top-1 w-2.5 h-2.5 rounded-full border border-black transition-transform duration-300 group-hover:scale-125" 
                style={{ 
                  background: event.relation_type === 'TRANSFERRED_TO' ? '#00a3ff' : 
                              event.relation_type === 'CALLED' ? '#98cbff' : '#feb700' 
                }} 
              />
              <div style={{ fontFamily: 'JetBrains Mono', fontSize: '11px', color: '#98cbff' }}>{event.timestamp}</div>
              <div style={{ fontFamily: 'Geist', fontSize: '13px', fontWeight: '500', color: '#e5e2e3', marginTop: '2px' }}>{event.description}</div>
              <div style={{ fontFamily: 'JetBrains Mono', fontSize: '9px', color: '#bec7d4', marginTop: '4px' }}>
                Source: {event.source_type} // Conf: {Math.round(event.confidence * 100)}%
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function AssistantTab({ selectedEntity }: { selectedEntity?: any }) {
  const [messages, setMessages] = useState<{ sender: 'user' | 'system'; text: string }[]>([
    { sender: 'system', text: 'TATVA Cognitive Engine initialized. You can ask queries regarding aliases, transaction flow paths, and entity overlaps.' }
  ]);
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (!input.trim()) return;
    const userMsg = input;
    setMessages(prev => [...prev, { sender: 'user', text: userMsg }]);
    setInput('');

    // Simulate AI response based on TATVA knowledge base
    setTimeout(() => {
      let reply = "Processing intelligence query... I could not find a direct answer in my current graph nodes list.";
      const query = userMsg.toLowerCase();

      if (query.includes('rahul') || query.includes('primary')) {
        reply = "Rahul Sen is the primary suspect (99% Risk). He has degree centrality 0.25, owns account 'acc_rahul_sen', and has 8 communications with Arjun Mehta.";
      } else if (query.includes('arjun') || query.includes('co-conspirator')) {
        reply = "Arjun Mehta (90% Risk) is flagged as a key co-conspirator. He is connected to both Rahul Sen and Rajan Varma, acting as a bridge node.";
      } else if (query.includes('hawala') || query.includes('smurfing') || query.includes('transfers')) {
        reply = "I detected a smurfing structure where money splits into intermediary accounts (Rajan Varma) and aggregates before exiting to Hawala (acc_hawala).";
      } else if (selectedEntity) {
        reply = `Analyzing entity '${selectedEntity.name}' (${selectedEntity.type}). They are associated with resolved ID ${selectedEntity.val}. What specific relationship paths or geolocations would you like me to inspect?`;
      }

      setMessages(prev => [...prev, { sender: 'system', text: reply }]);
    }, 1000);
  };

  return (
    <div className="flex flex-col h-[400px]">
      <h3 className="uppercase tracking-widest border-b border-[#3f4852]/20 pb-2 mb-3" style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#bec7d4' }}>
        Tactical Assistant
      </h3>
      <div className="flex-1 overflow-y-auto space-y-3 pr-2 mb-3 max-h-[300px] custom-scrollbar">
        {messages.map((m, idx) => (
          <div key={idx} className={`p-3 rounded-lg text-xs leading-relaxed max-w-[85%] ${
            m.sender === 'user' 
              ? 'bg-[#feb700]/10 border border-[#feb700]/30 text-[#ffdb9d] ml-auto' 
              : 'bg-[#353436]/40 border border-[#3f4852]/20 text-[#bec7d4]'
          }`}>
            <div className="font-bold mb-1 uppercase tracking-wider" style={{ fontSize: '9px', opacity: 0.8 }}>
              {m.sender === 'user' ? 'AGENT // INQUIRY' : 'TATVA // COGNITIVE'}
            </div>
            <div>{m.text}</div>
          </div>
        ))}
      </div>
      <div className="flex gap-2 mt-auto">
        <input 
          type="text" 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder={selectedEntity ? `Ask about ${selectedEntity.name}...` : "Query graph intelligence..."}
          className="flex-grow bg-[#201f20] border border-[#3f4852]/50 rounded px-3 py-2 text-xs text-[#e5e2e3] focus:outline-none focus:border-[#feb700]"
          style={{ fontFamily: 'Geist' }}
        />
        <button 
          onClick={handleSend}
          className="px-4 bg-[#feb700] hover:brightness-110 text-[#412d00] text-xs font-bold rounded flex items-center justify-center"
        >
          <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>send</span>
        </button>
      </div>
    </div>
  );
}

