from pathlib import Path

import pytest

from src.infrastructure.prompts.prompt_registry import PromptRegistry


class TestPromptRegistry:
  @pytest.fixture
  def registry(self):
    base = Path("prompts")
    return PromptRegistry(base, base / "manifest.yaml")

  def test_load_active_version(self, registry):
    bundle = registry.load()
    assert bundle.version == "v1.0.0"
    assert bundle.module == "call_to_trade"
    assert "financial intent" in bundle.system_prompt.lower()

  def test_hashes_are_stable(self, registry):
    first = registry.load("v1.0.0")
    second = registry.load("v1.0.0")
    assert first.combined_hash == second.combined_hash
    assert len(first.system_hash) == 16

  def test_render_user_prompt(self, registry):
    bundle = registry.load()
    rendered = registry.render_user_prompt(bundle, "test transcript")
    assert "test transcript" in rendered

  def test_cache_returns_same_instance_fields(self, registry):
    a = registry.load()
    b = registry.load()
    assert a.version == b.version
    assert a.combined_hash == b.combined_hash

  def test_missing_version_raises(self, registry):
    with pytest.raises(FileNotFoundError):
      registry.load("v9.9.9")
