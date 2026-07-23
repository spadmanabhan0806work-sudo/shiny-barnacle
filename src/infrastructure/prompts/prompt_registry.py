from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class PromptBundle:
    version: str
    module: str
    system_prompt: str
    user_prompt_template: str
    schema: dict
    system_hash: str
    user_hash: str
    combined_hash: str


class PromptRegistry:
    """Load, hash, and cache versioned prompts from the prompts directory."""

    def __init__(
        self,
        base_path: Path,
        manifest_path: Path | None = None,
    ) -> None:
        self._base_path = base_path
        self._manifest_path = manifest_path or base_path / "manifest.yaml"
        self._cache: dict[str, PromptBundle] = {}

    @staticmethod
    def _hash_content(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

    def _load_manifest(self) -> dict:
        if not self._manifest_path.exists():
            raise FileNotFoundError(f"Prompt manifest not found: {self._manifest_path}")
        with open(self._manifest_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def get_active_version(self, module: str = "call_to_trade") -> str:
        manifest = self._load_manifest()
        if manifest.get("module") == module:
            return manifest.get("active_version", "v1.0.0")
        versions = manifest.get("versions", {})
        for version, meta in versions.items():
            if meta.get("is_active"):
                return version
        return manifest.get("active_version", "v1.0.0")

    def get_manifest(self) -> dict:
        return self._load_manifest()

    def list_versions(self, module: str = "call_to_trade") -> list[str]:
        manifest = self._load_manifest()
        versions = manifest.get("versions", {})
        if versions:
            return sorted(versions.keys())
        version_dir = self._base_path / module
        if not version_dir.exists():
            return []
        return sorted(p.name for p in version_dir.iterdir() if p.is_dir())

    def get_weight(self, version: str) -> float:
        manifest = self._load_manifest()
        return manifest.get("versions", {}).get(version, {}).get("weight", 0.0)

    def set_active_version(self, version: str, module: str = "call_to_trade") -> None:
        manifest = self._load_manifest()
        manifest["active_version"] = version
        manifest["module"] = module
        versions = manifest.setdefault("versions", {})
        for ver in versions:
            versions[ver]["is_active"] = ver == version
        if version not in versions:
            versions[version] = {"weight": 1.0, "is_active": True}
        self._write_manifest(manifest)
        self._cache.clear()

    def update_weights(self, weights: dict[str, float]) -> None:
        manifest = self._load_manifest()
        versions = manifest.setdefault("versions", {})
        for version, weight in weights.items():
            versions.setdefault(version, {})["weight"] = weight
        self._write_manifest(manifest)
        self._cache.clear()

    def _write_manifest(self, manifest: dict) -> None:
        with open(self._manifest_path, "w", encoding="utf-8") as f:
            yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)

    def load(self, version: str | None = None, module: str = "call_to_trade") -> PromptBundle:
        resolved_version = version or self.get_active_version(module)
        cache_key = f"{module}:{resolved_version}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        version_dir = self._base_path / module / resolved_version
        system_path = version_dir / "system.md"
        user_path = version_dir / "user.md"
        schema_path = version_dir / "schema.json"

        if not system_path.exists() or not user_path.exists() or not schema_path.exists():
            raise FileNotFoundError(f"Prompt version not found: {version_dir}")

        system_prompt = system_path.read_text(encoding="utf-8")
        user_prompt_template = user_path.read_text(encoding="utf-8")
        with open(schema_path, encoding="utf-8") as f:
            schema = json.load(f)

        system_hash = self._hash_content(system_prompt)
        user_hash = self._hash_content(user_prompt_template)
        combined_hash = self._hash_content(system_prompt + user_prompt_template + json.dumps(schema))

        bundle = PromptBundle(
            version=resolved_version,
            module=module,
            system_prompt=system_prompt,
            user_prompt_template=user_prompt_template,
            schema=schema,
            system_hash=system_hash,
            user_hash=user_hash,
            combined_hash=combined_hash,
        )
        self._cache[cache_key] = bundle
        return bundle

    def render_user_prompt(self, bundle: PromptBundle, transcript: str) -> str:
        return bundle.user_prompt_template.replace("{transcript}", transcript)
