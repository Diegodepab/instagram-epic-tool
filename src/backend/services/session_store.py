"""Short-lived, in-memory storage for validated analysis sessions."""

from __future__ import annotations

import secrets
import threading
import time
from dataclasses import dataclass, field

from backend.domain.relationship_service import RelationshipMap


SESSION_TTL_SECONDS = 60 * 60
MAX_ACTIVE_SESSIONS = 25


class SessionNotFoundError(KeyError):
    """Raised when a session does not exist or has expired."""


class DuplicateImportError(ValueError):
    """Raised when the same profile export is added twice."""


@dataclass(frozen=True, slots=True)
class AnalysisSession:
    session_id: str
    root_user_id: str
    following_map: RelationshipMap
    follower_map: RelationshipMap
    imported_profiles: frozenset[str]
    relationship_timestamps: dict[tuple[str, str], int]
    relationship_sources: dict[tuple[str, str], frozenset[str]]
    created_at: float = field(default_factory=time.monotonic)


class AnalysisSessionStore:
    def __init__(
        self,
        ttl_seconds: int = SESSION_TTL_SECONDS,
        max_sessions: int = MAX_ACTIVE_SESSIONS,
    ) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_sessions = max_sessions
        self._sessions: dict[str, AnalysisSession] = {}
        self._lock = threading.Lock()

    def create(
        self,
        root_user_id: str,
        following_map: RelationshipMap,
        follower_map: RelationshipMap,
        relationship_timestamps: dict[tuple[str, str], int] | None = None,
    ) -> AnalysisSession:
        with self._lock:
            self._purge_expired()
            if len(self._sessions) >= self.max_sessions:
                oldest_id = min(
                    self._sessions,
                    key=lambda session_id: self._sessions[session_id].created_at,
                )
                del self._sessions[oldest_id]

            session = AnalysisSession(
                session_id=secrets.token_urlsafe(24),
                root_user_id=root_user_id,
                following_map=following_map,
                follower_map=follower_map,
                imported_profiles=frozenset({root_user_id}),
                relationship_timestamps=dict(relationship_timestamps or {}),
                relationship_sources={
                    edge: frozenset({root_user_id})
                    for edge in _direct_edges(root_user_id, following_map, follower_map)
                },
            )
            self._sessions[session.session_id] = session
            return session

    def merge(
        self,
        session_id: str,
        imported_profile: str,
        following_map: RelationshipMap,
        follower_map: RelationshipMap,
        relationship_timestamps: dict[tuple[str, str], int] | None = None,
    ) -> AnalysisSession:
        """Atomically merge one authorized export into an existing session."""
        with self._lock:
            self._purge_expired()
            try:
                current = self._sessions[session_id]
            except KeyError as exc:
                raise SessionNotFoundError(session_id) from exc
            if imported_profile in current.imported_profiles:
                raise DuplicateImportError(imported_profile)

            merged_following = _merge_maps(current.following_map, following_map)
            merged_followers = _merge_maps(current.follower_map, follower_map)
            merged_timestamps = dict(current.relationship_timestamps)
            merged_sources = dict(current.relationship_sources)
            for edge in _direct_edges(imported_profile, following_map, follower_map):
                merged_sources[edge] = merged_sources.get(edge, frozenset()) | {imported_profile}
            for edge, timestamp in (relationship_timestamps or {}).items():
                merged_timestamps[edge] = min(timestamp, merged_timestamps.get(edge, timestamp))

            merged = AnalysisSession(
                session_id=current.session_id,
                root_user_id=current.root_user_id,
                following_map=merged_following,
                follower_map=merged_followers,
                imported_profiles=current.imported_profiles | {imported_profile},
                relationship_timestamps=merged_timestamps,
                relationship_sources=merged_sources,
                created_at=current.created_at,
            )
            self._sessions[session_id] = merged
            return merged

    def get(self, session_id: str) -> AnalysisSession:
        with self._lock:
            self._purge_expired()
            try:
                return self._sessions[session_id]
            except KeyError as exc:
                raise SessionNotFoundError(session_id) from exc

    def delete(self, session_id: str) -> bool:
        with self._lock:
            return self._sessions.pop(session_id, None) is not None

    def _purge_expired(self) -> None:
        deadline = time.monotonic() - self.ttl_seconds
        expired = [
            session_id
            for session_id, session in self._sessions.items()
            if session.created_at < deadline
        ]
        for session_id in expired:
            del self._sessions[session_id]


session_store = AnalysisSessionStore()


def _merge_maps(left: RelationshipMap, right: RelationshipMap) -> RelationshipMap:
    merged = {username: set(neighbours) for username, neighbours in left.items()}
    for username, neighbours in right.items():
        merged.setdefault(username, set()).update(neighbours)
    return merged


def _direct_edges(
    owner: str,
    following_map: RelationshipMap,
    follower_map: RelationshipMap,
) -> set[tuple[str, str]]:
    edges = {(owner, username) for username in following_map.get(owner, set())}
    edges.update((username, owner) for username in follower_map.get(owner, set()))
    return edges
