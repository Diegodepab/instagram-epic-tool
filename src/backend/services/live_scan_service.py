"""Live scan service — fetch public follower/following data via instagrapi.

Security design:
- Credentials are never written to disk or logs.
- The instagrapi session is destroyed after every scan.
- Delays between API calls simulate human browsing cadence.
- Rate limiting prevents rapid-fire requests (120 s cooldown per IP).
- Pending scans auto-expire after 10 minutes.
- Only publicly visible profile data is collected (username, full_name,
  is_private, profile_pic_url). No descriptions, emails, or phone numbers.
"""

from __future__ import annotations

import base64
import logging
import os
import random
import secrets
import threading
import time
from dataclasses import dataclass, field
from typing import Any

from backend.domain.schemas import (
    ImportResponse,
    LiveProfileItem,
    LiveProfilePreview,
    LiveScanResult,
)
from backend.services.session_store import (
    SessionNotFoundError,
    session_store,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MAX_FOLLOWERS_FETCH = 200
MAX_FOLLOWING_FETCH = 200
MAX_PROFILE_PICS = 50
MAX_PROFILE_PIC_BYTES = 2 * 1024 * 1024
PROFILE_PIC_TIMEOUT = 4  # seconds per image
SCAN_TTL_SECONDS = 600  # 10 minutes until auto-purge
REQUEST_COOLDOWN_SECONDS = 120

# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

_last_request: dict[str, float] = {}
_rate_lock = threading.Lock()


class LiveScanDisabledError(RuntimeError):
    pass


class LiveScanRateLimitError(RuntimeError):
    pass


class LiveScanAuthError(RuntimeError):
    pass


class LiveScanNotFoundError(KeyError):
    pass


class LiveScanConflictError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# Pending scan store (in-memory, auto-expires)
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class PendingScan:
    scan_id: str
    target_username: str
    followers: list[str]
    following: list[str]
    warnings: tuple[str, ...] = ()
    created_at: float = field(default_factory=time.monotonic)


_pending_scans: dict[str, PendingScan] = {}
_scan_lock = threading.Lock()


def _purge_expired_scans() -> None:
    deadline = time.monotonic() - SCAN_TTL_SECONDS
    expired = [sid for sid, scan in _pending_scans.items() if scan.created_at < deadline]
    for sid in expired:
        del _pending_scans[sid]


def _safe_delay(min_s: float = 2.0, max_s: float = 5.0) -> None:
    delay = random.uniform(min_s, max_s)
    logger.info("Anti-ban delay: %.2f s", delay)
    time.sleep(delay)


# ---------------------------------------------------------------------------
# Profile picture proxy (download → base64, served inline)
# ---------------------------------------------------------------------------


def _fetch_profile_pic_b64(url: str | None) -> str | None:
    """Download a profile picture and return as a data-URI base64 string."""
    if not url:
        return None
    try:
        import httpx

        with httpx.Client(
            timeout=PROFILE_PIC_TIMEOUT,
            follow_redirects=True,
            limits=httpx.Limits(max_connections=2),
        ) as http:
            with http.stream("GET", url) as response:
                if response.status_code != 200:
                    return None
                content_type = response.headers.get("content-type", "").split(";", 1)[0].lower()
                content_length = int(response.headers.get("content-length", "0") or 0)
                if (
                    not content_type.startswith("image/")
                    or content_length > MAX_PROFILE_PIC_BYTES
                ):
                    return None
                content = bytearray()
                for chunk in response.iter_bytes():
                    content.extend(chunk)
                    if len(content) > MAX_PROFILE_PIC_BYTES:
                        return None
            encoded = base64.b64encode(content).decode("ascii")
            return f"data:{content_type};base64,{encoded}"
    except Exception:
        logger.debug("Could not fetch profile pic: %s", url, exc_info=True)
        return None


# ---------------------------------------------------------------------------
# Core scan logic
# ---------------------------------------------------------------------------


def _require_enabled() -> None:
    if os.getenv("ENABLE_INSTAGRAPI_LAB", "false").lower() != "true":
        raise LiveScanDisabledError(
            "La exploración en vivo está desactivada. "
            "Configura ENABLE_INSTAGRAPI_LAB=true en las variables de entorno del backend."
        )


def _enforce_rate_limit(requester_key: str) -> None:
    now = time.monotonic()
    cooldown = _configured_limit(
        "LIVE_SCAN_COOLDOWN_SECONDS", REQUEST_COOLDOWN_SECONDS, 600
    )
    with _rate_lock:
        previous = _last_request.get(requester_key, 0)
        if now - previous < cooldown:
            remaining = max(1, int(cooldown - (now - previous)))
            raise LiveScanRateLimitError(
                f"Espera {remaining} segundos antes de iniciar otra exploración."
            )
        _last_request[requester_key] = now


def _configured_limit(name: str, default: int, maximum: int) -> int:
    """Read a bounded lab tuning value without allowing unsafe/unbounded scans."""
    try:
        return max(1, min(int(os.getenv(name, str(default))), maximum))
    except ValueError:
        logger.warning("Ignoring invalid %s value", name)
        return default


def scan_target_account(
    temp_username: str,
    temp_password: str,
    target_username: str,
    requester_key: str,
) -> LiveScanResult:
    """Authenticate with a temp account, fetch target's public data, return a preview."""
    _require_enabled()
    _enforce_rate_limit(requester_key)

    try:
        from instagrapi import Client
        from instagrapi.exceptions import ClientError
    except ImportError as exc:
        raise LiveScanDisabledError(
            "La librería instagrapi no está instalada en el backend. "
            "Ejecuta: pip install instagrapi"
        ) from exc

    proxy_url = os.getenv("IG_PROXY")

    client = Client()
    client.request_timeout = 15
    client.delay_range = [2, 5]

    if proxy_url:
        logger.info("Configurando proxy para la sesión live scan.")
        client.set_proxy(proxy_url)

    warnings: list[str] = []
    followers_limit = _configured_limit("LIVE_SCAN_FOLLOWERS_LIMIT", MAX_FOLLOWERS_FETCH, 500)
    following_limit = _configured_limit("LIVE_SCAN_FOLLOWING_LIMIT", MAX_FOLLOWING_FETCH, 500)
    profile_pic_limit = _configured_limit("LIVE_SCAN_PROFILE_PICS_LIMIT", MAX_PROFILE_PICS, 100)

    try:
        # --- Login ---
        logger.info("Iniciando sesión con cuenta temporal: %s", temp_username)
        if not client.login(temp_username, temp_password):
            raise LiveScanAuthError("Instagram rechazó el inicio de sesión.")

        authenticated = str(client.account_info().username).lower()
        if authenticated != temp_username.lower().lstrip("@"):
            raise LiveScanAuthError(
                "La identidad autenticada no coincide con la cuenta temporal declarada."
            )
        logger.info("Sesión iniciada correctamente.")

        _safe_delay(2, 4)

        # --- Target profile info ---
        logger.info("Obteniendo perfil de @%s", target_username)
        try:
            target_user_id = client.user_id_from_username(target_username.lower())
        except Exception as exc:
            raise LiveScanAuthError(
                f"No se pudo encontrar el usuario @{target_username}."
            ) from exc

        target_info = client.user_info(target_user_id)
        target_pic_b64 = _fetch_profile_pic_b64(str(target_info.profile_pic_url_hd or target_info.profile_pic_url))

        _safe_delay(3, 6)

        # --- Followers ---
        logger.info("Descargando seguidores de @%s (límite: %d)", target_username, followers_limit)
        try:
            followers_dict = client.user_followers(target_user_id, amount=followers_limit)
        except Exception as exc:
            logger.warning("Error parcial al obtener seguidores: %s", exc)
            followers_dict = {}
            warnings.append("No se pudieron obtener todos los seguidores. El perfil puede ser privado o Instagram limitó la consulta.")

        _safe_delay(5, 10)

        # --- Following ---
        logger.info("Descargando seguidos de @%s (límite: %d)", target_username, following_limit)
        try:
            following_dict = client.user_following(target_user_id, amount=following_limit)
        except Exception as exc:
            logger.warning("Error parcial al obtener seguidos: %s", exc)
            following_dict = {}
            warnings.append("No se pudieron obtener todos los seguidos.")

        # --- Build profile items with pics ---
        logger.info("Procesando perfiles y descargando fotos…")

        remaining_pics = profile_pic_limit

        def _build_items(user_dict: dict, limit: int) -> list[LiveProfileItem]:
            nonlocal remaining_pics
            items: list[LiveProfileItem] = []
            for user in list(user_dict.values())[:limit]:
                pic_b64 = None
                if remaining_pics > 0:
                    pic_b64 = _fetch_profile_pic_b64(str(user.profile_pic_url) if user.profile_pic_url else None)
                    remaining_pics -= 1
                items.append(LiveProfileItem(
                    username=str(user.username).lower().lstrip("@"),
                    full_name=str(user.full_name or ""),
                    is_private=bool(user.is_private),
                    profile_pic_b64=pic_b64,
                ))
            return items

        follower_items = _build_items(followers_dict, followers_limit)
        following_items = _build_items(following_dict, following_limit)
        follower_total = int(target_info.follower_count or 0)
        following_total = int(target_info.following_count or 0)
        followers_complete = follower_total <= len(follower_items)
        following_complete = following_total <= len(following_items)
        if not followers_complete:
            warnings.append(
                f"Vista parcial: se obtuvieron {len(follower_items)} de {follower_total} seguidores."
            )
        if not following_complete:
            warnings.append(
                f"Vista parcial: se obtuvieron {len(following_items)} de {following_total} seguidos."
            )

        preview = LiveProfilePreview(
            username=target_username.lower(),
            full_name=str(target_info.full_name or ""),
            is_private=bool(target_info.is_private),
            profile_pic_b64=target_pic_b64,
            follower_count=follower_total,
            following_count=following_total,
            followers=follower_items,
            following=following_items,
            followers_complete=followers_complete,
            following_complete=following_complete,
        )

        # --- Store pending scan ---
        scan_id = secrets.token_urlsafe(24)
        pending = PendingScan(
            scan_id=scan_id,
            target_username=target_username.lower(),
            followers=[item.username for item in follower_items],
            following=[item.username for item in following_items],
            warnings=tuple(warnings),
        )
        with _scan_lock:
            _purge_expired_scans()
            _pending_scans[scan_id] = pending

        return LiveScanResult(
            scan_id=scan_id,
            preview=preview,
            warnings=warnings,
        )

    except (LiveScanAuthError, LiveScanDisabledError, LiveScanRateLimitError):
        raise
    except ClientError as exc:
        raise LiveScanAuthError(
            "Instagram rechazó o interrumpió la exploración. "
            "Puede que la cuenta temporal esté bloqueada temporalmente."
        ) from exc
    except Exception as exc:
        logger.error("Error inesperado durante live scan: %s", exc, exc_info=True)
        raise LiveScanAuthError(
            "Ocurrió un error inesperado durante la exploración."
        ) from exc
    finally:
        # Always destroy the session — credentials never persist
        try:
            client.private.close()
            client.public.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Commit scan → create or merge analysis session
# ---------------------------------------------------------------------------


def commit_scan(scan_id: str, session_id: str | None = None) -> dict[str, Any]:
    """Convert a pending scan into a CircleScope analysis session.

    Returns a dict compatible with ``ImportResponse`` serialization.
    """
    _require_enabled()

    with _scan_lock:
        _purge_expired_scans()
        pending = _pending_scans.get(scan_id)
        if pending is None:
            raise LiveScanNotFoundError(
                "El scan ha caducado o ya fue confirmado. Vuelve a escanear."
            )

        target = pending.target_username
        followers_set = set(pending.followers)
        following_set = set(pending.following)

        # Build relationship maps identical to what the ZIP import produces.
        following_map: dict[str, set[str]] = {target: following_set}
        follower_map: dict[str, set[str]] = {target: followers_set}

        for username in following_set:
            following_map.setdefault(username, set())
            follower_map.setdefault(username, set()).add(target)
        for username in followers_set:
            follower_map.setdefault(username, set())
            following_map.setdefault(username, set()).add(target)

        if session_id:
            try:
                session_store.merge(session_id, target, following_map, follower_map)
            except SessionNotFoundError as exc:
                raise LiveScanNotFoundError("La sesión de análisis ya no existe o ha caducado.") from exc
            except ValueError as exc:
                raise LiveScanConflictError(
                    f"@{target} ya está incluida en la sesión actual."
                ) from exc
            final_session_id = session_id
        else:
            session = session_store.create(target, following_map, follower_map)
            final_session_id = session.session_id

        # Consume only after the session mutation succeeded, so a failed commit is retryable.
        _pending_scans.pop(scan_id, None)

    # Build the standard ImportResponse via the existing graph analyzer
    from backend.services.graph_analyzer import GraphAnalyzer
    from backend.domain.schemas import ImportResponse, ProfileSummary
    from backend.services.session_store import SESSION_TTL_SECONDS

    sess = session_store.get(final_session_id)
    analyzer = GraphAnalyzer(
        current_user_id=sess.root_user_id,
        following_map=sess.following_map,
        follower_map=sess.follower_map,
        imported_profiles=sess.imported_profiles,
        relationship_timestamps=sess.relationship_timestamps,
        relationship_sources=sess.relationship_sources,
    )

    summary = ProfileSummary(
        username=analyzer.current_user_id,
        followers=len(analyzer.l1_followers),
        following=len(analyzer.l1_followings),
        mutuals=len(analyzer.get_mutuals()),
        followers_only=len(analyzer.get_fans()),
        following_only=len(analyzer.get_traitors()),
    )

    return ImportResponse(
        session_id=final_session_id,
        summary=summary,
        graph=analyzer.get_base_graph(),
        expires_in_seconds=SESSION_TTL_SECONDS,
        warnings=list(pending.warnings),
        imported_profiles=sorted(sess.imported_profiles),
    ).model_dump()
