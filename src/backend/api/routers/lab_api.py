from fastapi import APIRouter, HTTPException, Request, status

from backend.domain.schemas import InstagrapiOwnAccountRequest, LiveCommitRequest, LiveScanRequest
from backend.services.lab_integrations import (
    LabAuthenticationError,
    LabDisabledError,
    LabRateLimitError,
    inspect_offensive_repository,
    inspect_own_instagram_account,
    integration_status,
)
from backend.services.live_scan_service import (
    LiveScanAuthError,
    LiveScanConflictError,
    LiveScanDisabledError,
    LiveScanNotFoundError,
    LiveScanRateLimitError,
    commit_scan,
    scan_target_account,
)


router = APIRouter(prefix="/lab", tags=["Isolated experimental integrations"])


@router.get("/status")
def get_lab_status():
    return integration_status()


@router.get("/instagram-bruter/static-assessment")
def get_defensive_assessment():
    try:
        return inspect_offensive_repository()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/instagrapi/own-account")
def inspect_own_account(payload: InstagrapiOwnAccountRequest, request: Request):
    requester = request.client.host if request.client else "unknown"
    try:
        return inspect_own_instagram_account(
            username=payload.username,
            password=payload.password.get_secret_value(),
            relationship_limit=payload.relationship_limit,
            media_limit=payload.media_limit,
            requester_key=requester,
        )
    except LabDisabledError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except LabRateLimitError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc
    except LabAuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.post("/live-scan")
def live_scan(payload: LiveScanRequest, request: Request):
    """Scan a target account using a temporary login and return a preview."""
    requester = request.client.host if request.client else "unknown"
    try:
        return scan_target_account(
            temp_username=payload.temp_username,
            temp_password=payload.temp_password.get_secret_value(),
            target_username=payload.target_username,
            requester_key=requester,
        )
    except LiveScanDisabledError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except LiveScanRateLimitError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc
    except LiveScanAuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.post("/live-scan/commit")
def live_scan_commit(payload: LiveCommitRequest):
    """Convert a pending scan preview into a full analysis session."""
    try:
        return commit_scan(
            scan_id=payload.scan_id,
            session_id=payload.session_id,
        )
    except LiveScanDisabledError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except LiveScanNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except LiveScanConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
