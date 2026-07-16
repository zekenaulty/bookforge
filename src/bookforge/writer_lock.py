from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import socket
import threading
from typing import BinaryIO, Iterator


class BookWriterLockError(RuntimeError):
    """Raised when a second process tries to mutate an active book run."""


_HELD_LOCKS: set[str] = set()
_HELD_LOCKS_GUARD = threading.Lock()


def writer_lock_path(book_root: Path) -> Path:
    return book_root / ".bookforge" / "writer.lock"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _lock_key(path: Path) -> str:
    return os.path.normcase(str(path.resolve()))


def _read_owner(path: Path) -> dict[str, object]:
    try:
        with path.open("rb") as handle:
            handle.seek(1)
            payload = handle.read()
        loaded = json.loads(payload.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _owner_summary(path: Path) -> str:
    owner = _read_owner(path)
    details = []
    for key in ("pid", "hostname", "operation", "acquired_at"):
        value = owner.get(key)
        if value not in (None, ""):
            details.append(f"{key}={value}")
    return ", ".join(details) if details else "owner metadata unavailable"


def _try_platform_lock(handle: BinaryIO) -> bool:
    handle.seek(0)
    if os.name == "nt":
        import msvcrt

        try:
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            return False
        return True

    import fcntl

    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return False
    return True


def _platform_unlock(handle: BinaryIO) -> None:
    handle.seek(0)
    if os.name == "nt":
        import msvcrt

        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        return

    import fcntl

    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _open_lock_file(path: Path) -> BinaryIO:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    handle = os.fdopen(descriptor, "r+b", buffering=0)
    if os.fstat(handle.fileno()).st_size == 0:
        handle.write(b"\0")
        os.fsync(handle.fileno())
    return handle


def _write_owner(handle: BinaryIO, operation: str) -> None:
    owner = {
        "schema_version": "book_writer_lock_v1",
        "pid": os.getpid(),
        "hostname": socket.gethostname(),
        "operation": operation,
        "acquired_at": _utc_now_iso(),
    }
    payload = json.dumps(owner, ensure_ascii=True, sort_keys=True).encode("utf-8")
    handle.seek(0)
    handle.write(b"\0" + payload)
    handle.truncate()
    os.fsync(handle.fileno())


@contextmanager
def book_writer_lock(book_root: Path, *, operation: str = "book mutation") -> Iterator[Path]:
    """Hold a non-blocking, cross-process lock for one book workspace."""

    root = Path(book_root)
    path = writer_lock_path(root)
    key = _lock_key(path)

    with _HELD_LOCKS_GUARD:
        if key in _HELD_LOCKS:
            raise BookWriterLockError(
                f"Book writer lock is already held for '{root}'. Refusing concurrent "
                f"mutation. Lock: {path}. Owner: {_owner_summary(path)}"
            )
        _HELD_LOCKS.add(key)

    handle: BinaryIO | None = None
    locked = False
    try:
        handle = _open_lock_file(path)
        locked = _try_platform_lock(handle)
        if not locked:
            raise BookWriterLockError(
                f"Book writer lock is already held for '{root}'. Refusing concurrent "
                f"mutation. Lock: {path}. Owner: {_owner_summary(path)}"
            )
        _write_owner(handle, operation)
        yield path
    except BookWriterLockError:
        raise
    except OSError as exc:
        raise BookWriterLockError(f"Could not acquire book writer lock '{path}': {exc}") from exc
    finally:
        try:
            if locked and handle is not None:
                try:
                    _platform_unlock(handle)
                finally:
                    handle.close()
            elif handle is not None:
                handle.close()
        finally:
            with _HELD_LOCKS_GUARD:
                _HELD_LOCKS.discard(key)
