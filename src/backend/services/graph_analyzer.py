from typing import Set, Dict
from backend.domain.schemas import GraphPayload, UserNode, ConnectionEdge, ConnectionType


MAX_GRAPH_PROFILES = 599
MAX_EXPANSION_PROFILES = 299

class GraphAnalyzer:
    def __init__(self, current_user_id: str, following_map: Dict[str, Set[str]], follower_map: Dict[str, Set[str]], imported_profiles: frozenset[str] | None = None, relationship_timestamps: dict[tuple[str, str], int] | None = None, relationship_sources: dict[tuple[str, str], frozenset[str]] | None = None):
        self.current_user_id = current_user_id
        self.following_map = following_map
        self.follower_map = follower_map
        self.imported_profiles = imported_profiles or frozenset({current_user_id})
        self.relationship_timestamps = relationship_timestamps or {}
        self.relationship_sources = relationship_sources or {}
        
        self.l1_followings = self.following_map.get(current_user_id, set())
        self.l1_followers = self.follower_map.get(current_user_id, set())
        # El Nivel 1 completo
        self.l1_all = self.l1_followings.union(self.l1_followers)

    def get_traitors(self) -> Set[str]:
        return self.l1_followings.difference(self.l1_followers)

    def get_fans(self) -> Set[str]:
        return self.l1_followers.difference(self.l1_followings)

    def get_mutuals(self) -> Set[str]:
        return self.l1_followings.intersection(self.l1_followers)

    def _relationship_to_root(self, node_id: str) -> str:
        if node_id == self.current_user_id:
            return "root"
        follows = node_id in self.l1_followings
        followed_by = node_id in self.l1_followers
        if follows and followed_by:
            return "mutual"
        if followed_by:
            return "follower_only"
        return "following_only"

    def _create_user_node(
        self,
        node_id: str,
        is_expanded: bool = False,
        degree: int = 0,
        relation: str | None = None,
    ) -> UserNode:
        if degree == 0:
            degree = len(self.following_map.get(node_id, set()).union(
                self.follower_map.get(node_id, set())
            ))
        return UserNode(
            id=node_id,
            username=f"@{node_id}",
            group={"root": 0, "mutual": 1, "follower_only": 2, "following_only": 3}.get(relation, 0),
            is_expanded=is_expanded,
            degree=degree,
            metadata={
                **({"relation": relation} if relation else {}),
                "has_imported_data": node_id in self.imported_profiles,
            },
        )

    def _edge(self, source_id: str, target_id: str, connection_type: ConnectionType) -> ConnectionEdge:
        key = (source_id, target_id)
        return ConnectionEdge(
            source_id=source_id,
            target_id=target_id,
            connection_type=connection_type,
            since_timestamp=self.relationship_timestamps.get(key),
            sources=sorted(self.relationship_sources.get(key, frozenset())),
        )

    def _visible_profiles(self, limit: int = MAX_GRAPH_PROFILES) -> list[str]:
        groups = [
            sorted(self.get_mutuals()),
            sorted(self.get_fans()),
            sorted(self.get_traitors()),
        ]
        selected: list[str] = []
        selected_set: set[str] = set()
        quota = max(1, limit // len(groups))
        for group in groups:
            for node_id in group[:quota]:
                selected.append(node_id)
                selected_set.add(node_id)
        if len(selected) < limit:
            for node_id in sorted(self.l1_all - selected_set):
                selected.append(node_id)
                if len(selected) == limit:
                    break
        return selected[:limit]

    def get_base_graph(self) -> GraphPayload:
        nodes = []
        edges = []
        visible_profiles = self._visible_profiles()
        visible_set = set(visible_profiles)
        
        # Nodo raíz
        nodes.append(self._create_user_node(
            self.current_user_id,
            is_expanded=True,
            relation="root",
        ))
        
        # Construir nodos L1 y calcular aristas directas
        for node_id in visible_profiles:
            if node_id in self.l1_followings and node_id in self.l1_followers:
                relation = "mutual"
            elif node_id in self.l1_followers:
                relation = "follower_only"
            else:
                relation = "following_only"
            nodes.append(self._create_user_node(
                node_id,
                is_expanded=False,
                relation=relation,
            ))
            
            # Conexiones con el Root
            if node_id in self.l1_followings and node_id in self.l1_followers:
                edges.append(self._edge(self.current_user_id, node_id, ConnectionType.MUTUAL))
            elif node_id in self.l1_followings:
                edges.append(self._edge(self.current_user_id, node_id, ConnectionType.FOLLOWS))
            elif node_id in self.l1_followers:
                edges.append(self._edge(node_id, self.current_user_id, ConnectionType.FOLLOWS))
                
        # Interconexiones exclusivas dentro del L1
        for node_id in visible_profiles:
            node_followings = self.following_map.get(node_id, set())
            for target_id in node_followings.intersection(visible_set):
                edges.append(self._edge(node_id, target_id, ConnectionType.FOLLOWS))
                
        return GraphPayload(
            nodes=nodes,
            edges=edges,
            metadata={
                "description": "Base Graph (L1 Only)", 
                "total_nodes": len(self.l1_all) + 1,
                "visible_nodes": len(nodes),
                "truncated": len(self.l1_all) > len(visible_profiles),
                "visual_limit": MAX_GRAPH_PROFILES + 1,
                "traitors": len(self.get_traitors()),
                "fans": len(self.get_fans())
            }
        )

    def expand_known_node(self, target_user_id: str) -> GraphPayload:
        """Return only relationships already present in the imported dataset."""
        target_following = self.following_map.get(target_user_id, set())
        target_followers = self.follower_map.get(target_user_id, set())
        all_neighbours = target_following.union(target_followers)
        neighbours = set(sorted(all_neighbours)[:MAX_EXPANSION_PROFILES])

        nodes = [self._create_user_node(
            target_user_id,
            is_expanded=True,
            relation=self._relationship_to_root(target_user_id),
        )]
        for node_id in sorted(neighbours):
            follows = node_id in target_following
            followed_by = node_id in target_followers
            relation = "mutual" if follows and followed_by else (
                "following_only" if follows else "follower_only"
            )
            nodes.append(self._create_user_node(node_id, relation=relation))

        edges = []
        for node_id in sorted(neighbours):
            follows = node_id in target_following
            followed_by = node_id in target_followers
            if follows and followed_by:
                edges.append(self._edge(target_user_id, node_id, ConnectionType.MUTUAL))
            elif follows:
                edges.append(self._edge(target_user_id, node_id, ConnectionType.FOLLOWS))
            else:
                edges.append(self._edge(node_id, target_user_id, ConnectionType.FOLLOWS))

        return GraphPayload(
            nodes=nodes,
            edges=edges,
            metadata={
                "expanded_node": target_user_id,
                "known_connections": len(all_neighbours),
                "visible_connections": len(neighbours),
                "truncated": len(all_neighbours) > len(neighbours),
                "has_more_connections": bool(all_neighbours),
                "data_scope": "imported_exports_only",
            },
        )
