"""Backward-compatible facade for the DDD import service.

New code should depend on ``application.instagram_import_service`` or the
infrastructure reader directly, according to its layer.
"""

from backend.application.instagram_import_service import analyze_instagram_export
from backend.infrastructure.instagram_export_reader import (
    ExportDiagnostics,
    ExportFormatError,
    ExportSource,
    InstagramExportError,
    UnsafeArchiveError,
)


RelationshipMap = dict[str, set[str]]


def parse_instagram_export(
    source: ExportSource,
    root_user_id: str,
) -> tuple[RelationshipMap, RelationshipMap]:
    result = analyze_instagram_export(source, root_user_id)
    return result.following_map, result.follower_map


def parse_instagram_export_with_diagnostics(
    source: ExportSource,
    root_user_id: str,
) -> tuple[RelationshipMap, RelationshipMap, ExportDiagnostics]:
    result = analyze_instagram_export(source, root_user_id)
    return result.following_map, result.follower_map, result.diagnostics
