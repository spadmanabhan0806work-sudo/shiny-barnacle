"""Tests for K8s Helm chart and manifest structure."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
CHART_DIR = ROOT / "k8s" / "helm" / "operyx"


class TestHelmChart:
    def test_chart_metadata_exists(self):
        chart_yaml = yaml.safe_load((CHART_DIR / "Chart.yaml").read_text(encoding="utf-8"))
        assert chart_yaml["name"] == "operyx"
        assert chart_yaml["apiVersion"] == "v2"

    def test_values_has_required_components(self):
        values = yaml.safe_load((CHART_DIR / "values.yaml").read_text(encoding="utf-8"))
        assert values["replicaCount"]["api"] >= 1
        assert values["postgres"]["enabled"] is True
        assert values["redis"]["enabled"] is True
        assert "worker" in values["image"]
        assert "dashboard" in values["image"]

    def test_templates_cover_core_workloads(self):
        templates = {p.stem for p in (CHART_DIR / "templates").glob("*.yaml")}
        required = {"api", "worker", "dashboard", "postgres", "redis", "secret", "configmap"}
        assert required.issubset(templates)

    def test_worker_gpu_config_optional(self):
        values = yaml.safe_load((CHART_DIR / "values.yaml").read_text(encoding="utf-8"))
        assert values["worker"]["gpu"]["enabled"] is False

    def test_hpa_enabled_for_workers(self):
        values = yaml.safe_load((CHART_DIR / "values.yaml").read_text(encoding="utf-8"))
        assert values["hpa"]["enabled"] is True
        assert values["hpa"]["worker"]["maxReplicas"] >= values["hpa"]["worker"]["minReplicas"]

    def test_prod_overlay_enables_gpu(self):
        overlay = yaml.safe_load(
            (ROOT / "k8s" / "overlays" / "prod" / "values.yaml").read_text(encoding="utf-8")
        )
        assert overlay["worker"]["gpu"]["enabled"] is True

    def test_base_namespace_manifest(self):
        ns_path = ROOT / "k8s" / "base" / "namespace.yaml"
        assert ns_path.exists()
        content = ns_path.read_text(encoding="utf-8")
        assert "kind: Namespace" in content

    def test_ci_workflow_exists(self):
        workflow = ROOT / ".github" / "workflows" / "ci.yml"
        assert workflow.exists()
        content = workflow.read_text(encoding="utf-8")
        assert "pytest tests/" in content

    def test_security_docs_exist(self):
        assert (ROOT / "docs" / "security.md").exists()
        assert (ROOT / "docs" / "k8s-runbook.md").exists()

    @pytest.mark.parametrize(
        "template_file",
        [
            "api.yaml",
            "worker.yaml",
            "dashboard.yaml",
        ],
    )
    def test_deployments_have_probes_or_health(self, template_file: str):
        content = (CHART_DIR / "templates" / template_file).read_text(encoding="utf-8")
        if template_file == "worker.yaml":
            assert "resources:" in content
        else:
            assert "Probe" in content or "probe" in content
