import { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';

interface GraphNode extends d3.SimulationNodeDatum {
  id: string;
  name: string;
  type: string;
  val: string;
}

interface GraphLink extends d3.SimulationLinkDatum<GraphNode> {
  source: string | GraphNode;
  target: string | GraphNode;
  relation: string;
  confidence: number;
}

interface D3KnowledgeGraphProps {
  onNodeClick?: (node: GraphNode) => void;
}

export default function D3KnowledgeGraph({ onNodeClick }: D3KnowledgeGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [graphData, setGraphData] = useState<{ nodes: GraphNode[]; links: GraphLink[] } | null>(null);

  useEffect(() => {
    fetch('http://localhost:8000/api/graph')
      .then((res) => res.json())
      .then((data) => {
        // Map backend entities and relations to D3 nodes/links
        const masters = data.master_entities || [];
        const relations = data.relations || [];

        const nodes: GraphNode[] = masters.map((m: any) => {
          const resolved = m.resolved_values || [];
          let name = 'Unknown';
          for (const val of resolved) {
            if (!val.startsWith('acc') && !val.startsWith('twr') && !val.startsWith('98') && !val.startsWith('91') && !val.includes('@') && !/\d/.test(val)) {
              name = val.replace(/_/g, ' ');
              break;
            }
          }
          if (name === 'Unknown' && resolved.length > 0) {
            name = resolved[0].replace(/_/g, ' ');
          }
          return {
            id: m.master_id,
            name: name,
            type: m.master_type,
            val: resolved[0] || m.master_id,
          };
        });

        const links: GraphLink[] = relations.map((r: any) => ({
          source: r.source,
          target: r.target,
          relation: r.relation,
          confidence: r.confidence || 1.0,
        }));

        setGraphData({ nodes, links });
      })
      .catch((err) => console.error('Error loading graph data:', err));
  }, []);

  useEffect(() => {
    if (!graphData || !containerRef.current) return;

    // Clear previous graph
    containerRef.current.innerHTML = '';

    const width = containerRef.current.clientWidth || 800;
    const height = containerRef.current.clientHeight || 600;

    const svg = d3
      .select(containerRef.current)
      .append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', `0 0 ${width} ${height}`)
      .style('display', 'block');

    // Create a group for zoom functionality
    const g = svg.append('g');

    // Zoom handler
    const zoom = d3.zoom<SVGSVGElement, unknown>().on('zoom', (event) => {
      g.attr('transform', event.transform);
    });
    svg.call(zoom);

    // Forces setup
    const simulation = d3
      .forceSimulation<GraphNode>(graphData.nodes)
      .force(
        'link',
        d3
          .forceLink<GraphNode, GraphLink>(graphData.links)
          .id((d) => d.id)
          .distance(120)
      )
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(40));

    // Define marker arrows for relations
    svg
      .append('defs')
      .selectAll('marker')
      .data(['arrow'])
      .enter()
      .append('marker')
      .attr('id', (d) => d)
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 22) // Place arrow just at node boundary
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#3f4852');

    // Render links
    const link = g
      .append('g')
      .selectAll('line')
      .data(graphData.links)
      .enter()
      .append('line')
      .attr('stroke', '#3f4852')
      .attr('stroke-width', (d) => d.confidence * 2)
      .attr('stroke-opacity', 0.6)
      .attr('marker-end', 'url(#arrow)');

    // Link label text
    const linkText = g
      .append('g')
      .selectAll('text')
      .data(graphData.links)
      .enter()
      .append('text')
      .attr('fill', '#bec7d4')
      .attr('font-size', '8px')
      .attr('font-family', 'JetBrains Mono')
      .attr('text-anchor', 'middle')
      .text((d) => d.relation);

    // Node drag handlers
    const drag = (sim: d3.Simulation<GraphNode, undefined>) => {
      function dragstarted(event: any, d: GraphNode) {
        if (!event.active) sim.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      }
      function dragged(event: any, d: GraphNode) {
        d.fx = event.x;
        d.fy = event.y;
      }
      function dragended(event: any, d: GraphNode) {
        if (!event.active) sim.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      }
      return d3.drag<SVGGElement, GraphNode>().on('start', dragstarted).on('drag', dragged).on('end', dragended);
    };

    // Colors mapping
    const colorMap = (type: string) => {
      switch (type) {
        case 'PERSON':
          return '#feb700'; // Amber
        case 'PHONE':
          return '#98cbff'; // Light Blue
        case 'BANK_ACCOUNT':
          return '#00a3ff'; // Bright Blue
        case 'TOWER':
          return '#ffb3ae'; // Light Crimson
        default:
          return '#bec7d4'; // Gray
      }
    };

    // Render Nodes
    const node = g
      .append('g')
      .selectAll('g')
      .data(graphData.nodes)
      .enter()
      .append('g')
      .call(drag(simulation) as any)
      .on('click', (_event, d) => {
        if (onNodeClick) onNodeClick(d);
      })
      .style('cursor', 'pointer');

    // Draw node circles
    node
      .append('circle')
      .attr('r', 12)
      .attr('fill', (d) => colorMap(d.type))
      .attr('stroke', '#131314')
      .attr('stroke-width', 2)
      .attr('class', 'transition-all duration-300')
      .style('filter', (d) => `drop-shadow(0 0 6px ${colorMap(d.type)}80)`);

    // Draw type indicator icons/initials
    node
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '.3em')
      .attr('fill', '#131314')
      .attr('font-size', '8px')
      .attr('font-weight', 'bold')
      .attr('font-family', 'JetBrains Mono')
      .text((d) => d.type.substring(0, 1));

    // Draw node text labels
    node
      .append('text')
      .attr('dx', 16)
      .attr('dy', '.35em')
      .attr('fill', '#e5e2e3')
      .attr('font-size', '10px')
      .attr('font-family', 'Geist')
      .text((d) => d.name);

    // Update positions on tick
    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      linkText
        .attr('x', (d: any) => ((d.source.x + d.target.x) / 2))
        .attr('y', (d: any) => ((d.source.y + d.target.y) / 2) - 4);

      node.attr('transform', (d: any) => `translate(${d.x},${d.y})`);
    });

    // Clean up simulation on unmount
    return () => {
      simulation.stop();
    };
  }, [graphData]);

  return (
    <div className="w-full h-full relative" style={{ background: '#0a0a0b' }}>
      <div ref={containerRef} className="w-full h-full" />
      <div className="absolute bottom-4 left-4 flex gap-4 text-xs font-mono bg-black/60 p-3 rounded border border-[#3f4852]/30 backdrop-blur-md">
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-[#feb700]" /> Person
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-[#98cbff]" /> Phone
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-[#00a3ff]" /> Account
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-[#ffb3ae]" /> Tower
        </div>
      </div>
    </div>
  );
}
