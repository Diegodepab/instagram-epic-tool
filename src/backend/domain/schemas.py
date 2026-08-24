from pydantic import BaseModel, Field, SecretStr, field_validator
from typing import List, Dict, Any
from enum import Enum

class ConnectionType(str, Enum):
    FOLLOWS = "follows"
    FOLLOWED_BY = "followed_by"
    MUTUAL = "mutual"
    BLOCKS = "blocks"


class RelationshipCategory(str, Enum):
    ALL = "all"
    FOLLOWERS = "followers"
    FOLLOWING = "following"
    MUTUALS = "mutuals"
    FOLLOWERS_ONLY = "followers_only"
    FOLLOWING_ONLY = "following_only"

class UserNode(BaseModel):
    id: str = Field(..., description="ID interno (alfanumérico único) o el ID real de Instagram.")
    username: str = Field(..., description="El handle del usuario (ej: @john_doe)")
    group: int = Field(default=0, ge=0, le=3, description="0 central, 1 mutuo, 2 fan, 3 no seguidor")
    is_expanded: bool = Field(
        default=False, 
        description="True si el frontend ya solicitó y cargó las relaciones L2 de este nodo."
    )
    degree: int = Field(
        default=0, 
        description="El grado computado (conexiones totales). Permite al frontend escalar visualmente el tamaño del nodo (Hubs son más grandes)."
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ConnectionEdge(BaseModel):
    source_id: str
    target_id: str
    connection_type: ConnectionType
    weight: float = Field(default=1.0)
    since_timestamp: int | None = None
    sources: List[str] = Field(default_factory=list)

class GraphPayload(BaseModel):
    """
    Contenedor estándar que soporta actualizaciones incrementales (parches de grafos).
    """
    nodes: List[UserNode]
    edges: List[ConnectionEdge]
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Información de la respuesta (ej: { 'is_partial': True, 'pruned_nodes': 4500 })"
    )


class ProfileSummary(BaseModel):
    username: str
    followers: int
    following: int
    mutuals: int
    followers_only: int
    following_only: int


class ImportResponse(BaseModel):
    session_id: str
    summary: ProfileSummary
    graph: GraphPayload
    expires_in_seconds: int
    warnings: List[str] = Field(default_factory=list)
    imported_profiles: List[str] = Field(default_factory=list)


class RelationshipItem(BaseModel):
    username: str
    relationship: str
    known_connections: int


class RelationshipPage(BaseModel):
    items: List[RelationshipItem]
    total: int
    offset: int
    limit: int


class InstagrapiOwnAccountRequest(BaseModel):
    username: str = Field(min_length=1, max_length=30, pattern=r"^[A-Za-z0-9._]+$")
    password: SecretStr = Field(min_length=6, max_length=256)
    relationship_limit: int = Field(default=25, ge=1, le=50)
    media_limit: int = Field(default=6, ge=0, le=12)
    consent: bool

    @field_validator("consent")
    @classmethod
    def require_consent(cls, value: bool) -> bool:
        if not value:
            raise ValueError("Debes confirmar que la cuenta es tuya o que tienes autorización expresa.")
        return value


# ---------------------------------------------------------------------------
# Live Scan schemas
# ---------------------------------------------------------------------------


class LiveProfileItem(BaseModel):
    """Minimal publicly-visible profile data for a single user."""
    username: str
    full_name: str = ""
    is_private: bool = False
    profile_pic_b64: str | None = None


class LiveProfilePreview(BaseModel):
    """Preview card for a scanned target account."""
    username: str
    full_name: str = ""
    is_private: bool = False
    profile_pic_b64: str | None = None
    follower_count: int = 0
    following_count: int = 0
    followers: List[LiveProfileItem] = Field(default_factory=list)
    following: List[LiveProfileItem] = Field(default_factory=list)
    followers_complete: bool = False
    following_complete: bool = False


class LiveScanRequest(BaseModel):
    """Frontend request to scan a target account via a temporary login."""
    temp_username: str = Field(min_length=1, max_length=30, pattern=r"^[A-Za-z0-9._]+$")
    temp_password: SecretStr = Field(min_length=6, max_length=256)
    target_username: str = Field(min_length=1, max_length=30, pattern=r"^[A-Za-z0-9._]+$")
    consent: bool

    @field_validator("consent")
    @classmethod
    def require_scan_consent(cls, value: bool) -> bool:
        if not value:
            raise ValueError(
                "Debes confirmar que tienes autorización expresa del propietario "
                "de la cuenta objetivo."
            )
        return value


class LiveScanResult(BaseModel):
    """Response returned after a live scan (preview, not yet committed)."""
    scan_id: str
    preview: LiveProfilePreview
    warnings: List[str] = Field(default_factory=list)


class LiveCommitRequest(BaseModel):
    """Request to persist a previewed scan into an analysis session."""
    scan_id: str = Field(min_length=20, max_length=128)
    session_id: str | None = Field(
        default=None,
        description="If provided, merge into this existing session. Otherwise create a new one.",
    )
