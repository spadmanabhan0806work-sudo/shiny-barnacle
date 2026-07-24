from __future__ import annotations

from pathlib import Path


class LocalStorageAdapter:
    """Local filesystem storage adapter."""

    def __init__(self, base_path: Path) -> None:
        self._base_path = base_path
        self._base_path.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        return self._base_path / key

    async def upload(self, key: str, data: bytes) -> str:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return key

    async def download(self, key: str) -> bytes:
        path = self._resolve(key)
        if not path.exists():
            raise FileNotFoundError(f"Storage key not found: {key}")
        return path.read_bytes()

    async def delete(self, key: str) -> None:
        path = self._resolve(key)
        if path.exists():
            path.unlink()

    async def exists(self, key: str) -> bool:
        return self._resolve(key).exists()
