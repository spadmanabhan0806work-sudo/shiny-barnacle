
from src.infrastructure.config.settings import Settings


class TestSettings:
    def test_default_values(self):
        settings = Settings()
        assert settings.tenant_id == "default"
        assert settings.storage_backend == "local"

    def test_load_yaml(self, tmp_path):
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        yaml_file = config_dir / "default.yaml"
        yaml_file.write_text("app:\n  name: test-operyx\n")
        settings = Settings()
        settings.load_yaml(yaml_file)
        assert settings.get("app.name") == "test-operyx"

    def test_get_nested_key_missing_returns_default(self):
        settings = Settings()
        settings.yaml_config = {}
        assert settings.get("missing.key", "fallback") == "fallback"
