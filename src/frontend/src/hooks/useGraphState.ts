import { useCallback, useState } from 'react';
import { api } from '../services/api';
import type { APIGraphPayload, GraphLink, GraphNode, InternalGraphState } from '../types/domain';

const emptyGraph: InternalGraphState = { nodes: [], links: [] };

function toInternalGraph(payload: APIGraphPayload): InternalGraphState {
  return {
    nodes: payload.nodes,
    links: payload.edges.map((edge) => ({
      source: edge.source_id,
      target: edge.target_id,
      connection_type: edge.connection_type,
      weight: edge.weight,
      since_timestamp: edge.since_timestamp,
      sources: edge.sources,
    })),
  };
}

export function useGraphState() {
  const [graphData, setGraphData] = useState<InternalGraphState>(emptyGraph);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const loadGraph = useCallback((payload: APIGraphPayload) => {
    setGraphData(toInternalGraph(payload));
    setMessage(null);
  }, []);

  const clearGraph = useCallback(() => {
    setGraphData(emptyGraph);
    setMessage(null);
  }, []);

  const expandNode = useCallback(async (sessionId: string, targetId: string) => {
    setIsLoading(true);
    setMessage(null);
    try {
      const subgraph = await api.expandNode(sessionId, targetId);
      setGraphData((previous) => {
        const nodeMap = new Map<string, GraphNode>(previous.nodes.map((node) => [node.id, node]));
        subgraph.nodes.forEach((newNode) => {
          const existing = nodeMap.get(newNode.id);
          nodeMap.set(newNode.id, existing
            ? { ...existing, ...newNode, degree: Math.max(existing.degree, newNode.degree) }
            : newNode);
        });

        const expanded = nodeMap.get(targetId);
        if (expanded) expanded.is_expanded = true;

        const signature = (link: GraphLink) => {
          const source = typeof link.source === 'object' ? link.source.id : link.source;
          const target = typeof link.target === 'object' ? link.target.id : link.target;
          return `${source}:${target}:${link.connection_type}`;
        };
        const knownLinks = new Set(previous.links.map(signature));
        const links = [...previous.links];
        subgraph.edges.forEach((edge) => {
          const link: GraphLink = {
            source: edge.source_id,
            target: edge.target_id,
            connection_type: edge.connection_type,
            weight: edge.weight,
            since_timestamp: edge.since_timestamp,
            sources: edge.sources,
          };
          if (!knownLinks.has(signature(link))) links.push(link);
        });
        return { nodes: [...nodeMap.values()], links };
      });

      const count = Number(subgraph.metadata.known_connections ?? 0);
      setMessage(count > 0
        ? `Se encontraron ${count} conexiones conocidas para @${targetId}.`
        : `El archivo importado no contiene más conexiones conocidas para @${targetId}.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'No se pudo ampliar este perfil.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { graphData, isLoading, message, loadGraph, clearGraph, expandNode, setMessage };
}
