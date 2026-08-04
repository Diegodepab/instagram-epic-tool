"""Infrastructure adapter for official Instagram relationship exports.

The parser reads JSON directly from an archive (it never extracts files) or from
an already extracted directory. No network calls or credentials are involved.
"""

from __future__ import annotations

import io
import json
import re
import stat
import unicodedata
import zipfile
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO, TypeAlias

from pydantic import ValidationError

from backend.domain.models import RawFollowingDocument, RawRelationship


ExportSource: TypeAlias = str | Path | bytes | bytearray | BinaryIO

MAX_ARCHIVE_BYTES = 1024 * 1024 * 1024
MAX_JSON_BYTES = 100 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 200 * 1024 * 1024
MAX_ARCHIVE_MEMBERS = 10_000
MAX_COMPRESSION_RATIO = 200

_USERNAME_PATTERN = re.compile(r"^[a-z0-9._]{1,30}$")
_FOLLOWERS_FILE_PATTERN = re.compile(r"^followers.*\.json$", re.IGNORECASE)
_FOLLOWERS_HTML_PATTERN = re.compile(r"^followers.*\.html$", re.IGNORECASE)

_HTML_EXPORT_MESSAGE = (
    "Esta exportación de Instagram está en formato HTML. CircleScope necesita "
    "el ZIP en formato JSON. Solicita una nueva descarga y selecciona JSON, no HTML."
)


class InstagramExportError(ValueError):
    """Base error for an invalid or unsupported Instagram export."""


class ExportFormatError(InstagramExportError):
    """Raised when required JSON files or relationship structures are absent."""


class UnsafeArchiveError(InstagramExportError):
    """Raised when an archive violates the parser's security limits."""


@dataclass(frozen=True, slots=True)
class ExportDiagnostics:
    follower_entries: int
    following_entries: int
    earliest_follower_timestamp: int | None
    earliest_following_timestamp: int | None

    @property
    def likely_partial_followers(self) -> bool:
        if self.earliest_follower_timestamp is None or self.earliest_following_timestamp is None:
            return False
        two_years = 2 * 365 * 24 * 60 * 60
        return (
            self.follower_entries < self.following_entries
            and self.earliest_follower_timestamp - self.earliest_following_timestamp > two_years
        )


@dataclass(frozen=True, slots=True)
class ExtractedRelationships:
    root_username: str
    followers: frozenset[str]
    following: frozenset[str]
    follower_since: dict[str, int]
    following_since: dict[str, int]
    diagnostics: ExportDiagnostics


def extract_instagram_relationships(
    source: ExportSource,
    root_user_id: str,
) -> ExtractedRelationships:
    """Read and normalize every followers partition and the following document."""
    root = _normalise_username(root_user_id, field="root_user_id")
    documents = _read_relationship_documents(source)

    followers: set[str] = set()
    following: set[str] = set()
    followers_files = 0
    following_files = 0
    follower_timestamps: list[int] = []
    following_timestamps: list[int] = []
    follower_since: dict[str, int] = {}
    following_since: dict[str, int] = {}

    for filename, payload in documents:
        basename = PurePosixPath(filename).name.lower()
        if _FOLLOWERS_FILE_PATTERN.fullmatch(basename):
            followers_files += 1
            parsed, dated = _parse_relationship_entries(payload, filename, "followers")
            followers.update(parsed)
            _merge_earliest_timestamps(follower_since, dated)
            follower_timestamps.extend(_relationship_timestamps(payload, filename, "followers"))
        elif basename == "following.json":
            following_files += 1
            parsed, dated = _parse_relationship_entries(payload, filename, "following")
            following.update(parsed)
            _merge_earliest_timestamps(following_since, dated)
            following_timestamps.extend(_relationship_timestamps(payload, filename, "following"))

    if followers_files == 0 or following_files == 0:
        missing = []
        if followers_files == 0:
            missing.append("followers_N.json")
        if following_files == 0:
            missing.append("following.json")
        raise ExportFormatError(
            "Faltan los archivos JSON de relaciones requeridos: " + ", ".join(missing)
        )

    followers.discard(root)
    following.discard(root)

    diagnostics = ExportDiagnostics(
        follower_entries=len(followers),
        following_entries=len(following),
        earliest_follower_timestamp=min(follower_timestamps, default=None),
        earliest_following_timestamp=min(following_timestamps, default=None),
    )
    return ExtractedRelationships(
        root_username=root,
        followers=frozenset(followers),
        following=frozenset(following),
        follower_since=follower_since,
        following_since=following_since,
        diagnostics=diagnostics,
    )


