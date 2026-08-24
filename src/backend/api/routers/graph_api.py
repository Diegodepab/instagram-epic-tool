import csv
import io

from fastapi import APIRouter, File, Form, HTTPException, Query, Response, UploadFile, status

from backend.application.instagram_import_service import analyze_instagram_export
from backend.domain.models import GraphData
from backend.domain.schemas import (
    GraphPayload,
    ImportResponse,
    ProfileSummary,
    RelationshipCategory,
    RelationshipItem,
    RelationshipPage,
)
from backend.services.demo_data import generate_demo_data
from backend.services.graph_analyzer import GraphAnalyzer
from backend.services.session_store import (
    SESSION_TTL_SECONDS,
    SessionNotFoundError,
    DuplicateImportError,
    session_store,
)
from backend.infrastructure.instagram_export_reader import (
    ExportFormatError,
    InstagramExportError,
    UnsafeArchiveError,
)


router = APIRouter(prefix="/analysis", tags=["Instagram export analysis"])


def _get_analyzer(session_id: str) -> GraphAnalyzer:
    try:
        session = session_store.get(session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La sesión no existe o ha caducado. Importa el archivo de nuevo.",
        ) from exc
    return GraphAnalyzer(
        current_user_id=session.root_user_id,
        following_map=session.following_map,
        follower_map=session.follower_map,
        imported_profiles=session.imported_profiles,
        relationship_timestamps=session.relationship_timestamps,
        relationship_sources=session.relationship_sources,
    )


def _summary(analyzer: GraphAnalyzer) -> ProfileSummary:
    return ProfileSummary(
        username=analyzer.current_user_id,
        followers=len(analyzer.l1_followers),
        following=len(analyzer.l1_followings),
        mutuals=len(analyzer.get_mutuals()),
        followers_only=len(analyzer.get_fans()),
        following_only=len(analyzer.get_traitors()),
    )


def _import_response(session_id: str, warnings: list[str] | None = None) -> ImportResponse:
    analyzer = _get_analyzer(session_id)
    return ImportResponse(
        session_id=session_id,
        summary=_summary(analyzer),
        graph=analyzer.get_base_graph(),
        expires_in_seconds=SESSION_TTL_SECONDS,
        warnings=warnings or [],
        imported_profiles=sorted(session_store.get(session_id).imported_profiles),
    )


def _profiles_for_category(
    analyzer: GraphAnalyzer,
    category: RelationshipCategory,
) -> set[str]:
    categories = {
        RelationshipCategory.ALL: analyzer.l1_all,
        RelationshipCategory.FOLLOWERS: analyzer.l1_followers,
        RelationshipCategory.FOLLOWING: analyzer.l1_followings,
        RelationshipCategory.MUTUALS: analyzer.get_mutuals(),
        RelationshipCategory.FOLLOWERS_ONLY: analyzer.get_fans(),
        RelationshipCategory.FOLLOWING_ONLY: analyzer.get_traitors(),
    }
    return categories[category]


def _relationship_name(analyzer: GraphAnalyzer, username: str) -> str:
    follows = username in analyzer.l1_followings
    followed_by = username in analyzer.l1_followers
    if follows and followed_by:
        return RelationshipCategory.MUTUALS.value
    if followed_by:
        return RelationshipCategory.FOLLOWERS_ONLY.value
    return RelationshipCategory.FOLLOWING_ONLY.value


