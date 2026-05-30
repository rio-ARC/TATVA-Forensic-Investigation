import { useEffect, useRef, useState, useCallback } from 'react';
import ForceGraph3D from 'react-force-graph-3d';
import * as THREE from 'three';

// ─────────────────────────────────────────────────────────────────────────────
// Types — mirrors the backend GraphRenderPayload schema exactly.
// No entity resolution logic lives here. The backend sends ready-to-render data.
// ─────────────────────────────────────────────────────────────────────────────

export interface RenderNode {
  id: string;
  label: string;
  type: string;      // master_type: PERSON | PLACE | INFRASTRUCTURE | ENTITY
  sub_type: string;  // entity_types[0]: ACCOUNT | CELL_TOWER | VEHICLE | …
  risk_score: number;
  // Added by react-force-graph-3d at runtime (do not set manually)
  x?: number;
  y?: number;
  z?: number;
}

export interface RenderLink {
  source: string | RenderNode;
  target: string | RenderNode;
  type: string;
  confidence: number;
}

interface GraphRenderPayload {
  nodes: RenderNode[];
  links: RenderLink[];
}

interface ForceGraphKnowledgeGraphProps {
  onNodeClick?: (node: { id: string; name: string; type: string; val: string }) => void;
}

// ─────────────────────────────────────────────────────────────────────────────
// Colour mappings — covers every master_type / sub_type combo in unified_graph
// ─────────────────────────────────────────────────────────────────────────────

function nodeColor(node: RenderNode): string {
  if (node.type === 'PERSON')         return '#feb700';   // Amber  — persons / suspects
  if (node.type === 'PLACE')          return '#98ff8f';   // Green  — locations
  if (node.type === 'INFRASTRUCTURE') {
    if (node.sub_type === 'CELL_TOWER') return '#98cbff'; // Light Blue — towers
    if (node.sub_type === 'CAMERA')     return '#ff6b6b'; // Red    — cameras
    if (node.sub_type === 'PLATFORM')   return '#c084fc'; // Purple — platforms
    return '#98cbff';
  }
  if (node.type === 'ENTITY') {
    if (node.sub_type === 'ACCOUNT')        return '#00a3ff'; // Blue   — bank accounts
    if (node.sub_type === 'VEHICLE')        return '#ffb4ab'; // Pink   — vehicles
    if (node.sub_type === 'TRACKER')        return '#e879f9'; // Fuchsia— trackers
    if (node.sub_type === 'EMAIL_ADDRESS')  return '#6ee7b7'; // Teal   — emails
    if (node.sub_type === 'WEARABLE_DEVICE') return '#fcd34d'; // Yellow — wearables
    return '#bec7d4';
  }
  return '#bec7d4'; // Default grey
}

