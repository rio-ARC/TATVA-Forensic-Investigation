/**
 * ExportReportModal.tsx
 * =====================
 * Premium PDF export modal for TATVA Forensic Investigation Reports.
 * Fetches the Gemini-generated markdown report from the backend,
 * parses it, and generates a styled multi-page PDF dossier using jsPDF.
 */

import { useState } from 'react'
import jsPDF from 'jspdf'

interface ExportReportModalProps {
  onClose: () => void
  caseId: string
}

interface ReportPayload {
  report_markdown: string
  risk_profiles: any[]
  timeline: any
  summary: any
  generated_at: number | null
}

// ── Colour palette (mimics TATVA UI) ────────────────────────────────────────
const GOLD   = [254, 183, 0]   as const   // #feb700
const DARK   = [10, 10, 11]   as const    // #0a0a0b
const MID    = [28, 27, 28]   as const    // #1c1b1c
const LIGHT  = [229, 226, 227] as const   // #e5e2e3
const MUTED  = [190, 199, 212] as const   // #bec7d4
const RED    = [239, 68, 68]   as const   // #ef4444
const AMBER  = [255, 180, 171] as const   // #ffb4ab

// Risk level → colour
const riskColor = (score: number): readonly [number, number, number] => {
  if (score >= 85) return RED
  if (score >= 60) return AMBER
  return MUTED
}

/**
 * Convert a markdown string to an ordered list of { type, text } blocks
 * suitable for rendering into jsPDF cells. We handle only the subset of
 * markdown that the Gemini report uses.
 */
