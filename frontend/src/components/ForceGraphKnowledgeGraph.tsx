import { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import ForceGraph3D from 'react-force-graph-3d';
import * as THREE from 'three';
import type { RenderNode, RenderLink, GraphRenderPayload, AssessmentsMap, EntityStatus } from '../types/graph';

// Re-export for any legacy import sites that imported RenderNode from here.
export type { RenderNode, RenderLink, GraphRenderPayload };

// ─────────────────────────────────────────────────────────────────────────────
// Props
// ─────────────────────────────────────────────────────────────────────────────

interface ForceGraphKnowledgeGraphProps {
  /** Pre-filtered graph data from InvestigationPage. May be null while loading. */
  graphData: GraphRenderPayload | null;
  loading?: boolean;
  error?: string | null;
  onNodeClick?: (node: { id: string; name: string; type: string; val: string }) => void;
  /** Investigator assessments map — keyed by entity_id */
  assessments?: AssessmentsMap;
  /** Whether to render CLEARED nodes. Default: true */
  showCleared?: boolean;
  /** Called when the Show Cleared toggle is flipped inside the component */
  onToggleCleared?: (show: boolean) => void;
}

// ─────────────────────────────────────────────────────────────────────────────
// Status → visual configuration
// ─────────────────────────────────────────────────────────────────────────────

interface StatusVisual {
  color: string;
  emissiveIntensity: number;
  opacity: number;
  sizeMod: number; // added to base + risk-bonus
}

const STATUS_VISUALS: Record<EntityStatus, StatusVisual> = {
  ACTIVE:             { color: '',       emissiveIntensity: -1,   opacity: 0.92, sizeMod: 0  },  // '' = use type-based color
  CLEARED:            { color: '#6b7280', emissiveIntensity: 0.05, opacity: 0.30, sizeMod: -2 },
  PERSON_OF_INTEREST: { color: '#f97316', emissiveIntensity: 0.70, opacity: 0.95, sizeMod: 4  },
  PRIORITY_TARGET:    { color: '#ef4444', emissiveIntensity: 1.0,  opacity: 1.0,  sizeMod: 8  },
};

// ─────────────────────────────────────────────────────────────────────────────
// Colour mappings — covers every master_type / sub_type combo in unified_graph
// ─────────────────────────────────────────────────────────────────────────────

function typeColor(node: RenderNode): string {
  if (node.type === 'PERSON')         return '#feb700';
  if (node.type === 'PLACE')          return '#98ff8f';
  if (node.type === 'INFRASTRUCTURE') {
    if (node.sub_type === 'CELL_TOWER') return '#98cbff';
    if (node.sub_type === 'CAMERA')     return '#ff6b6b';
    if (node.sub_type === 'PLATFORM')   return '#c084fc';
    return '#98cbff';
  }
  if (node.type === 'ENTITY') {
    if (node.sub_type === 'ACCOUNT')         return '#00a3ff';
    if (node.sub_type === 'VEHICLE')         return '#ffb4ab';
    if (node.sub_type === 'TRACKER')         return '#e879f9';
    if (node.sub_type === 'EMAIL_ADDRESS')   return '#6ee7b7';
    if (node.sub_type === 'WEARABLE_DEVICE') return '#fcd34d';
    return '#bec7d4';
  }
  return '#bec7d4';
}

function nodeColor(node: RenderNode, status: EntityStatus): string {
  const vis = STATUS_VISUALS[status];
  return vis.color || typeColor(node);
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
// Node size — risk_score-driven + status modifier
// ─────────────────────────────────────────────────────────────────────────────

function nodeSize(node: RenderNode, status: EntityStatus): number {
  const base = 4;
  const riskBonus = (node.risk_score / 100) * 8;
  const statusMod = STATUS_VISUALS[status].sizeMod;
  return Math.max(2, base + riskBonus + statusMod);
}

// ─────────────────────────────────────────────────────────────────────────────
// Helper: get entity status from assessments map
// ─────────────────────────────────────────────────────────────────────────────

function getStatus(node: RenderNode, assessments: AssessmentsMap): EntityStatus {
  return (assessments[node.id]?.status as EntityStatus) ?? 'ACTIVE';
}

// ─────────────────────────────────────────────────────────────────────────────
// Legend items
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

export default function ForceGraphKnowledgeGraph({
  graphData,
  loading = false,
  error = null,
  onNodeClick,
  assessments = {},
  showCleared = true,
  onToggleCleared,
}: ForceGraphKnowledgeGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
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

  // Apply showCleared filter — purely presentational, graphData prop is never mutated
  const visibleGraphData = useMemo(() => {
    if (!graphData) return null;
    if (showCleared) return graphData;

    const clearedIds = new Set(
      Object.entries(assessments)
        .filter(([, a]) => a.status === 'CLEARED')
        .map(([id]) => id)
    );
    if (clearedIds.size === 0) return graphData;

    const nodes = graphData.nodes.filter(n => !clearedIds.has(n.id));
    const visibleIds = new Set(nodes.map(n => n.id));
    const links = graphData.links.filter(l => {
      const src = typeof l.source === 'string' ? l.source : l.source.id;
      const tgt = typeof l.target === 'string' ? l.target : l.target.id;
      return visibleIds.has(src) && visibleIds.has(tgt);
    });
    return { nodes, links };
  }, [graphData, showCleared, assessments]);

  // Node click handler
  const handleNodeClick = useCallback((node: object) => {
    const n = node as RenderNode;
    if (onNodeClick) {
      onNodeClick({ id: n.id, name: n.label, type: n.type, val: n.sub_type });
    }
  }, [onNodeClick]);

  // Custom node 3D object — sphere with assessment-aware glow
  const nodeThreeObject = useCallback((node: object) => {
    const n = node as RenderNode;
    const status = getStatus(n, assessments);
    const vis = STATUS_VISUALS[status];
    const radius = nodeSize(n, status);
    const color = nodeColor(n, status);

    const geometry = new THREE.SphereGeometry(radius, 16, 16);
    const material = new THREE.MeshPhongMaterial({
      color: new THREE.Color(color),
      emissive: new THREE.Color(color),
      emissiveIntensity: vis.emissiveIntensity < 0
        ? (n.risk_score > 50 ? 0.6 : 0.25)  // ACTIVE: use risk-score default
        : vis.emissiveIntensity,
      shininess: status === 'PRIORITY_TARGET' ? 120 : 80,
      transparent: true,
      opacity: vis.opacity,
    });
    return new THREE.Mesh(geometry, material);
  }, [assessments]);

  // Link directional particles — stop for CLEARED links
  const getLinkParticleSpeed = useCallback((link: object) => {
    const l = link as RenderLink;
    const src = typeof l.source === 'string' ? l.source : l.source.id;
    const tgt = typeof l.target === 'string' ? l.target : l.target.id;
    if (assessments[src]?.status === 'CLEARED' || assessments[tgt]?.status === 'CLEARED') return 0;
    return 0.004;
  }, [assessments]);

  // Link dash pattern — dashed Three.js line for edges connected to CLEARED nodes
  const getLinkThreeObject = useCallback((link: object) => {
    const l = link as RenderLink;
    const src = typeof l.source === 'string' ? l.source : (l.source as RenderNode).id;
    const tgt = typeof l.target === 'string' ? l.target : (l.target as RenderNode).id;
    const isCleared =
      assessments[src]?.status === 'CLEARED' || assessments[tgt]?.status === 'CLEARED';
    if (!isCleared) return undefined as any; // let ForceGraph3D use its default rendering

    const material = new THREE.LineDashedMaterial({
      color: new THREE.Color('#6b7280'),
      dashSize: 3,
      gapSize: 3,
      opacity: 0.3,
      transparent: true,
    });
    const geometry = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(0, 0, 0),
      new THREE.Vector3(1, 0, 0),
    ]);
    const line = new THREE.Line(geometry, material);
    line.computeLineDistances(); // required for dashes to render
    return line;
  }, [assessments]);


  const clearedCount = Object.values(assessments).filter(a => a.status === 'CLEARED').length;

  return (
    <div
      ref={containerRef}
      className="w-full h-full relative"
      style={{ background: '#0a0a0b' }}
    >
      {/* Show Cleared Toggle — top center */}
      <div
        className="absolute top-4 left-1/2 -translate-x-1/2 z-20 flex items-center gap-2 glass-panel rounded-full px-3 py-1.5 border border-[#3f4852]/40"
        style={{ backdropFilter: 'blur(12px)' }}
      >
        <button
          onClick={() => onToggleCleared?.(!showCleared)}
          className="flex items-center gap-2"
          title={showCleared ? 'Click to hide cleared entities' : 'Click to show cleared entities'}
        >
          <span
            className="w-3.5 h-3.5 rounded-sm border flex items-center justify-center flex-shrink-0 transition-all"
            style={{
              borderColor: showCleared ? '#feb700' : '#3f4852',
              background: showCleared ? '#feb700' : 'transparent',
            }}
          >
            {showCleared && <span className="material-symbols-outlined" style={{ fontSize: '10px', color: '#412d00', fontWeight: 900 }}>check</span>}
          </span>
          <span style={{ fontFamily: 'JetBrains Mono', fontSize: '10px', color: showCleared ? '#ffdb9d' : '#bec7d4', letterSpacing: '0.05em' }}>
            SHOW CLEARED
          </span>
        </button>
        {clearedCount > 0 && (
          <span
            className="px-1.5 py-0.5 rounded text-[9px] font-bold"
            style={{ background: 'rgba(107,114,128,0.3)', color: '#9ca3af', fontFamily: 'JetBrains Mono' }}
          >
            {clearedCount}
          </span>
        )}
      </div>

      {/* Loading state */}
      {loading && (
        <div className="absolute inset-0 flex flex-col items-center justify-center z-20">
          <div className="w-12 h-12 rounded-full border-2 border-[#feb700]/30 border-t-[#feb700] animate-spin mb-4" />
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
      {visibleGraphData && !loading && (
        <ForceGraph3D
          width={dimensions.width}
          height={dimensions.height}
          graphData={visibleGraphData}
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
          linkDirectionalParticleSpeed={getLinkParticleSpeed}
          linkThreeObject={getLinkThreeObject}
          linkPositionUpdate={(line, { start, end }) => {
            // Only reposition our custom dashed lines; null objects are handled by default
            if (!line) return false;
            const l = line as THREE.Line;
            const positions = new Float32Array([
              start.x, start.y, start.z,
              end.x, end.y, end.z,
            ]);
            l.geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
            l.geometry.computeBoundingSphere();
            l.computeLineDistances();
            return true;
          }}
          // Physics
          d3AlphaDecay={0.02}
          d3VelocityDecay={0.3}
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
          {assessments[hoveredNode.id] && assessments[hoveredNode.id].status !== 'ACTIVE' && (
            <div style={{ fontFamily: 'JetBrains Mono', fontSize: '10px', marginTop: '4px', fontWeight: 'bold', color:
              assessments[hoveredNode.id].status === 'CLEARED' ? '#9ca3af' :
              assessments[hoveredNode.id].status === 'PERSON_OF_INTEREST' ? '#f97316' : '#ef4444'
            }}>
              ● {assessments[hoveredNode.id].status?.replace(/_/g, ' ')}
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
        {/* Status legend */}
        <div style={{ fontFamily: 'JetBrains Mono', fontSize: '9px', color: '#bec7d4', marginTop: '8px', marginBottom: '4px', letterSpacing: '0.1em' }}>
          ASSESSMENT STATUS
        </div>
        <div className="space-y-1">
          {[
            { color: '#6b7280', label: 'Cleared' },
            { color: '#f97316', label: 'Person of Interest' },
            { color: '#ef4444', label: 'Priority Target' },
          ].map(({ color, label }) => (
            <div key={label} className="flex items-center gap-1.5">
              <span className="flex-shrink-0 rounded-full" style={{ width: 8, height: 8, background: color, boxShadow: `0 0 4px ${color}80` }} />
              <span style={{ fontFamily: 'JetBrains Mono', fontSize: '9px', color: '#bec7d4' }}>{label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Node count overlay */}
      {visibleGraphData && (
        <div
          className="absolute top-4 left-4 glass-panel rounded px-2 py-1 z-10"
          style={{ backdropFilter: 'blur(8px)', border: '1px solid rgba(254,183,0,0.15)' }}
        >
          <span style={{ fontFamily: 'JetBrains Mono', fontSize: '10px', color: '#ffdb9d' }}>
            {visibleGraphData.nodes.length} ENTITIES · {visibleGraphData.links.length} LINKS
          </span>
        </div>
      )}
    </div>
  );
}