def _read_relationship_documents(source: ExportSource) -> list[tuple[str, Any]]:
    if isinstance(source, (str, Path)):
        path = Path(source)
        if path.is_dir():
            return _read_directory(path)
        if not path.is_file():
            raise ExportFormatError(f"Export path does not exist or is not a file: {path}")
        if path.stat().st_size > MAX_ARCHIVE_BYTES:
            raise UnsafeArchiveError("ZIP archive exceeds the 1 GiB upload limit")
        try:
            with path.open("rb") as archive_file:
                return _read_zip(archive_file)
        except OSError as exc:
            raise ExportFormatError(f"Could not read export archive: {exc}") from exc

    if isinstance(source, (bytes, bytearray)):
        if len(source) > MAX_ARCHIVE_BYTES:
            raise UnsafeArchiveError("ZIP archive exceeds the 1 GiB upload limit")
        return _read_zip(io.BytesIO(source))

    if source.seekable():
        original_position = source.tell()
        source.seek(0, io.SEEK_END)
        archive_size = source.tell()
        source.seek(0)
        if archive_size > MAX_ARCHIVE_BYTES:
            raise UnsafeArchiveError("ZIP archive exceeds the 1 GiB upload limit")
        try:
            return _read_zip(source)
        finally:
            source.seek(original_position)

    archive_bytes = source.read(MAX_ARCHIVE_BYTES + 1)
    if len(archive_bytes) > MAX_ARCHIVE_BYTES:
        raise UnsafeArchiveError("ZIP archive exceeds the 1 GiB upload limit")
    return _read_zip(io.BytesIO(archive_bytes))


def _read_directory(root: Path) -> list[tuple[str, Any]]:
    documents: list[tuple[str, Any]] = []
    total_size = 0
    resolved_root = root.resolve(strict=True)

    for path in root.rglob("*.json"):
        if path.is_symlink():
            raise UnsafeArchiveError(f"Symbolic links are not allowed: {path.name}")
        resolved_path = path.resolve(strict=True)
        if not resolved_path.is_relative_to(resolved_root):
            raise UnsafeArchiveError(f"File escapes the export directory: {path.name}")
        relative_name = resolved_path.relative_to(resolved_root).as_posix()
        if not _is_relationship_file(relative_name):
            continue
        size = resolved_path.stat().st_size
        if size > MAX_JSON_BYTES:
            raise UnsafeArchiveError(f"JSON file exceeds the 100 MiB limit: {relative_name}")
        total_size += size
        if total_size > MAX_UNCOMPRESSED_BYTES:
            raise UnsafeArchiveError("Relationship JSON files exceed the 200 MiB limit")
        try:
            documents.append((relative_name, _decode_json(resolved_path.read_bytes(), relative_name)))
        except OSError as exc:
            raise ExportFormatError(f"Could not read {relative_name}: {exc}") from exc

    html_relationship_files = [
        path.relative_to(root).as_posix()
        for path in root.rglob("*.html")
        if _is_html_relationship_file(path.name)
    ]
    _reject_html_export_if_json_is_missing(
        [filename for filename, _ in documents],
        html_relationship_files,
    )
    return documents


