from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID


@dataclass
class GoldEntry:
    call_id: UUID | None
    ground_truth: dict
    prediction: dict | None = None


@dataclass
class GoldDataset:
    version: str
    name: str
    description: str
    entries: list[GoldEntry]

    @classmethod
    def from_path(cls, path: Path) -> "GoldDataset":
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        entries = []
        for item in raw.get("entries", []):
            call_id = UUID(item["call_id"]) if item.get("call_id") else None
            entries.append(
                GoldEntry(
                    call_id=call_id,
                    ground_truth=item["ground_truth"],
                    prediction=item.get("prediction"),
                )
            )
        return cls(
            version=raw.get("version", "1.0"),
            name=raw.get("name", path.stem),
            description=raw.get("description", ""),
            entries=entries,
        )

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "name": self.name,
            "description": self.description,
            "entries": [
                {
                    "call_id": str(entry.call_id) if entry.call_id else None,
                    "ground_truth": entry.ground_truth,
                    "prediction": entry.prediction,
                }
                for entry in self.entries
            ],
        }
