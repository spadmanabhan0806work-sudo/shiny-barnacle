from __future__ import annotations

from typing import Protocol


class StorageProvider(Protocol):
    async def upload(self, key: str, data: bytes) -> str:
        """Upload data and return the storage key."""
        ...

    async def download(self, key: str) -> bytes:
        """Download data by storage key."""
        ...

    async def delete(self, key: str) -> None:
        """Delete data by storage key."""
        ...

    async def exists(self, key: str) -> bool:
        """Check if a key exists in storage."""
        ...