function parseMarkdown(md: string): Array<{ type: string; text: string; level?: number }> {
  const blocks: Array<{ type: string; text: string; level?: number }> = []
  const lines = md.split('\n')

  for (const raw of lines) {
    const line = raw.trimEnd()
    if (!line) {
      blocks.push({ type: 'blank', text: '' })
      continue
    }
    const h1 = line.match(/^# (.+)/)
    const h2 = line.match(/^## (.+)/)
    const h3 = line.match(/^### (.+)/)
    const h4 = line.match(/^#### (.+)/)
    const bullet = line.match(/^\s*[\*\-]\s+(.+)/)
    const numbered = line.match(/^\s*\d+\.\s+(.+)/)
    const bold = line.match(/^\*\*(.+)\*\*$/)
    const hr = line.match(/^---+$/)
    const code = line.match(/^```/)

    if (hr) {
      blocks.push({ type: 'hr', text: '' })
    } else if (code) {
      blocks.push({ type: 'code_fence', text: '' })
    } else if (h1) {
      blocks.push({ type: 'h1', text: h1[1].replace(/\*/g, '') })
    } else if (h2) {
      blocks.push({ type: 'h2', text: h2[1].replace(/\*/g, '') })
    } else if (h3) {
      blocks.push({ type: 'h3', text: h3[1].replace(/\*/g, '') })
    } else if (h4) {
      blocks.push({ type: 'h4', text: h4[1].replace(/\*/g, '') })
    } else if (bold) {
      blocks.push({ type: 'bold', text: bold[1] })
    } else if (bullet) {
      const clean = bullet[1].replace(/\*\*(.+?)\*\*/g, '$1').replace(/\*/g, '')
      blocks.push({ type: 'bullet', text: clean })
    } else if (numbered) {
      const clean = numbered[1].replace(/\*\*(.+?)\*\*/g, '$1').replace(/\*/g, '')
      blocks.push({ type: 'numbered', text: clean })
    } else {
      // plain paragraph — strip inline markdown
      const clean = line
        .replace(/\*\*(.+?)\*\*/g, '$1')
        .replace(/\*(.+?)\*/g, '$1')
        .replace(/`(.+?)`/g, '$1')
      blocks.push({ type: 'p', text: clean })
    }
  }
  return blocks
}

/**
 * Draws a full-bleed cover page.
 */
function drawCoverPage(pdf: jsPDF, caseId: string, generatedAt: number | null) {
  const W = pdf.internal.pageSize.getWidth()
  const H = pdf.internal.pageSize.getHeight()

  // Background
  pdf.setFillColor(...DARK)
  pdf.rect(0, 0, W, H, 'F')

  // Gold accent strip
  pdf.setFillColor(...GOLD)
  pdf.rect(0, 0, 6, H, 'F')

  // TATVA wordmark
  pdf.setFont('helvetica', 'bold')
  pdf.setFontSize(52)
  pdf.setTextColor(...GOLD)
  pdf.text('TATVA', 24, 60)

  // Subtitle
  pdf.setFontSize(13)
  pdf.setFont('helvetica', 'normal')
  pdf.setTextColor(...MUTED)
  pdf.text('FORENSIC INTELLIGENCE PLATFORM', 24, 74)

  // Divider
  pdf.setDrawColor(...GOLD)
  pdf.setLineWidth(0.5)
  pdf.line(24, 82, W - 24, 82)

  // Report title
  pdf.setFontSize(22)
  pdf.setFont('helvetica', 'bold')
  pdf.setTextColor(...LIGHT)
  pdf.text('FORENSIC INVESTIGATION REPORT', 24, 108)

  // Case info block
  const ts = generatedAt ? new Date(generatedAt * 1000).toUTCString() : new Date().toUTCString()
  pdf.setFontSize(11)
  pdf.setFont('helvetica', 'normal')
  pdf.setTextColor(...MUTED)
  pdf.text(`Case Reference:  ${caseId}`, 24, 130)
  pdf.text(`Classification:   RESTRICTED — LAW ENFORCEMENT ONLY`, 24, 143)
  pdf.text(`Generated:        ${ts}`, 24, 156)

  // Footer
  pdf.setFillColor(...MID)
  pdf.rect(0, H - 28, W, 28, 'F')
  pdf.setFontSize(9)
  pdf.setTextColor(...MUTED)
  pdf.text('TATVA | Automated Forensic Intelligence System', 24, H - 12)
  pdf.text('CONFIDENTIAL', W - 24, H - 12, { align: 'right' })
}

/**
 * Renders the full markdown report into subsequent PDF pages.
 * Returns the final Y position.
 */
function drawReportContent(pdf: jsPDF, blocks: ReturnType<typeof parseMarkdown>) {
  const W = pdf.internal.pageSize.getWidth()
  const H = pdf.internal.pageSize.getHeight()
  const marginL = 20
  const marginR = 20
  const contentW = W - marginL - marginR
  const marginBottom = 28
  const lineGap = 5

  let y = 28
  let insideCodeBlock = false

  const ensureSpace = (needed: number) => {
    if (y + needed > H - marginBottom) {
      pdf.addPage()
      // Dark background on every page
      pdf.setFillColor(...DARK)
      pdf.rect(0, 0, W, H, 'F')
      // Gold left strip
      pdf.setFillColor(...GOLD)
      pdf.rect(0, 0, 4, H, 'F')
      // Page footer
      pdf.setFillColor(...MID)
      pdf.rect(0, H - 20, W, 20, 'F')
      pdf.setFontSize(8)
      pdf.setFont('helvetica', 'normal')
      pdf.setTextColor(...MUTED)
      pdf.text('TATVA Forensic Report — CONFIDENTIAL', marginL, H - 8)
      const pageNum = pdf.getNumberOfPages()
      pdf.text(`Page ${pageNum}`, W - marginR, H - 8, { align: 'right' })
      y = 28
    }
  }

  for (const block of blocks) {
    if (block.type === 'code_fence') {
      insideCodeBlock = !insideCodeBlock
      continue
    }
    if (insideCodeBlock) continue // skip raw JSON in report

    switch (block.type) {
      case 'blank': {
        y += 3
        break
      }
      case 'hr': {
        ensureSpace(6)
        pdf.setDrawColor(...GOLD)
        pdf.setLineWidth(0.3)
        pdf.line(marginL, y, W - marginR, y)
        y += 8
        break
      }
      case 'h1': {
        ensureSpace(18)
        pdf.setFillColor(...MID)
        pdf.rect(marginL - 4, y - 6, contentW + 8, 16, 'F')
        pdf.setFillColor(...GOLD)
        pdf.rect(marginL - 4, y - 6, 3, 16, 'F')
        pdf.setFontSize(16)
        pdf.setFont('helvetica', 'bold')
        pdf.setTextColor(...GOLD)
        const lines = pdf.splitTextToSize(block.text, contentW)
        pdf.text(lines, marginL + 4, y + 4)
        y += lines.length * 7 + 8
        break
      }
      case 'h2': {
        ensureSpace(14)
        pdf.setFontSize(13)
        pdf.setFont('helvetica', 'bold')
        pdf.setTextColor(...GOLD)
        const lines = pdf.splitTextToSize(block.text.toUpperCase(), contentW)
        pdf.text(lines, marginL, y)
        y += 2
        pdf.setDrawColor(...GOLD)
        pdf.setLineWidth(0.4)
        pdf.line(marginL, y + 2, W - marginR, y + 2)
        y += lines.length * 6 + 6
        break
      }
      case 'h3': {
        ensureSpace(10)
        pdf.setFontSize(11)
        pdf.setFont('helvetica', 'bold')
        pdf.setTextColor(...LIGHT)
        const lines = pdf.splitTextToSize(block.text, contentW)
        pdf.text(lines, marginL, y)
        y += lines.length * 5.5 + 4
        break
      }
      case 'h4': {
        ensureSpace(8)
        pdf.setFontSize(10)
        pdf.setFont('helvetica', 'bold')
        pdf.setTextColor(...MUTED)
        pdf.text(block.text, marginL, y)
        y += 5 + 3
        break
      }
      case 'bold': {
        ensureSpace(8)
        pdf.setFontSize(10)
        pdf.setFont('helvetica', 'bold')
        pdf.setTextColor(...LIGHT)
        const lines = pdf.splitTextToSize(block.text, contentW)
        pdf.text(lines, marginL, y)
        y += lines.length * 5 + 2
        break
      }
      case 'bullet': {
        const bulletLines = pdf.splitTextToSize(block.text, contentW - 10)
        ensureSpace(bulletLines.length * lineGap + 3)
        pdf.setFontSize(9.5)
        pdf.setFont('helvetica', 'normal')
        pdf.setTextColor(...MUTED)
        // Gold bullet dot
        pdf.setFillColor(...GOLD)
        pdf.circle(marginL + 2, y - 1.5, 1.2, 'F')
        pdf.text(bulletLines, marginL + 8, y)
        y += bulletLines.length * lineGap + 2
        break
      }
      case 'numbered': {
        const numLines = pdf.splitTextToSize(block.text, contentW - 10)
        ensureSpace(numLines.length * lineGap + 3)
        pdf.setFontSize(9.5)
        pdf.setFont('helvetica', 'normal')
        pdf.setTextColor(...MUTED)
        pdf.text(numLines, marginL + 8, y)
        y += numLines.length * lineGap + 2
        break
      }
      case 'p': {
        if (!block.text.trim()) { y += 2; break }
        const pLines = pdf.splitTextToSize(block.text, contentW)
        ensureSpace(pLines.length * lineGap + 2)
        pdf.setFontSize(9.5)
        pdf.setFont('helvetica', 'normal')
        pdf.setTextColor(...MUTED)
        pdf.text(pLines, marginL, y)
        y += pLines.length * lineGap + 2
        break
      }
    }
  }
}

/**
 * Draws the Risk Profiles summary table on a new page.
 */
function drawRiskTable(pdf: jsPDF, profiles: any[]) {
  if (!profiles || profiles.length === 0) return

  pdf.addPage()
  const W = pdf.internal.pageSize.getWidth()
  const H = pdf.internal.pageSize.getHeight()

  pdf.setFillColor(...DARK)
  pdf.rect(0, 0, W, H, 'F')
  pdf.setFillColor(...GOLD)
  pdf.rect(0, 0, 4, H, 'F')

  let y = 28
  const marginL = 20

  // Section header
  pdf.setFontSize(14)
  pdf.setFont('helvetica', 'bold')
  pdf.setTextColor(...GOLD)
  pdf.text('SUSPECT RISK SUMMARY TABLE', marginL, y)
  y += 3
  pdf.setDrawColor(...GOLD)
  pdf.setLineWidth(0.4)
  pdf.line(marginL, y + 2, W - 20, y + 2)
  y += 12

  // Table header
  const colW = [60, 30, 22, 22, W - 20 - 60 - 30 - 22 - 22 - 20]
  const headers = ['Name / Identifiers', 'Risk Level', 'Score', 'Conf.', 'Triggered Rules']

  pdf.setFillColor(...MID)
  pdf.rect(marginL, y - 5, W - 40, 12, 'F')
  pdf.setFontSize(8)
  pdf.setFont('helvetica', 'bold')
  pdf.setTextColor(...GOLD)

  let xOff = marginL
  headers.forEach((h, i) => {
    pdf.text(h, xOff + 2, y + 1)
    xOff += colW[i]
  })
  y += 10

  profiles.slice(0, 20).forEach((p, idx) => {
    const rowH = 14
    if (y + rowH > H - 28) return

    // Alternate row shade
    if (idx % 2 === 0) {
      pdf.setFillColor(22, 21, 22)
      pdf.rect(marginL, y - 5, W - 40, rowH, 'F')
    }

    const color = riskColor(p.risk_score ?? 0)
    pdf.setFontSize(8)
    pdf.setFont('helvetica', 'normal')
    pdf.setTextColor(...MUTED)

    xOff = marginL
    // Name
    const nameText = pdf.splitTextToSize(p.name ?? p.person_id ?? '—', colW[0] - 4)
    pdf.text(nameText[0] ?? '—', xOff + 2, y + 1)
    xOff += colW[0]

    // Risk level badge
    pdf.setTextColor(...color)
    pdf.setFont('helvetica', 'bold')
    pdf.text(p.risk_level ?? '—', xOff + 2, y + 1)
    xOff += colW[1]

    // Score
    pdf.setTextColor(...color)
    pdf.text(`${(p.risk_score ?? 0).toFixed(0)}%`, xOff + 2, y + 1)
    xOff += colW[2]

    // Confidence
    pdf.setFont('helvetica', 'normal')
    pdf.setTextColor(...MUTED)
    pdf.text(`${(p.confidence ?? 0).toFixed(0)}%`, xOff + 2, y + 1)
    xOff += colW[3]

    // Rules
    const rules = (p.evidence ?? []).map((e: any) => e.rule_name).join(', ')
    const rulesLines = pdf.splitTextToSize(rules || '—', colW[4] - 4)
    pdf.text(rulesLines[0] ?? '—', xOff + 2, y + 1)

    y += rowH
  })

  // Footer
  pdf.setFillColor(...MID)
  pdf.rect(0, H - 20, W, 20, 'F')
  pdf.setFontSize(8)
  pdf.setFont('helvetica', 'normal')
  pdf.setTextColor(...MUTED)
  pdf.text('TATVA Forensic Report — CONFIDENTIAL', marginL, H - 8)
  const pageNum = pdf.getNumberOfPages()
  pdf.text(`Page ${pageNum}`, W - 20, H - 8, { align: 'right' })
}


// ── The Modal Component ──────────────────────────────────────────────────────

export default function ExportReportModal({ onClose, caseId }: ExportReportModalProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [progress, setProgress] = useState('')

  const handleExport = async () => {
    setLoading(true)
    setError(null)
    setProgress('Fetching forensic report from server...')

    try {
      const res = await fetch('http://localhost:8000/api/report/export')
      if (!res.ok) {
        throw new Error(`Server returned ${res.status}: ${res.statusText}. Run the pipeline first.`)
      }
      const payload: ReportPayload = await res.json()

      setProgress('Parsing investigation report...')
      const blocks = parseMarkdown(payload.report_markdown)

      setProgress('Initialising PDF renderer...')
      const pdf = new jsPDF({
        orientation: 'portrait',
        unit: 'mm',
        format: 'a4',
      })

      setProgress('Generating cover page...')
      drawCoverPage(pdf, caseId, payload.generated_at)

      setProgress('Rendering report narrative...')
      pdf.addPage()
      const W = pdf.internal.pageSize.getWidth()
      const H = pdf.internal.pageSize.getHeight()
      pdf.setFillColor(...DARK)
      pdf.rect(0, 0, W, H, 'F')
      pdf.setFillColor(...GOLD)
      pdf.rect(0, 0, 4, H, 'F')
      pdf.setFillColor(...MID)
      pdf.rect(0, H - 20, W, 20, 'F')
      pdf.setFontSize(8)
      pdf.setFont('helvetica', 'normal')
      pdf.setTextColor(...MUTED)
      pdf.text('TATVA Forensic Report — CONFIDENTIAL', 20, H - 8)
      pdf.text('Page 2', W - 20, H - 8, { align: 'right' })

      drawReportContent(pdf, blocks)

      setProgress('Generating risk summary table...')
      drawRiskTable(pdf, payload.risk_profiles)

      setProgress('Saving PDF file...')
      const dateStr = new Date().toISOString().slice(0, 10)
      pdf.save(`TATVA_ForensicReport_${caseId}_${dateStr}.pdf`)

      setProgress('Done!')
      setTimeout(() => {
        onClose()
      }, 800)
    } catch (err: any) {
      console.error('[ExportReport] Failed:', err)
      setError(err.message || 'Unknown error occurred')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-[999] flex items-center justify-center"
      style={{ background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(8px)' }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <div
        className="relative flex flex-col rounded-lg overflow-hidden"
        style={{
          background: '#131314',
          border: '1px solid rgba(254,183,0,0.3)',
          width: '480px',
          maxWidth: '95vw',
          boxShadow: '0 0 60px rgba(254,183,0,0.08)',
        }}
      >
        {/* Header */}
        <div
          className="flex items-center justify-between px-6 py-4 border-b"
          style={{ borderColor: 'rgba(254,183,0,0.2)', background: 'rgba(28,27,28,0.8)' }}
        >
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined" style={{ color: '#feb700', fontSize: '22px' }}>
              picture_as_pdf
            </span>
            <div>
              <div style={{ fontFamily: 'JetBrains Mono', fontSize: '13px', fontWeight: 700, color: '#feb700', letterSpacing: '0.08em' }}>
                EXPORT FORENSIC REPORT
              </div>
              <div style={{ fontFamily: 'JetBrains Mono', fontSize: '10px', color: '#bec7d4' }}>
                Gemini Intelligence Dossier → PDF
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="material-symbols-outlined hover:text-[#feb700] transition-colors"
            style={{ color: '#bec7d4', fontSize: '20px' }}
          >
            close
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-6 space-y-5">
          {/* Info cards */}
          <div className="space-y-3">
            {[
              { icon: 'psychology', label: 'AI Narrative', desc: 'Executive summary & full case analysis written by Gemini' },
              { icon: 'groups', label: 'Suspect Profiles', desc: 'Risk scores, triggered rules & graph centrality metrics' },
              { icon: 'timeline', label: 'Timeline Reconstruction', desc: 'Chronological sequence of suspicious events' },
              { icon: 'bar_chart', label: 'Network Topology', desc: 'Graph summary & entity relationship overview' },
            ].map(card => (
              <div
                key={card.icon}
                className="flex items-center gap-3 p-3 rounded"
                style={{ background: 'rgba(254,183,0,0.04)', border: '1px solid rgba(254,183,0,0.12)' }}
              >
                <span className="material-symbols-outlined" style={{ color: '#feb700', fontSize: '18px' }}>
                  {card.icon}
                </span>
                <div>
                  <div style={{ fontFamily: 'JetBrains Mono', fontSize: '11px', fontWeight: 700, color: '#ffdb9d' }}>
                    {card.label}
                  </div>
                  <div style={{ fontFamily: 'Geist', fontSize: '12px', color: '#bec7d4' }}>
                    {card.desc}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Progress / error */}
          {loading && (
            <div
              className="flex items-center gap-3 p-3 rounded animate-pulse"
              style={{ background: 'rgba(254,183,0,0.06)', border: '1px solid rgba(254,183,0,0.2)' }}
            >
              <div className="w-4 h-4 rounded-full border-2 border-[#feb700]/30 border-t-[#feb700] animate-spin flex-shrink-0" />
              <span style={{ fontFamily: 'JetBrains Mono', fontSize: '11px', color: '#ffdb9d' }}>
                {progress}
              </span>
            </div>
          )}

          {error && (
            <div
              className="flex items-start gap-3 p-3 rounded"
              style={{ background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.25)' }}
            >
              <span className="material-symbols-outlined flex-shrink-0" style={{ color: '#ef4444', fontSize: '18px' }}>
                error
              </span>
              <span style={{ fontFamily: 'Geist', fontSize: '12px', color: '#ffb4ab' }}>
                {error}
              </span>
            </div>
          )}

          {/* Export button */}
          <button
            onClick={handleExport}
            disabled={loading}
            className="w-full py-4 rounded-lg flex items-center justify-center gap-3 font-bold uppercase tracking-wider hover:brightness-110 active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            style={{
              background: loading ? 'rgba(254,183,0,0.5)' : '#feb700',
              color: '#412d00',
              fontFamily: 'JetBrains Mono',
              fontSize: '13px',
              boxShadow: loading ? 'none' : '0 0 20px rgba(254,183,0,0.25)',
            }}
          >
            <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>
              {loading ? 'hourglass_top' : 'download'}
            </span>
            {loading ? 'Generating PDF...' : 'Download PDF Report'}
          </button>

          <p style={{ fontFamily: 'JetBrains Mono', fontSize: '9px', color: '#bec7d4', textAlign: 'center', opacity: 0.6 }}>
            CLASSIFICATION: RESTRICTED · LAW ENFORCEMENT ONLY
          </p>
        </div>
      </div>
    </div>
  )
}
