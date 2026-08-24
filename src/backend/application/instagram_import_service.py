"""Application service coordinating infrastructure and domain operations."""

from __future__ import annotations

from dataclasses import dataclass

from backend.domain.models import GraphData
from backend.domain.relationship_service import (
    RelationshipMap,
    RelationshipSets,
    build_central_graph,
    build_relationship_maps,
    calculate_relationships,
)
from backend.infrastructure.instagram_export_reader import (
    ExportDiagnostics,
    ExportSource,
    extract_instagram_relationships,
)


@dataclass(frozen=True, slots=True)
class InstagramImportResult:
    root_username: str
    relationships: RelationshipSets
    following_map: RelationshipMap
    follower_map: RelationshipMap
    relationship_timestamps: dict[tuple[str, str], int]
    graph: GraphData
    diagnostics: ExportDiagnostics


def analyze_instagram_export(
    source: ExportSource,
    root_username: str,
) -> InstagramImportResult:
    extracted = extract_instagram_relationships(source, root_username)
    relationships = calculate_relationships(extracted.followers, extracted.following)
    following_map, follower_map = build_relationship_maps(
        extracted.root_username,
        relationships,
    )
    relationship_timestamps = {
        **{(extracted.root_username, username): timestamp for username, timestamp in extracted.following_since.items()},
        **{(username, extracted.root_username): timestamp for username, timestamp in extracted.follower_since.items()},
    }
    return InstagramImportResult(
        root_username=extracted.root_username,
        relationships=relationships,
        following_map=following_map,
        follower_map=follower_map,
        relationship_timestamps=relationship_timestamps,
        graph=build_central_graph(extracted.root_username, relationships),
        diagnostics=extracted.diagnostics,
    )