function linkColor(link: RenderLink): string {
  switch (link.type) {
    case 'CALLED':                return '#98cbff';
    case 'TRANSFERRED_TO':        return '#feb700';
    case 'TRANSFERRED_MONEY':     return '#feb700';
    case 'CONNECTED_TO_TOWER':    return '#6ee7b7';
    case 'LOCATED_AT':            return '#98ff8f';
    case 'MOVED_TO':              return '#98ff8f';
    case 'DETECTED':              return '#ff6b6b';
    case 'MESSAGED':              return '#c084fc';
    case 'EMAILED':               return '#c084fc';
    case 'OWNS_ACCOUNT':          return '#00a3ff';
    case 'ASSOCIATED_WITH':       return '#fcd34d';
    default:                      return '#3f4852';
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Node size — risk_score-driven (0 → 4, 99 → 12)
// ─────────────────────────────────────────────────────────────────────────────

function nodeSize(node: RenderNode): number {
  const base = 4;
  const bonus = (node.risk_score / 100) * 8;
  return base + bonus;
}

// ─────────────────────────────────────────────────────────────────────────────
// Legend items derived from the colour map
// ─────────────────────────────────────────────────────────────────────────────

const LEGEND = [
  { color: '#feb700', label: 'Person / Suspect' },
  { color: '#98ff8f', label: 'Location' },
  { color: '#00a3ff', label: 'Bank Account' },
  { color: '#98cbff', label: 'Cell Tower' },
  { color: '#ffb4ab', label: 'Vehicle' },
  { color: '#ff6b6b', label: 'Camera' },
  { color: '#c084fc', label: 'Platform' },
  { color: '#6ee7b7', label: 'Email / Tracker' },
];

// ─────────────────────────────────────────────────────────────────────────────
// Component
// ─────────────────────────────────────────────────────────────────────────────

export default function ForceGraphKnowledgeGraph({ onNodeClick }: ForceGraphKnowledgeGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [graphData, setGraphData] = useState<GraphRenderPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hoveredNode, setHoveredNode] = useState<RenderNode | null>(null);

  // Track container size
  useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setDimensions({
          width: entry.contentRect.width,
          height: entry.contentRect.height,
        });
      }
    });
    observer.observe(containerRef.current);
    setDimensions({
      width: containerRef.current.clientWidth,
      height: containerRef.current.clientHeight,
    });
    return () => observer.disconnect();
  }, []);

  // Fetch clean visualization data from backend
  useEffect(() => {
    setLoading(true);
    setError(null);
    fetch('http://localhost:8000/graph/render')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        return res.json();
      })
      .then((data: GraphRenderPayload) => {
        setGraphData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('[ForceGraphKnowledgeGraph] Failed to load graph:', err);
        setError(err.message);
        setLoading(false);
      });
  }, []);

  // Node click handler — maps RenderNode to the shape InvestigationPage expects
  const handleNodeClick = useCallback((node: object) => {
    const n = node as RenderNode;
    if (onNodeClick) {
      onNodeClick({
        id: n.id,
        name: n.label,
        type: n.type,
        val: n.sub_type,
      });
    }
  }, [onNodeClick]);

  // Custom node 3D object — sphere with glow
  const nodeThreeObject = useCallback((node: object) => {
    const n = node as RenderNode;
    const radius = nodeSize(n);
    const color = nodeColor(n);

    const geometry = new THREE.SphereGeometry(radius, 16, 16);
    const material = new THREE.MeshPhongMaterial({
      color: new THREE.Color(color),
      emissive: new THREE.Color(color),
      emissiveIntensity: n.risk_score > 50 ? 0.6 : 0.25,
      shininess: 80,
      transparent: true,
      opacity: 0.92,
    });
    return new THREE.Mesh(geometry, material);
  }, []);

  return (
    <div
      ref={containerRef}
      className="w-full h-full relative"
      style={{ background: '#0a0a0b' }}
    >
      {/* Loading state */}
      {loading && (
        <div className="absolute inset-0 flex flex-col items-center justify-center z-20">
          <div
            className="w-12 h-12 rounded-full border-2 border-[#feb700]/30 border-t-[#feb700] animate-spin mb-4"
          />
          <span style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#bec7d4' }}>
            LOADING KNOWLEDGE GRAPH…
          </span>
        </div>
      )}

      {/* Error state */}
      {error && !loading && (
        <div className="absolute inset-0 flex flex-col items-center justify-center z-20">
          <span className="material-symbols-outlined text-[#ffb4ab] text-4xl mb-3">error</span>
          <span style={{ fontFamily: 'JetBrains Mono', fontSize: '12px', color: '#ffb4ab' }}>
            GRAPH LOAD FAILED
          </span>
          <span style={{ fontFamily: 'JetBrains Mono', fontSize: '10px', color: '#bec7d4', marginTop: '8px' }}>
            {error}
          </span>
          <span style={{ fontFamily: 'JetBrains Mono', fontSize: '10px', color: '#bec7d4' }}>
            Ensure backend is running on port 8000
          </span>
        </div>
      )}

      {/* Force Graph */}
      {graphData && !loading && (
        <ForceGraph3D
          width={dimensions.width}
          height={dimensions.height}
          graphData={graphData}
          backgroundColor="#0a0a0b"
          // Nodes
          nodeThreeObject={nodeThreeObject}
          nodeThreeObjectExtend={false}
          onNodeClick={handleNodeClick}
          onNodeHover={(node) => setHoveredNode(node ? (node as RenderNode) : null)}
          // Links
          linkColor={(link) => linkColor(link as RenderLink)}
          linkWidth={(link) => ((link as RenderLink).confidence ?? 1) * 1.5}
          linkOpacity={0.5}
          linkDirectionalParticles={2}
          linkDirectionalParticleWidth={(link) => {
            const l = link as RenderLink;
            return l.type === 'TRANSFERRED_TO' || l.type === 'TRANSFERRED_MONEY' ? 2.5 : 1.5;
          }}
          linkDirectionalParticleColor={(link) => linkColor(link as RenderLink)}
          linkDirectionalParticleSpeed={0.004}
          // Physics
          d3AlphaDecay={0.02}
          d3VelocityDecay={0.3}
          // Lighting is handled by ThreeJS defaults (point light)
          showNavInfo={false}
        />
      )}

      {/* Hover tooltip */}
      {hoveredNode && (
        <div
          className="absolute pointer-events-none z-20 glass-panel rounded px-3 py-2 border border-[#3f4852]/50"
          style={{
            top: 80,
            left: '50%',
            transform: 'translateX(-50%)',
            backdropFilter: 'blur(12px)',
            maxWidth: 280,
          }}
        >
          <div style={{ fontFamily: 'Geist', fontSize: '14px', fontWeight: '600', color: '#e5e2e3' }}>
            {hoveredNode.label}
          </div>
          <div style={{ fontFamily: 'JetBrains Mono', fontSize: '10px', color: '#bec7d4', marginTop: '2px' }}>
            {hoveredNode.type} / {hoveredNode.sub_type}
          </div>
          {hoveredNode.risk_score > 0 && (
            <div style={{ fontFamily: 'JetBrains Mono', fontSize: '10px', color: '#ffb4ab', marginTop: '4px', fontWeight: 'bold' }}>
              RISK: {hoveredNode.risk_score.toFixed(1)}%
            </div>
          )}
        </div>
      )}

      {/* Legend */}
      <div
        className="absolute bottom-4 left-4 glass-panel rounded border border-[#3f4852]/30 z-10"
        style={{ padding: '10px 12px', backdropFilter: 'blur(12px)' }}
      >
        <div style={{ fontFamily: 'JetBrains Mono', fontSize: '9px', color: '#bec7d4', marginBottom: '6px', letterSpacing: '0.1em' }}>
          ENTITY TYPES
        </div>
        <div className="grid grid-cols-2 gap-x-4 gap-y-1">
          {LEGEND.map(({ color, label }) => (
            <div key={label} className="flex items-center gap-1.5">
              <span
                className="flex-shrink-0 rounded-full"
                style={{ width: 8, height: 8, background: color, boxShadow: `0 0 4px ${color}80` }}
              />
              <span style={{ fontFamily: 'JetBrains Mono', fontSize: '9px', color: '#bec7d4' }}>{label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Node count overlay */}
      {graphData && (
        <div
          className="absolute top-4 left-4 glass-panel rounded px-2 py-1 z-10"
          style={{ backdropFilter: 'blur(8px)', border: '1px solid rgba(254,183,0,0.15)' }}
        >
          <span style={{ fontFamily: 'JetBrains Mono', fontSize: '10px', color: '#ffdb9d' }}>
            {graphData.nodes.length} ENTITIES · {graphData.links.length} LINKS
          </span>
        </div>
      )}
    </div>
  );
}
