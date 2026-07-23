import json
from pathlib import Path

import pytest

from src.adapters.llm.mock_llm_adapter import MockLLMAdapter
from src.infrastructure.prompts.prompt_registry import PromptRegistry


FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.asyncio
async def test_mock_llm_extracts_buy_intent():
  adapter = MockLLMAdapter()
  transcript = (
    "I want to buy one hundred shares of Reliance at twenty five hundred rupees on NSE."
  )
  result = await adapter.extract_structured(transcript, {}, prompt_version="v1.0.0")
  assert result.data["side"] == "BUY"
  assert result.data["stock_symbol"].lower() == "reliance"
  assert result.data["quantity"] == 100
  assert result.data["exchange"] == "NSE"
  assert result.provider == "mock"


@pytest.mark.asyncio
@pytest.mark.parametrize(
  "fixture_file",
  ["en_buy_reliance.json", "hi_buy_reliance.json", "mixed_buy_reliance.json"],
)
async def test_fixture_transcripts_match_schema(fixture_file):
  registry = PromptRegistry(Path("prompts"), Path("prompts/manifest.yaml"))
  bundle = registry.load()
  adapter = MockLLMAdapter()

  fixture = json.loads((FIXTURES / fixture_file).read_text(encoding="utf-8"))
  result = await adapter.extract_structured(
    fixture["transcript"],
    bundle.schema,
    prompt_version=bundle.version,
  )

  for field in bundle.schema["required"]:
    assert field in result.data, f"Missing required field: {field}"

  props = bundle.schema["properties"]
  assert result.data["side"] in props["side"]["enum"]
  assert result.data["exchange"] in props["exchange"]["enum"]
  assert result.data["quantity"] >= props["quantity"]["minimum"]
  assert result.data["price"] >= props["price"]["minimum"]
  assert 0 <= result.data["confidence"] <= 1
