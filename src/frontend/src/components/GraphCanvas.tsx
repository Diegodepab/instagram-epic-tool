import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import type { ForceGraphMethods, NodeObject } from 'react-force-graph-2d';
import { forceCollide, forceX, forceY } from 'd3-force';
import type { ForceLink, ForceManyBody } from 'd3-force';
import type { GraphLink, GraphNode, InternalGraphState, RelationshipKind } from '../types/domain';

interface GraphCanvasProps {
  graphData: InternalGraphState;
  search: string;
  layout: GraphLayout;
  onNodeExpand: (nodeId: string) => void;
  onNodeSelect: (node: GraphNode) => void;
}

export type GraphLayout = 'groups' | 'free';

const colors: Record<RelationshipKind, string> = {
  root: '#f97367',
  mutual: '#36c690',
  follower_only: '#8b7cf6',
  following_only: '#f3aa52',
};

const renderedEndpointId = (endpoint: unknown): string => {
  if (typeof endpoint === 'object' && endpoint !== null && 'id' in endpoint) {
    return String(endpoint.id);
  }
  return String(endpoint ?? '');
};

export function GraphCanvas({ graphData, search, layout, onNodeExpand, onNodeSelect }: GraphCanvasProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const graphRef = useRef<ForceGraphMethods<GraphNode> | undefined>(undefined);
  const [size, setSize] = useState({ width: 800, height: 600 });
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver(([entry]) => {
      setSize({ width: entry.contentRect.width, height: entry.contentRect.height });
    });
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const graph = graphRef.current;
    if (!graph) return;

    const profileCount = graphData.nodes.length;
    const charge = graph.d3Force('charge') as ForceManyBody<GraphNode> | undefined;
    charge?.strength(profileCount > 400 ? -360 : -240).distanceMax(900);

    const link = graph.d3Force('link') as ForceLink<GraphNode, GraphLink> | undefined;
    link?.distance(profileCount > 400 ? 72 : 56).strength(0.12);

    graph.d3Force('collide', forceCollide<GraphNode>()
      .radius((node) => Math.sqrt(5 + Math.min(node.degree, 20) * 0.35) * 4 + 5)
      .strength(0.95)
      .iterations(2));

    if (layout === 'groups') {
      const anchorX: Record<RelationshipKind, number> = {
        root: 0,
        mutual: 0,
        follower_only: -Math.min(size.width * 0.25, 260),
        following_only: Math.min(size.width * 0.25, 260),
      };
      const anchorY: Record<RelationshipKind, number> = {
        root: 0,
        mutual: -Math.min(size.height * 0.22, 150),
        follower_only: Math.min(size.height * 0.15, 110),
        following_only: Math.min(size.height * 0.15, 110),
      };
      graph.d3Force('group-x', forceX<GraphNode>((node) => anchorX[node.metadata.relation ?? 'following_only']).strength(0.18));
      graph.d3Force('group-y', forceY<GraphNode>((node) => anchorY[node.metadata.relation ?? 'following_only']).strength(0.18));
    } else {
      graph.d3Force('group-x', null);
      graph.d3Force('group-y', null);
    }
    graph.d3ReheatSimulation();
  }, [graphData.nodes.length, layout, size.height, size.width]);

  const normalizedSearch = search.trim().toLowerCase();
  const matchingIds = useMemo(() => new Set(
    normalizedSearch
      ? graphData.nodes.filter((node) => node.id.includes(normalizedSearch)).map((node) => node.id)
      : [],
  ), [graphData.nodes, normalizedSearch]);

  useEffect(() => {
    if (!normalizedSearch || matchingIds.size === 0) return;
    const match = graphData.nodes.find((node) => matchingIds.has(node.id));
    if (match?.x !== undefined && match.y !== undefined) {
      graphRef.current?.centerAt(match.x, match.y, 500);
      graphRef.current?.zoom(3.2, 500);
    }
  }, [graphData.nodes, matchingIds, normalizedSearch]);

  const handleClick = useCallback((node: NodeObject<GraphNode>) => {
    setSelectedId(node.id);
    onNodeSelect(node);
    graphRef.current?.centerAt(node.x, node.y, 650);
    graphRef.current?.zoom(3.4, 650);
    if (!node.is_expanded && node.metadata.has_imported_data === true) onNodeExpand(node.id);
  }, [onNodeExpand, onNodeSelect]);

  const focusedIds = useMemo(() => {
    if (!selectedId) return null;
    const ids = new Set([selectedId]);
    graphData.links.forEach((edge) => {
      const source = typeof edge.source === 'string' ? edge.source : edge.source.id;
      const target = typeof edge.target === 'string' ? edge.target : edge.target.id;
      if (source === selectedId) ids.add(target);
      if (target === selectedId) ids.add(source);
    });
    return ids;
  }, [graphData.links, selectedId]);

  return (
    <div className="graph-canvas" ref={containerRef}>
      <ForceGraph2D
        ref={graphRef}
        width={size.width}
        height={size.height}
        graphData={graphData}
        nodeId="id"
        nodeColor={(node) => focusedIds && !focusedIds.has(node.id)
          ? 'rgba(181, 189, 205, 0.28)'
          : colors[node.metadata.relation ?? 'following_only']}
        nodeVal={(node) => (node.id === selectedId ? 9 : 5) + Math.min(node.degree, 20) * 0.35}
        nodeRelSize={4}
        nodeCanvasObjectMode={() => 'after'}
        nodeCanvasObject={(node, context, scale) => {
          const hasImportedData = node.metadata.has_imported_data === true;
          if (!matchingIds.has(node.id) && node.id !== selectedId && !hasImportedData) return;
          context.beginPath();
          context.arc(node.x ?? 0, node.y ?? 0, 10, 0, Math.PI * 2);
          context.strokeStyle = node.id === selectedId
            ? '#273454'
            : hasImportedData ? '#126d50' : '#ffffff';
          context.lineWidth = 3 / scale;
          context.stroke();
        }}
        onNodeClick={handleClick}
        nodeLabel={(node) => `${node.username} · ${node.degree} conexiones conocidas${node.metadata.has_imported_data === true ? ' · red importada' : ''}`}
        linkDirectionalArrowLength={3}
        linkDirectionalArrowRelPos={1}
        linkLabel={(edge) => edge.since_timestamp
          ? `Conexión registrada desde ${new Date(edge.since_timestamp * 1000).toLocaleDateString('es-ES')}`
          : 'Conexión incluida en una exportación autorizada'}
        linkWidth={0.8}
        linkColor={(edge) => {
          if (!selectedId) return 'rgba(134, 154, 190, 0.28)';
          const source = renderedEndpointId(edge.source);
          const target = renderedEndpointId(edge.target);
          return source === selectedId || target === selectedId
            ? 'rgba(82, 100, 145, 0.72)'
            : 'rgba(170, 178, 194, 0.08)';
        }}
        backgroundColor="#f8fafc"
        cooldownTicks={180}
        d3AlphaDecay={0.035}
        d3VelocityDecay={0.28}
        onEngineStop={() => graphRef.current?.zoomToFit(500, 70)}
      />
      <button className="fit-graph-button" onClick={() => graphRef.current?.zoomToFit(500, 70)}>Ajustar mapa</button>
      <div className="graph-hint">Haz clic en una persona para explorar sus conexiones conocidas</div>
    </div>
  );
}
