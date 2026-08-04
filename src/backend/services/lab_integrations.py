"""Bounded integrations for third-party repositories kept under ``lab/``.

The offensive repository is never imported. Its integration is intentionally a
static source-code assessment. Instagrapi is imported lazily only when the
operator enables the feature explicitly.
"""

from __future__ import annotations

import ast
import hashlib
import os
import threading
import time
from pathlib import Path
from typing import Any


MAX_RELATIONSHIPS = 50
MAX_MEDIA = 12
REQUEST_COOLDOWN_SECONDS = 60
_last_request: dict[str, float] = {}
_rate_lock = threading.Lock()


class LabDisabledError(RuntimeError):
    pass


class LabRateLimitError(RuntimeError):
    pass


class LabAuthenticationError(RuntimeError):
    pass


def _lab_root() -> Path:
    configured = os.getenv("LAB_ROOT")
    if configured:
        return Path(configured).resolve()
    return Path(__file__).resolve().parents[3] / "lab"


def integration_status() -> dict[str, Any]:
    root = _lab_root()
    return {
        "instagrapi": {
            "available": (root / "instagrapi" / "instagrapi").is_dir(),
            "enabled": os.getenv("ENABLE_INSTAGRAPI_LAB", "false").lower() == "true",
            "mode": "cuenta_propia",
            "limits": {"relationships": MAX_RELATIONSHIPS, "media": MAX_MEDIA},
        },
        "instagram_bruter": {
            "available": (root / "Instagram-" / "instagram.py").is_file(),
            "enabled": True,
            "mode": "analisis_estatico_sin_ejecucion",
        },
    }


def inspect_offensive_repository() -> dict[str, Any]:
    """Inspect Python sources without importing or executing any lab code."""
    repository = (_lab_root() / "Instagram-").resolve()
    if not repository.is_dir() or repository.parent != _lab_root().resolve():
        raise FileNotFoundError("No se encontró el repositorio defensivo en lab/Instagram-.")

    indicators = {
        "credential_attempts": ("password", "passlist", "authenticated"),
        "proxy_rotation": ("proxy", "proxies"),
        "concurrency": ("thread", "queue"),
        "external_requests": ("requests", "HTMLSession", ".post", ".get"),
    }
    counts = {key: 0 for key in indicators}
    files: list[dict[str, Any]] = []
    total_functions = 0
    total_classes = 0

    for source_path in sorted(repository.rglob("*.py")):
        if source_path.is_symlink() or not source_path.resolve().is_relative_to(repository):
            continue
        raw = source_path.read_bytes()
        if len(raw) > 512_000:
            continue
        text = raw.decode("utf-8", errors="replace")
        try:
            tree = ast.parse(text, filename=str(source_path))
        except SyntaxError:
            continue
        functions = sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) for node in ast.walk(tree))
        classes = sum(isinstance(node, ast.ClassDef) for node in ast.walk(tree))
        total_functions += functions
        total_classes += classes
        lowered = text.lower()
        for category, needles in indicators.items():
            counts[category] += sum(lowered.count(needle.lower()) for needle in needles)
        files.append({
            "path": source_path.relative_to(repository).as_posix(),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "functions": functions,
            "classes": classes,
        })

    return {
        "repository": "Bitwise-01/Instagram-",
        "mode": "static_only",
        "executed": False,
        "network_access": False,
        "classification": "prohibited_offensive_capability",
        "summary": {"python_files": len(files), "functions": total_functions, "classes": total_classes},
        "indicator_counts": counts,
        "files": files,
    }


def inspect_own_instagram_account(
    username: str,
    password: str,
    relationship_limit: int,
    media_limit: int,
    requester_key: str,
) -> dict[str, Any]:
    if os.getenv("ENABLE_INSTAGRAPI_LAB", "false").lower() != "true":
        raise LabDisabledError("La integración instagrapi está desactivada por el operador.")

    now = time.monotonic()
    with _rate_lock:
        previous = _last_request.get(requester_key, 0)
        if now - previous < REQUEST_COOLDOWN_SECONDS:
            raise LabRateLimitError("Espera un minuto antes de iniciar otra consulta experimental.")
        _last_request[requester_key] = now

    try:
        from instagrapi import Client
        from instagrapi.exceptions import ClientError
    except ImportError as exc:
        raise LabDisabledError("El repositorio instagrapi no está instalado en el backend.") from exc

    client = Client()
    client.request_timeout = 15
    client.delay_range = [1, 2]
    try:
        if not client.login(username, password):
            raise LabAuthenticationError("Instagram rechazó el inicio de sesión.")
        account = client.account_info()
        authenticated_username = str(account.username).lower()
        if authenticated_username != username.lower().lstrip("@"):
            raise LabAuthenticationError("La identidad autenticada no coincide con la cuenta declarada.")

        user_id = str(account.pk)
        profile = client.user_info(user_id)
        following = client.user_following(user_id, amount=min(relationship_limit, MAX_RELATIONSHIPS))
        followers = client.user_followers(user_id, amount=min(relationship_limit, MAX_RELATIONSHIPS))
        media = client.user_medias(user_id, amount=min(media_limit, MAX_MEDIA))
        return {
            "username": authenticated_username,
            "full_name": account.full_name,
            "is_private": account.is_private,
            "follower_count": profile.follower_count,
            "following_count": profile.following_count,
            "followers_sample": [item.username for item in followers.values() if item.username],
            "following_sample": [item.username for item in following.values() if item.username],
            "media_sample": [
                {"id": str(item.pk), "code": item.code, "media_type": int(item.media_type)}
                for item in media
            ],
            "limits_applied": {"relationships": min(relationship_limit, MAX_RELATIONSHIPS), "media": min(media_limit, MAX_MEDIA)},
        }
    except LabAuthenticationError:
        raise
    except ClientError as exc:
        raise LabAuthenticationError("Instagram rechazó o interrumpió la consulta experimental.") from exc
    finally:
        # Nothing is dumped to disk: credentials and session stay in this request only.
        client.private.close()
        client.public.close()