def _read_zip(file: BinaryIO) -> list[tuple[str, Any]]:
    try:
        with zipfile.ZipFile(file) as archive:
            members = archive.infolist()
            if len(members) > MAX_ARCHIVE_MEMBERS:
                raise UnsafeArchiveError("ZIP archive contains too many files")

            member_names = [member.filename for member in members if not member.is_dir()]
            _reject_html_export_if_json_is_missing(
                [name for name in member_names if _is_relationship_file(name)],
                [name for name in member_names if _is_html_relationship_file(name)],
            )

            total_size = 0
            documents: list[tuple[str, Any]] = []
            for member in members:
                _validate_member(member)
                if member.is_dir() or not _is_relationship_file(member.filename):
                    continue
                total_size += member.file_size
                if total_size > MAX_UNCOMPRESSED_BYTES:
                    raise UnsafeArchiveError("Relationship JSON files exceed the 200 MiB limit")
                _validate_compression_ratio(member)
                if member.file_size > MAX_JSON_BYTES:
                    raise UnsafeArchiveError(
                        f"JSON file exceeds the 100 MiB limit: {member.filename}"
                    )
                with archive.open(member, "r") as json_file:
                    data = json_file.read(MAX_JSON_BYTES + 1)
                if len(data) > MAX_JSON_BYTES:
                    raise UnsafeArchiveError(
                        f"JSON file exceeds the 100 MiB limit: {member.filename}"
                    )
                documents.append((member.filename, _decode_json(data, member.filename)))
            return documents
    except zipfile.BadZipFile as exc:
        raise ExportFormatError("The uploaded file is not a valid ZIP archive") from exc


def _validate_member(member: zipfile.ZipInfo) -> None:
    name = member.filename.replace("\\", "/")
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts:
        raise UnsafeArchiveError(f"Unsafe path in ZIP archive: {member.filename}")
    if member.flag_bits & 0x1:
        raise UnsafeArchiveError("Encrypted ZIP files are not supported")
    unix_mode = member.external_attr >> 16
    if unix_mode and stat.S_ISLNK(unix_mode):
        raise UnsafeArchiveError(f"Symbolic links are not allowed: {member.filename}")


def _validate_compression_ratio(member: zipfile.ZipInfo) -> None:
    if member.file_size and member.compress_size == 0:
        raise UnsafeArchiveError(f"Invalid compression metadata: {member.filename}")
    if member.compress_size and member.file_size / member.compress_size > MAX_COMPRESSION_RATIO:
        raise UnsafeArchiveError(f"Suspicious compression ratio: {member.filename}")


def _is_relationship_file(filename: str) -> bool:
    normalised = filename.replace("\\", "/")
    path = PurePosixPath(normalised)
    if path.is_absolute() or ".." in path.parts:
        raise UnsafeArchiveError(f"Unsafe export path: {filename}")
    basename = path.name.lower()
    return basename == "following.json" or bool(_FOLLOWERS_FILE_PATTERN.fullmatch(basename))


def _is_html_relationship_file(filename: str) -> bool:
    """Recognise the equivalent files produced by Meta's HTML export option."""
    normalised = filename.replace("\\", "/")
    path = PurePosixPath(normalised)
    if path.is_absolute() or ".." in path.parts:
        raise UnsafeArchiveError(f"Unsafe export path: {filename}")
    basename = path.name.lower()
    return basename == "following.html" or bool(_FOLLOWERS_HTML_PATTERN.fullmatch(basename))


def _reject_html_export_if_json_is_missing(
    json_files: Iterable[str],
    html_files: Iterable[str],
) -> None:
    json_basenames = {PurePosixPath(name.replace("\\", "/")).name.lower() for name in json_files}
    html_basenames = {PurePosixPath(name.replace("\\", "/")).name.lower() for name in html_files}
    has_json_followers = any(_FOLLOWERS_FILE_PATTERN.fullmatch(name) for name in json_basenames)
    has_html_followers = any(_FOLLOWERS_HTML_PATTERN.fullmatch(name) for name in html_basenames)
    missing_json_has_html_equivalent = (
        (not has_json_followers and has_html_followers)
        or ("following.json" not in json_basenames and "following.html" in html_basenames)
    )
    if missing_json_has_html_equivalent:
        raise ExportFormatError(_HTML_EXPORT_MESSAGE)


