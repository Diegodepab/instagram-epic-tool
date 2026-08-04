from fastapi import APIRouter, HTTPException, Request, status

from backend.domain.schemas import InstagrapiOwnAccountRequest
from backend.services.lab_integrations import (
    LabAuthenticationError,
    LabDisabledError,
    LabRateLimitError,
    inspect_offensive_repository,
    inspect_own_instagram_account,
    integration_status,
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
