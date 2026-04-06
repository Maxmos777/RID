"""
Traefik docker-compose configuration tests.

Validates that ST-001-01 (Traefik service) and ST-001-02 (Langflow labels)
are correctly configured in docker-compose.yml.

Feature: rid-langflow-single-entry
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
COMPOSE_FILE = REPO_ROOT / "docker-compose.yml"


@pytest.fixture(scope="module")
def compose_config() -> dict:
    """Load and parse docker-compose.yml."""
    return yaml.safe_load(COMPOSE_FILE.read_text())


@pytest.fixture(scope="module")
def compose_raw() -> str:
    """Raw content of docker-compose.yml for string-based assertions."""
    return COMPOSE_FILE.read_text()


# ---------------------------------------------------------------------------
# ST-001-01: Traefik service
# ---------------------------------------------------------------------------

class TestTraefikService:
    def test_traefik_service_exists(self, compose_config):
        """ST-001-01: traefik service must be declared."""
        assert "traefik" in compose_config["services"], (
            "Traefik service not found in docker-compose.yml. "
            "See ST-001-01-traefik-docker-compose.md"
        )

    def test_traefik_image_pinned(self, compose_config):
        """ST-001-01: Traefik image must be pinned to v3.3.6."""
        image = compose_config["services"]["traefik"]["image"]
        assert image == "traefik:v3.3.6", (
            f"Traefik image must be 'traefik:v3.3.6', got '{image}'. "
            "Pinned versions prevent unexpected upgrades in production."
        )

    def test_traefik_container_name(self, compose_config):
        """ST-001-01: Container name must be rid-traefik."""
        name = compose_config["services"]["traefik"].get("container_name")
        assert name == "rid-traefik", (
            f"container_name must be 'rid-traefik', got '{name}'."
        )

    def test_traefik_port_80(self, compose_raw):
        """ST-001-01: Port 80:80 must be exposed."""
        assert "80:80" in compose_raw, "Port 80:80 not found in docker-compose.yml."

    def test_traefik_port_443(self, compose_raw):
        """ST-001-01: Port 443:443 must be exposed."""
        assert "443:443" in compose_raw, "Port 443:443 not found in docker-compose.yml."

    def test_traefik_docker_socket_readonly(self, compose_raw):
        """ST-001-01: Docker socket must be mounted read-only."""
        assert "/var/run/docker.sock:/var/run/docker.sock:ro" in compose_raw, (
            "Docker socket must be mounted read-only (:ro). "
            "Write access to the socket is a security risk."
        )

    def test_traefik_profile_langflow(self, compose_config):
        """ST-001-01: Traefik must be under the 'langflow' profile."""
        profiles = compose_config["services"]["traefik"].get("profiles", [])
        assert "langflow" in profiles, (
            f"Traefik must be in 'langflow' profile, got profiles={profiles}."
        )

    def test_traefik_network_rid_network(self, compose_config):
        """ST-001-01: Traefik must be connected to rid-network."""
        networks = compose_config["services"]["traefik"].get("networks", [])
        # networks can be a list or a dict
        if isinstance(networks, dict):
            assert "rid-network" in networks
        else:
            assert "rid-network" in networks, (
                "Traefik must be connected to rid-network."
            )

    def test_certs_directory_exists(self):
        """ST-001-01: certs/ directory must exist for TLS certificates."""
        certs_dir = REPO_ROOT / "certs"
        assert certs_dir.is_dir(), (
            "certs/ directory not found. Required for TLS certificate volume."
        )


# ---------------------------------------------------------------------------
# ST-001-02: Langflow labels and forwardAuth
# ---------------------------------------------------------------------------

class TestLangflowTraefikLabels:
    def test_langflow_port_7861_removed(self, compose_config):
        """ST-001-02: Public port 7861 must be removed from langflow service."""
        langflow = compose_config["services"].get("langflow", {})
        ports = langflow.get("ports", [])
        port_strings = [str(p) for p in ports]
        assert not any("7861" in p for p in port_strings), (
            "Port 7861:7860 must be removed from langflow service. "
            "Langflow is internal-only, accessed via Traefik."
        )

    def test_langflow_traefik_enabled(self, compose_raw):
        """ST-001-02: traefik.enable=true label must be present on langflow."""
        assert "traefik.enable=true" in compose_raw, (
            "traefik.enable=true label not found. "
            "Langflow must be discovered by Traefik."
        )

    def test_langflow_forward_auth_address(self, compose_raw):
        """ST-001-02: forwardAuth must point to Django auth-check endpoint."""
        assert "backend:8000/internal/auth-check/" in compose_raw, (
            "forwardAuth address not pointing to /internal/auth-check/. "
            "All Langflow requests must be validated by Django auth."
        )

    def test_langflow_trust_forward_header(self, compose_raw):
        """ST-001-02: trustForwardHeader must be enabled."""
        assert "trustForwardHeader=true" in compose_raw, (
            "trustForwardHeader=true not found. "
            "Required so Django receives the original client IP."
        )

    def test_langflow_websocket_middleware(self, compose_raw):
        """ST-001-02: WebSocket middleware langflow-ws must be declared."""
        assert "langflow-ws" in compose_raw, (
            "langflow-ws WebSocket middleware not found. "
            "Required for WebSocket connections to Langflow."
        )

    def test_langflow_path_prefix_flows(self, compose_raw):
        """ST-001-02: Router rule must match /flows prefix."""
        assert "PathPrefix" in compose_raw and "/flows" in compose_raw, (
            "PathPrefix('/flows') router rule not found. "
            "Traefik must route /flows/* to Langflow."
        )

    def test_langflow_base_url_internal(self, compose_raw):
        """ST-001-02: LANGFLOW_BASE_URL must point to internal container URL."""
        assert "LANGFLOW_BASE_URL" in compose_raw, (
            "LANGFLOW_BASE_URL not found in docker-compose.yml. "
            "Langflow must know its own internal URL."
        )
        assert "langflow:7860" in compose_raw, (
            "LANGFLOW_BASE_URL must point to http://langflow:7860 (internal). "
            "External URLs break container networking."
        )

    def test_langflow_service_port_7860(self, compose_raw):
        """ST-001-02: Traefik loadbalancer must use internal port 7860."""
        assert "loadbalancer.server.port=7860" in compose_raw, (
            "Traefik loadbalancer server port must be 7860 (Langflow native port)."
        )