@router.post("/imports", response_model=ImportResponse, status_code=status.HTTP_201_CREATED)
async def import_export(
    export: UploadFile = File(..., description="ZIP oficial de exportación de Instagram"),
    username: str = Form(..., min_length=1, max_length=31),
) -> ImportResponse:
    if not export.filename or not export.filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Selecciona el archivo ZIP oficial de Instagram en formato JSON.",
        )

    try:
        import_result = analyze_instagram_export(
            export.file,
            username,
        )
    except UnsafeArchiveError as exc:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc)) from exc
    except (ExportFormatError, InstagramExportError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    finally:
        await export.close()

    session = session_store.create(
        import_result.root_username,
        import_result.following_map,
        import_result.follower_map,
        import_result.relationship_timestamps,
    )
    warnings = []
    if import_result.diagnostics.likely_partial_followers:
        warnings.append(
            "La lista de seguidores parece corresponder a un intervalo de fechas parcial. "
            "Para métricas actuales exactas, solicita a Instagram una exportación desde siempre."
        )
    return _import_response(session.session_id, warnings)


@router.post(
    "/sessions/{session_id}/imports",
    response_model=ImportResponse,
    status_code=status.HTTP_200_OK,
)
async def merge_export(
    session_id: str,
    export: UploadFile = File(..., description="ZIP adicional autorizado"),
    username: str = Form(..., min_length=1, max_length=31),
    consent: bool = Form(..., description="Autorización expresa del propietario del ZIP"),
) -> ImportResponse:
    """Merge a second authorized account export into the temporary graph."""
    if not consent:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Debes confirmar la autorización expresa del propietario de la exportación.",
        )
    if not export.filename or not export.filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Selecciona el archivo ZIP oficial de Instagram en formato JSON.",
        )
    try:
        result = analyze_instagram_export(export.file, username)
        session_store.merge(
            session_id,
            result.root_username,
            result.following_map,
            result.follower_map,
            result.relationship_timestamps,
        )
    except DuplicateImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"La exportación de @{exc.args[0]} ya forma parte de esta sesión.",
        ) from exc
    except SessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La sesión no existe o ha caducado. Importa el archivo principal de nuevo.",
        ) from exc
    except UnsafeArchiveError as exc:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc)) from exc
    except (ExportFormatError, InstagramExportError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    finally:
        await export.close()

    warnings = []
    if result.diagnostics.likely_partial_followers:
        warnings.append(f"La exportación de @{result.root_username} podría usar un intervalo parcial.")
    return _import_response(session_id, warnings)


@router.post("/imports/graph", response_model=GraphData)
async def import_graph(
    export: UploadFile = File(..., description="ZIP oficial de exportación de Instagram"),
    username: str = Form(..., min_length=1, max_length=31),
) -> GraphData:
    """Return a strict react-force-graph ``nodes``/``links`` projection."""
    if not export.filename or not export.filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Selecciona el archivo ZIP oficial de Instagram en formato JSON.",
        )
    try:
        return analyze_instagram_export(export.file, username).graph
    except UnsafeArchiveError as exc:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc)) from exc
    except (ExportFormatError, InstagramExportError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    finally:
        await export.close()


@router.post("/demo", response_model=ImportResponse, status_code=status.HTTP_201_CREATED)
async def create_demo() -> ImportResponse:
    root_user_id, following_map, follower_map = generate_demo_data()
    session = session_store.create(root_user_id, following_map, follower_map)
    return _import_response(session.session_id)


@router.get("/sessions/{session_id}/graph", response_model=GraphPayload)
async def get_graph(session_id: str) -> GraphPayload:
    return _get_analyzer(session_id).get_base_graph()


@router.get("/sessions/{session_id}/nodes/{node_id}", response_model=GraphPayload)
async def expand_node(session_id: str, node_id: str) -> GraphPayload:
    return _get_analyzer(session_id).expand_known_node(node_id.lower())


@router.get("/sessions/{session_id}/relationships", response_model=RelationshipPage)
async def list_relationships(
    session_id: str,
    category: RelationshipCategory = RelationshipCategory.ALL,
    search: str = Query("", max_length=30),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> RelationshipPage:
    analyzer = _get_analyzer(session_id)
    normalized_search = search.strip().removeprefix("@").lower()
    profiles = sorted(_profiles_for_category(analyzer, category))
    if normalized_search:
        profiles = [profile for profile in profiles if normalized_search in profile]
    page = profiles[offset:offset + limit]
    items = [
        RelationshipItem(
            username=profile,
            relationship=_relationship_name(analyzer, profile),
            known_connections=len(
                analyzer.following_map.get(profile, set()).union(
                    analyzer.follower_map.get(profile, set())
                )
            ),
        )
        for profile in page
    ]
    return RelationshipPage(
        items=items,
        total=len(profiles),
        offset=offset,
        limit=limit,
    )


@router.get("/sessions/{session_id}/relationships.csv")
async def export_relationships_csv(
    session_id: str,
    category: RelationshipCategory = RelationshipCategory.ALL,
) -> Response:
    analyzer = _get_analyzer(session_id)
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["username", "relationship", "known_connections"])
    for profile in sorted(_profiles_for_category(analyzer, category)):
        writer.writerow([
            profile,
            _relationship_name(analyzer, profile),
            len(
                analyzer.following_map.get(profile, set()).union(
                    analyzer.follower_map.get(profile, set())
                )
            ),
        ])
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="circlescope-{category.value}.csv"'
        },
    )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: str) -> Response:
    session_store.delete(session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
