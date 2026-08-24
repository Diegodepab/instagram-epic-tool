import { useMemo } from 'react';
import type { GraphNode, InternalGraphState } from '../types/domain';

export interface GraphFilters {
  showMutuals: boolean;
  showFans: boolean;
  showNonFollowers: boolean;
  searchQuery: string;
  nodeLimit: 100 | 250 | 600;
}

const endpointId = (endpoint: string | GraphNode): string =>
  typeof endpoint === 'string' ? endpoint : endpoint.id;

export function useGraphFilters(
  originalGraphData: InternalGraphState,
  filters: GraphFilters,
): InternalGraphState {
  return useMemo(() => {
    const query = filters.searchQuery.trim().toLocaleLowerCase();
    const matchingNodes = originalGraphData.nodes.filter((node) => {
      if (node.group === 0) return true;
      if (node.group === 1 && !filters.showMutuals) return false;
      if (node.group === 2 && !filters.showFans) return false;
      if (node.group === 3 && !filters.showNonFollowers) return false;
      return !query || node.username.toLocaleLowerCase().includes(query);
    });

    const root = matchingNodes.find((node) => node.group === 0);
    const groups = [1, 2, 3].map((group) =>
      matchingNodes.filter((node) => node.group === group));
    const limitedNodes: GraphNode[] = [];
    let groupIndex = 0;
    while (limitedNodes.length < filters.nodeLimit - (root ? 1 : 0) && groups.some((group) => group.length)) {
      const group = groups[groupIndex % groups.length];
      const node = group.shift();
      if (node) limitedNodes.push(node);
      groupIndex += 1;
    }
    const nodes = root ? [root, ...limitedNodes] : limitedNodes;

    const validNodeIds = new Set(nodes.map((node) => node.id));
    const links = originalGraphData.links.filter((link) =>
      validNodeIds.has(endpointId(link.source))
      && validNodeIds.has(endpointId(link.target)));

    return { nodes, links };
  }, [filters, originalGraphData]);
}
