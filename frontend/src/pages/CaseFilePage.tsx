import { useState, useEffect, useRef, useCallback } from 'react'
import type { DragEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import type { CaseListItem, EvidenceUploadItem, CognitiveConfig } from '../types/case'

// ====================================================================
// TATVA | Case File Initialization
// Stitch screen: e51101a195104961b26a638bab7f14a8
// Layout: Fixed TopNav + Fixed SideNav + Scrollable main
// Colors: Blue primary (#98cbff), Amber accent (#feb700)
// ====================================================================

const API_BASE = 'http://localhost:8000'
const ALLOWED_EXTENSIONS = new Set(['csv', 'json', 'txt', 'pdf', 'wav', 'jpg', 'jpeg', 'png', 'log'])

function slugify(str: string): string {
  return str
    .toUpperCase()
    .replace(/[^A-Z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 40) || 'CASE'
}

function generateCaseId(caseName: string): string {
  const timestamp = Math.floor(Date.now() / 1000)
  return `CASE-${timestamp}-${slugify(caseName)}`
}

function getFileType(filename: string): string {
  return filename.split('.').pop()?.toLowerCase() || 'unknown'
}

function getFileIcon(fileType: string): string {
  switch (fileType) {
    case 'csv': return 'table_chart'
    case 'json': return 'data_object'
    case 'pdf': return 'picture_as_pdf'
    case 'txt': case 'log': return 'description'
    case 'wav': return 'graphic_eq'
    case 'jpg': case 'jpeg': case 'png': return 'image'
    default: return 'database'
  }
}

function getStatusColor(status: EvidenceUploadItem['status']): string {
  switch (status) {
    case 'uploading': return '#ffdb9d'
    case 'uploaded': return '#a8d8a8'
    case 'error': return '#ffb4ab'
    default: return '#bec7d4'
  }
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatCaseDate(iso: string | null): string {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleDateString('en-US', {
      month: 'short', day: '2-digit', year: 'numeric'
    })
  } catch { return '—' }
}

function getStatusBadge(status: string): { bg: string; color: string; label: string } {
  switch (status) {
    case 'open': return { bg: 'rgba(152,203,255,0.15)', color: '#98cbff', label: 'OPEN' }
    case 'in_progress': return { bg: 'rgba(254,183,0,0.15)', color: '#ffdb9d', label: 'ACTIVE' }
    case 'closed': return { bg: 'rgba(63,72,82,0.3)', color: '#bec7d4', label: 'CLOSED' }
    default: return { bg: 'rgba(63,72,82,0.3)', color: '#bec7d4', label: status.toUpperCase() }
  }
}

export default function CaseFilePage() {
  const navigate = useNavigate()
  const fileInputRef = useRef<HTMLInputElement>(null)

  // ── Form State ──────────────────────────────────────────────
  const [caseName, setCaseName] = useState('')
  const [investigationType, setInvestigationType] = useState('Cyber Forensics')
  const [incidentDate, setIncidentDate] = useState('')
  const [priorityLevel, setPriorityLevel] = useState<'LOW' | 'CRITICAL' | 'IMMEDIATE'>('CRITICAL')
  const [investigatorNotes, setInvestigatorNotes] = useState('')
  const [configs, setConfigs] = useState<CognitiveConfig>({
    anomaly: true,
    gnn: false,
    intel: true,
    temporal: true,
  })

  // ── Upload Queue ─────────────────────────────────────────────
  const [uploadQueue, setUploadQueue] = useState<EvidenceUploadItem[]>([])
  const [isDragging, setIsDragging] = useState(false)

  // ── Submission State ─────────────────────────────────────────
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [formError, setFormError] = useState('')

  // ── Case Repository ──────────────────────────────────────────
  const [cases, setCases] = useState<CaseListItem[]>([])
  const [casesLoading, setCasesLoading] = useState(true)
  const [casesError, setCasesError] = useState('')

  // ── Fetch existing cases ─────────────────────────────────────
  const fetchCases = useCallback(async () => {
    setCasesLoading(true)
    setCasesError('')
    try {
      const res = await fetch(`${API_BASE}/api/cases`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setCases(Array.isArray(data) ? data : [])
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load cases'
      setCasesError(msg)
    } finally {
      setCasesLoading(false)
    }
  }, [])

  useEffect(() => { fetchCases() }, [fetchCases])

  // ── Toggle cognitive config ──────────────────────────────────
  const toggleConfig = (key: keyof CognitiveConfig) => {
    setConfigs(prev => ({ ...prev, [key]: !prev[key] }))
  }

  // ── Add files to queue ───────────────────────────────────────
  const addFiles = useCallback((files: FileList | File[]) => {
    const arr = Array.from(files)
    const valid = arr.filter(f => {
      const ext = f.name.split('.').pop()?.toLowerCase() || ''
      return ALLOWED_EXTENSIONS.has(ext)
    })

    if (valid.length < arr.length) {
      setFormError(`Some files were skipped — only CSV, JSON, TXT, PDF, WAV, JPG, PNG, LOG are supported.`)
      setTimeout(() => setFormError(''), 4000)
    }

    setUploadQueue(prev => [
      ...prev,
      ...valid.map(f => ({
        key: `${f.name}-${Date.now()}-${Math.random()}`,
        file: f,
        filename: f.name,
        file_type: getFileType(f.name),
        status: 'queued' as const,
        progress: 0,
      }))
    ])
  }, [])

  // ── Drag handlers ────────────────────────────────────────────
  const onDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(true)
  }
  const onDragLeave = () => setIsDragging(false)
  const onDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)
    if (e.dataTransfer.files.length > 0) addFiles(e.dataTransfer.files)
  }

  const removeFile = (key: string) => {
    setUploadQueue(prev => prev.filter(f => f.key !== key))
  }

  // ── Upload a single file via XHR for progress tracking ───────
  const uploadFile = (
    caseId: string,
    item: EvidenceUploadItem,
    onProgress: (p: number) => void,
    onDone: (hash: string) => void,
    onError: (msg: string) => void
  ) => {
    const formData = new FormData()
    formData.append('file', item.file, item.filename)

    const xhr = new XMLHttpRequest()
    xhr.open('POST', `${API_BASE}/api/cases/${caseId}/upload`)

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) {
        onProgress(Math.round((e.loaded / e.total) * 100))
      }
    }

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const resp = JSON.parse(xhr.responseText)
          onDone(resp.file_hash || '')
        } catch {
          onDone('')
        }
      } else {
        try {
          const err = JSON.parse(xhr.responseText)
          onError(err.detail || `HTTP ${xhr.status}`)
        } catch {
          onError(`HTTP ${xhr.status}`)
        }
      }
    }

    xhr.onerror = () => onError('Network error')
    xhr.send(formData)
  }

  // ── Update a queue item by key ───────────────────────────────
  const updateQueueItem = (key: string, patch: Partial<EvidenceUploadItem>) => {
    setUploadQueue(prev =>
      prev.map(item => item.key === key ? { ...item, ...patch } : item)
    )
  }

  // ── INITIALIZE UNIT handler ──────────────────────────────────
  const handleInitializeUnit = async () => {
    setFormError('')

    // Validation
    if (!caseName.trim()) {
      setFormError('Case Name is required.')
      return
    }

    setIsSubmitting(true)
    const caseId = generateCaseId(caseName.trim())

    try {
      // 1. Create case in PostgreSQL
      const createRes = await fetch(`${API_BASE}/api/cases`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          case_id: caseId,
          title: caseName.trim(),
          description: investigatorNotes.trim(),
          investigator: 'Analyst',
          metadata: {
            investigation_type: investigationType,
            incident_date: incidentDate,
            priority: priorityLevel,
            cognitive_config: configs,
          },
        }),
      })

      if (!createRes.ok) {
        const err = await createRes.json()
        throw new Error(err.detail || `Case creation failed (HTTP ${createRes.status})`)
      }

      // 2. Upload files sequentially
      const pendingFiles = uploadQueue.filter(f => f.status === 'queued')
      for (const item of pendingFiles) {
        // Mark as uploading
        updateQueueItem(item.key, { status: 'uploading', progress: 0 })

        await new Promise<void>((resolve) => {
          uploadFile(
            caseId,
            item,
            (p) => updateQueueItem(item.key, { progress: p }),
            (hash) => {
              updateQueueItem(item.key, { status: 'uploaded', progress: 100, file_hash: hash })
              resolve()
            },
            (msg) => {
              updateQueueItem(item.key, { status: 'error', error: msg })
              resolve() // continue with next file even if one fails
            }
          )
        })
      }

      // 3. Refresh case list
      await fetchCases()

      // 4. Navigate to reconstruction/processing page
      navigate('/reconstruction')

    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unknown error occurred'
      setFormError(msg)
    } finally {
      setIsSubmitting(false)
    }
  }

  // ── Discard handler ──────────────────────────────────────────
  const handleDiscard = () => {
    setCaseName('')
    setInvestigationType('Cyber Forensics')
    setIncidentDate('')
    setPriorityLevel('CRITICAL')
    setInvestigatorNotes('')
    setConfigs({ anomaly: true, gnn: false, intel: true, temporal: true })
    setUploadQueue([])
    setFormError('')
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
            <a href="#" onClick={(e) => { e.preventDefault(); navigate('/case/new') }} className="font-bold border-b-2 border-[#feb700] pb-1 transition-colors duration-200" style={{ color: '#ffdb9d', fontFamily: 'Geist', fontSize: '16px' }}>Dashboard</a>
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
            <div className="flex gap-4 items-start flex-col">
              {formError && (
                <p className="text-right px-4 py-2 rounded border border-[#ffb4ab]/30"
                  style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#ffb4ab', background: 'rgba(255,180,171,0.08)', maxWidth: '320px' }}>
                  {formError}
                </p>
              )}
              <div className="flex gap-4">
                <button
                  onClick={handleDiscard}
                  disabled={isSubmitting}
                  className="px-6 py-2 rounded border border-[#3f4852] text-[#e5e2e3] hover:bg-[#353436]/20 transition-all font-medium disabled:opacity-50"
                >
                  DISCARD
                </button>
                <button
                  id="initialize-unit-btn"
                  onClick={handleInitializeUnit}
                  disabled={isSubmitting}
                  className="px-8 py-2 rounded font-bold transition-all flex items-center gap-2 disabled:opacity-60"
                  style={{ background: '#98cbff', color: '#003354', boxShadow: '0 0 20px rgba(152,203,255,0.1)' }}
                >
                  {isSubmitting && (
                    <span className="material-symbols-outlined animate-spin" style={{ fontSize: '18px' }}>progress_activity</span>
                  )}
                  {isSubmitting ? 'INITIALIZING...' : 'INITIALIZE UNIT'}
                </button>
              </div>
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
                    <label className="uppercase" style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#bec7d4' }}>
                      Case Name <span style={{ color: '#ffb4ab' }}>*</span>
                    </label>
                    <input
                      id="case-name-input"
                      type="text"
                      value={caseName}
                      onChange={e => setCaseName(e.target.value)}
                      placeholder="e.g., OPERATION_STORM_WATCH"
                      className="w-full border border-[#3f4852]/40 rounded px-4 py-2.5 focus:border-[#feb700] outline-none transition-all"
                      style={{ background: '#0e0e0f', color: '#e5e2e3', fontFamily: 'JetBrains Mono', fontSize: '14px', fontWeight: '500' }}
                    />
                    {caseName && (
                      <p style={{ fontFamily: 'JetBrains Mono', fontSize: '10px', color: '#bec7d4', opacity: 0.7 }}>
                        ID: {generateCaseId(caseName)}
                      </p>
                    )}
                  </div>

                  {/* Investigation Type */}
                  <div className="space-y-1.5">
                    <label className="uppercase" style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#bec7d4' }}>Investigation Type</label>
                    <select
                      id="investigation-type-select"
                      value={investigationType}
                      onChange={e => setInvestigationType(e.target.value)}
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
                      id="incident-date-input"
                      type="date"
                      value={incidentDate}
                      onChange={e => setIncidentDate(e.target.value)}
                      className="w-full border border-[#3f4852]/40 rounded px-4 py-2.5 focus:border-[#feb700] outline-none transition-all"
                      style={{ background: '#0e0e0f', color: '#e5e2e3', fontFamily: 'JetBrains Mono', fontSize: '14px', fontWeight: '500' }}
                    />
                  </div>

                  {/* Priority Level */}
                  <div className="space-y-1.5">
                    <label className="uppercase" style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#bec7d4' }}>Priority Level</label>
                    <div className="flex gap-2">
                      {(['LOW', 'CRITICAL', 'IMMEDIATE'] as const).map(level => (
                        <button
                          id={`priority-${level.toLowerCase()}-btn`}
                          key={level}
                          onClick={() => setPriorityLevel(level)}
                          className="flex-1 py-2 border rounded font-bold transition-all"
                          style={{
                            fontFamily: 'JetBrains Mono',
                            fontSize: '12px',
                            background: priorityLevel === level ? 'rgba(254,183,0,0.1)' : 'transparent',
                            color: priorityLevel === level ? '#ffdb9d' : '#bec7d4',
                            border: priorityLevel === level ? '1px solid rgba(254,183,0,0.4)' : '1px solid rgba(63,72,82,0.4)',
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
                      id="investigator-notes-input"
                      rows={3}
                      value={investigatorNotes}
                      onChange={e => setInvestigatorNotes(e.target.value)}
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
                    SUPPORTED: CSV, JSON, PDF, TXT, WAV, LOG
                  </span>
                </div>

                {/* Hidden file input */}
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept=".csv,.json,.txt,.pdf,.wav,.jpg,.jpeg,.png,.log"
                  style={{ display: 'none' }}
                  onChange={e => { if (e.target.files) addFiles(e.target.files); e.target.value = '' }}
                />

                {/* Drop Zone */}
                <div
                  id="evidence-drop-zone"
                  className="border-2 border-dashed rounded-xl p-10 flex flex-col items-center justify-center group cursor-pointer transition-all"
                  style={{
                    background: isDragging ? 'rgba(152,203,255,0.05)' : 'rgba(28,27,28,0.3)',
                    borderColor: isDragging ? 'rgba(152,203,255,0.5)' : 'rgba(63,72,82,0.3)',
                  }}
                  onDragOver={onDragOver}
                  onDragLeave={onDragLeave}
                  onDrop={onDrop}
                  onClick={() => fileInputRef.current?.click()}
                >
                  <span
                    className="material-symbols-outlined mb-4 transition-colors"
                    style={{ fontSize: '64px', color: isDragging ? '#98cbff' : '#3f4852' }}
                  >
                    move_to_inbox
                  </span>
                  <p className="font-semibold mb-2" style={{ fontFamily: 'Geist', fontSize: '18px', color: '#e5e2e3' }}>
                    Drop forensic payload here
                  </p>
                  <p style={{ fontFamily: 'Geist', fontSize: '14px', color: '#bec7d4' }}>
                    or <span className="hover:underline" style={{ color: '#98cbff' }}>browse files</span> for ingestion
                  </p>
                </div>

                {/* Upload Queue */}
                {uploadQueue.length > 0 && (
                  <div className="mt-6 space-y-3">
                    {uploadQueue.map(item => (
                      <div
                        key={item.key}
                        className="border border-[#3f4852]/20 rounded p-4 flex items-center gap-4"
                        style={{ background: '#0e0e0f', opacity: item.status === 'queued' ? 0.7 : 1 }}
                      >
                        <span className="material-symbols-outlined" style={{ color: getStatusColor(item.status) }}>
                          {getFileIcon(item.file_type)}
                        </span>
                        <div className="flex-1 min-w-0">
                          <div className="flex justify-between mb-1.5" style={{ fontFamily: 'JetBrains Mono', fontSize: '12px' }}>
                            <span className="font-bold truncate pr-2">{item.filename.toUpperCase()}</span>
                            <span style={{ color: getStatusColor(item.status), whiteSpace: 'nowrap', flexShrink: 0 }}>
                              {item.status === 'uploading' && `UPLOADING... ${item.progress}%`}
                              {item.status === 'queued' && `QUEUED · ${formatFileSize(item.file.size)}`}
                              {item.status === 'uploaded' && '✓ UPLOADED'}
                              {item.status === 'error' && `✗ ERROR: ${item.error}`}
                            </span>
                          </div>
                          <div className="w-full h-1 bg-[#353436] rounded-full overflow-hidden">
                            <div
                              className="h-full rounded-full transition-all duration-300"
                              style={{
                                width: `${item.progress}%`,
                                background: item.status === 'error'
                                  ? '#ffb4ab'
                                  : item.status === 'uploaded'
                                    ? '#a8d8a8'
                                    : '#feb700',
                              }}
                            />
                          </div>
                        </div>
                        {item.status !== 'uploading' && (
                          <button
                            onClick={() => removeFile(item.key)}
                            className="material-symbols-outlined cursor-pointer hover:text-[#ffb4ab] transition-colors flex-shrink-0"
                            style={{ color: '#bec7d4' }}
                          >
                            close
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </section>

              {/* ── Cognitive Configuration ── */}
              <section className="glass-panel p-6 rounded-xl">
                <h2 className="flex items-center gap-2 mb-6" style={{ fontFamily: 'Geist', fontSize: '24px', fontWeight: '600', color: '#e5e2e3' }}>
                  <span className="material-symbols-outlined">settings_input_component</span> Cognitive Configuration
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {[
                    { key: 'anomaly' as const, label: 'Anomaly Detection', sub: 'Heuristic pattern mismatch trigger' },
                    { key: 'gnn' as const, label: 'GNN Inference', sub: 'Graph Neural Network link prediction' },
                    { key: 'intel' as const, label: 'Intel Matching', sub: 'Auto-cross-reference known records' },
                    { key: 'temporal' as const, label: 'Temporal Recon', sub: '4D causality mapping of evidence' },
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
                          checked={configs[item.key]}
                          onChange={() => toggleConfig(item.key)}
                        />
                        <div
                          onClick={() => toggleConfig(item.key)}
                          className="w-11 h-6 rounded-full relative transition-colors"
                          style={{ background: configs[item.key] ? '#feb700' : '#353436' }}
                        >
                          <div
                            className="absolute top-0.5 h-5 w-5 rounded-full bg-white transition-transform"
                            style={{ left: '2px', transform: configs[item.key] ? 'translateX(20px)' : 'translateX(0)' }}
                          />
                        </div>
                      </div>
                    </label>
                  ))}
                </div>
              </section>
            </div>

            {/* Right: 4 cols — Case Repository */}
            <div className="col-span-12 lg:col-span-4">
              <section className="glass-panel p-6 rounded-xl h-full flex flex-col">
                <h2 className="flex items-center gap-2 mb-2" style={{ fontFamily: 'Geist', fontSize: '24px', fontWeight: '600', color: '#e5e2e3' }}>
                  <span className="material-symbols-outlined">folder_open</span> Case Repository
                </h2>
                <p className="uppercase tracking-widest border-b border-[#3f4852]/20 pb-4 mb-6" style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#bec7d4' }}>
                  PostgreSQL — Supabase
                </p>

                <div className="flex-1 overflow-y-auto custom-scrollbar space-y-3" style={{ maxHeight: '680px' }}>

                  {/* Loading state */}
                  {casesLoading && (
                    <div className="flex flex-col items-center justify-center py-12 gap-3">
                      <span className="material-symbols-outlined animate-spin" style={{ fontSize: '32px', color: '#bec7d4' }}>
                        progress_activity
                      </span>
                      <p style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#bec7d4' }}>LOADING CASES...</p>
                    </div>
                  )}

                  {/* Error state */}
                  {!casesLoading && casesError && (
                    <div className="flex flex-col items-center justify-center py-10 gap-3">
                      <span className="material-symbols-outlined" style={{ fontSize: '32px', color: '#ffb4ab' }}>wifi_off</span>
                      <p style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#ffb4ab', textAlign: 'center' }}>
                        COULD NOT FETCH CASES
                      </p>
                      <p style={{ fontFamily: 'Geist', fontSize: '12px', color: '#bec7d4', textAlign: 'center' }}>
                        {casesError}
                      </p>
                      <button
                        onClick={fetchCases}
                        className="mt-2 px-4 py-1.5 rounded border border-[#3f4852]/40 hover:border-[#98cbff]/40 transition-all"
                        style={{ fontFamily: 'JetBrains Mono', fontSize: '11px', color: '#98cbff' }}
                      >
                        RETRY
                      </button>
                    </div>
                  )}

                  {/* Empty state */}
                  {!casesLoading && !casesError && cases.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-12 gap-3">
                      <span className="material-symbols-outlined" style={{ fontSize: '48px', color: '#3f4852' }}>inbox</span>
                      <p style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#bec7d4', textAlign: 'center' }}>
                        NO CASES FOUND
                      </p>
                      <p style={{ fontFamily: 'Geist', fontSize: '13px', color: '#3f4852', textAlign: 'center' }}>
                        Create your first investigation above.
                      </p>
                    </div>
                  )}

                  {/* Case list */}
                  {!casesLoading && !casesError && cases.map(c => {
                    const badge = getStatusBadge(c.status)
                    return (
                      <div
                        key={c.case_id}
                        className="p-4 border border-[#3f4852]/30 rounded hover:border-[#feb700]/50 transition-all cursor-pointer group"
                        style={{ background: '#0e0e0f' }}
                        onClick={() => navigate('/investigation')}
                      >
                        {/* Case title + status badge */}
                        <div className="flex justify-between items-start mb-2 gap-2">
                          <span className="font-bold truncate" style={{ fontFamily: 'Geist', fontSize: '14px', color: '#e5e2e3' }}>
                            {c.title}
                          </span>
                          <span
                            className="px-2 py-0.5 rounded font-bold flex-shrink-0"
                            style={{ background: badge.bg, color: badge.color, fontSize: '10px', fontFamily: 'JetBrains Mono' }}
                          >
                            {badge.label}
                          </span>
                        </div>

                        {/* Case ID */}
                        <p style={{ fontFamily: 'JetBrains Mono', fontSize: '11px', color: '#bec7d4', marginBottom: '8px' }}>
                          {c.case_id}
                        </p>

                        {/* Metadata row */}
                        <div className="flex items-center justify-between">
                          <div className="flex gap-2 flex-wrap">
                            {c.investigator && (
                              <span className="px-1.5 py-0.5 border border-[#3f4852]/30" style={{ fontFamily: 'JetBrains Mono', fontSize: '10px', color: '#bec7d4' }}>
                                {c.investigator}
                              </span>
                            )}
                          </div>
                          <span style={{ fontFamily: 'JetBrains Mono', fontSize: '10px', color: '#3f4852' }}>
                            {formatCaseDate(c.created_at)}
                          </span>
                        </div>
                      </div>
                    )
                  })}
                </div>

                {/* Footer: open investigation */}
                <div className="mt-auto pt-6 border-t border-[#3f4852]/20">
                  <button
                    onClick={() => navigate('/investigation')}
                    className="w-full py-3 rounded border border-[#98cbff]/40 font-bold hover:bg-[#98cbff]/10 transition-all flex items-center justify-center gap-2"
                    style={{ color: '#98cbff', fontFamily: 'Geist', fontSize: '14px' }}
                  >
                    <span className="material-symbols-outlined">analytics</span> OPEN INVESTIGATION
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
