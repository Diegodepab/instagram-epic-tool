"""Pure set mathematics and graph projection for imported relationships."""

from __future__ import annotations

from dataclasses import dataclass

from backend.domain.models import GraphData, GraphLink, NodeGroup, UserNode


RelationshipMap = dict[str, set[str]]


@dataclass(frozen=True, slots=True)
class RelationshipSets:
    followers: frozenset[str]
    following: frozenset[str]
    mutuals: frozenset[str]
    fans: frozenset[str]
    non_followers: frozenset[str]


def calculate_relationships(
    followers: set[str] | frozenset[str],
    following: set[str] | frozenset[str],
) -> RelationshipSets:
    """Calculate exact relationship categories with hash-set operations."""
    follower_set = frozenset(followers)
    following_set = frozenset(following)
    return RelationshipSets(
        followers=follower_set,
        following=following_set,
        mutuals=follower_set & following_set,
        fans=follower_set - following_set,
        non_followers=following_set - follower_set,
    )


def build_central_graph(
    root_username: str,
    relationships: RelationshipSets,
) -> GraphData:
    """Project relationship sets to a react-force-graph compatible star graph."""
    nodes = [
        UserNode(
            id=root_username,
            username=f"@{root_username}",
            group=NodeGroup.CENTRAL,
        )
    ]
    links: list[GraphLink] = []

    for username in sorted(relationships.mutuals):
        nodes.append(UserNode(id=username, username=f"@{username}", group=NodeGroup.MUTUAL))
        links.append(GraphLink(source=root_username, target=username))

    for username in sorted(relationships.fans):
        nodes.append(UserNode(id=username, username=f"@{username}", group=NodeGroup.FAN))
        links.append(GraphLink(source=username, target=root_username))

    for username in sorted(relationships.non_followers):
        nodes.append(
            UserNode(id=username, username=f"@{username}", group=NodeGroup.NON_FOLLOWER)
        )
        links.append(GraphLink(source=root_username, target=username))

    return GraphData(nodes=nodes, links=links)


def build_relationship_maps(
    root_username: str,
    relationships: RelationshipSets,
) -> tuple[RelationshipMap, RelationshipMap]:
    """Create internally consistent adjacency maps for lazy graph navigation."""
    following_map: RelationshipMap = {
        root_username: set(relationships.following),
    }
    follower_map: RelationshipMap = {
        root_username: set(relationships.followers),
    }
    for username in relationships.following:
        following_map.setdefault(username, set())
        follower_map.setdefault(username, set()).add(root_username)
    for username in relationships.followers:
        follower_map.setdefault(username, set())
        following_map.setdefault(username, set()).add(root_username)
    return following_map, follower_map