def _decode_json(data: bytes, filename: str) -> Any:
    try:
        return json.loads(data.decode("utf-8-sig"))
    except UnicodeDecodeError as exc:
        raise ExportFormatError(f"{filename} is not UTF-8 JSON") from exc
    except json.JSONDecodeError as exc:
        raise ExportFormatError(f"Malformed JSON in {filename}: {exc.msg}") from exc


def _parse_relationship_entries(
    payload: Any,
    filename: str,
    kind: str,
) -> tuple[set[str], dict[str, int]]:
    entries = _relationship_entries(payload, filename, kind)

    usernames: set[str] = set()
    timestamps: dict[str, int] = {}
    for entry in entries:
        try:
            RawRelationship.model_validate(entry)
        except ValidationError as exc:
            raise ExportFormatError(f"Invalid relationship entry in {filename}") from exc
        candidates = tuple(_username_candidates(entry))
        if not candidates:
            raise ExportFormatError(f"Relationship without a username in {filename}")
        entry_timestamps = _find_integer_values(entry, "timestamp")
        for candidate in candidates:
            username = _normalise_username(candidate, field=filename)
            usernames.add(username)
            if entry_timestamps:
                timestamp = min(entry_timestamps)
                timestamps[username] = min(timestamp, timestamps.get(username, timestamp))
    return usernames, timestamps


def _merge_earliest_timestamps(target: dict[str, int], incoming: Mapping[str, int]) -> None:
    for username, timestamp in incoming.items():
        target[username] = min(timestamp, target.get(username, timestamp))


def _relationship_entries(payload: Any, filename: str, kind: str) -> list[Any]:
    entries: Any = payload
    if isinstance(payload, Mapping):
        expected_key = "relationships_following" if kind == "following" else "relationships_followers"
        if kind == "following" and expected_key in payload:
            try:
                RawFollowingDocument.model_validate(payload)
            except ValidationError as exc:
                raise ExportFormatError(f"Invalid following document in {filename}") from exc
        entries = payload.get(expected_key)
        if entries is None and kind == "followers":
            entries = payload.get("relationships_followers_and_following")

    if not isinstance(entries, list):
        raise ExportFormatError(f"Unexpected {kind} structure in {filename}")
    return entries


def _relationship_timestamps(payload: Any, filename: str, kind: str) -> list[int]:
    timestamps: list[int] = []
    entries = _relationship_entries(payload, filename, kind)
    for entry in entries:
        timestamps.extend(_find_integer_values(entry, "timestamp"))
    return timestamps


def _username_candidates(entry: Any) -> Iterable[str]:
    if not isinstance(entry, Mapping):
        return ()
    values = list(_find_string_values(entry, "value"))
    if not values and isinstance(entry.get("title"), str):
        values.append(entry["title"])
    if not values:
        hrefs = _find_string_values(entry, "href")
        for href in hrefs:
            candidate = href.rstrip("/").rsplit("/", 1)[-1]
            if candidate:
                values.append(candidate)
    return values


def _find_string_values(value: Any, target_key: str) -> list[str]:
    found: list[str] = []
    pending = [value]
    while pending:
        current = pending.pop()
        if isinstance(current, Mapping):
            direct = current.get(target_key)
            if isinstance(direct, str):
                found.append(direct)
            pending.extend(
                nested for nested in current.values() if isinstance(nested, (Mapping, list))
            )
        elif isinstance(current, list):
            pending.extend(current)
    return found


def _find_integer_values(value: Any, target_key: str) -> list[int]:
    found: list[int] = []
    pending = [value]
    while pending:
        current = pending.pop()
        if isinstance(current, Mapping):
            direct = current.get(target_key)
            if isinstance(direct, int):
                found.append(direct)
            pending.extend(
                nested for nested in current.values() if isinstance(nested, (Mapping, list))
            )
        elif isinstance(current, list):
            pending.extend(current)
    return found


def _normalise_username(value: str, *, field: str) -> str:
    username = unicodedata.normalize("NFKC", value).strip().removeprefix("@").lower()
    if not _USERNAME_PATTERN.fullmatch(username):
        raise ExportFormatError(f"Invalid Instagram username in {field}")
    return username
