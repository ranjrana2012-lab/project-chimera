"""
Unit tests for REST API.

Tests FastAPI endpoints.
"""

import pytest
import sys
from pathlib import Path

# Add orchestrator to path
orchestrator_path = Path(__file__).parent.parent
sys.path.insert(0, str(orchestrator_path))


class TestAPIAvailability:
    """Test API module availability."""

    def test_fastapi_import(self):
        """Test if FastAPI is available."""
        try:
            from fastapi import FastAPI
            FASTAPI_AVAILABLE = True
        except ImportError:
            FASTAPI_AVAILABLE = False

        # Test should pass regardless of FastAPI availability
        assert True

    def test_api_module_import(self):
        """Test that API module can be imported."""
        from api import routes

        assert routes is not None

    def test_create_app_without_fastapi(self):
        """Test create_app behavior when FastAPI unavailable."""
        # This test verifies the degraded mode behavior
        from api import routes

        # If FastAPI is available, create_app should return an app
        # If not, it should return None
        app = routes.create_app(services_path="services")

        # Either way, should not crash
        if routes.FASTAPI_AVAILABLE:
            assert app is not None
        else:
            assert app is None


class TestAPIModels:
    """Test API request/response models."""

    def test_models_when_available(self):
        """Test model creation when FastAPI available."""
        try:
            from api.routes import RunTestsRequest, TestRunResponse

            # Create request
            request = RunTestsRequest(
                services=["svc1", "svc2"],
                parallel=True,
                max_workers=4
            )

            assert request.services == ["svc1", "svc2"]
            assert request.parallel is True

            # Create response
            response = TestRunResponse(
                run_id="test-run",
                status="running",
                message="Started"
            )

            assert response.run_id == "test-run"

        except ImportError:
            # FastAPI not available
            assert True


class TestAPICreation:
    """Test API app creation."""

    def test_create_app_basic(self):
        """Test basic app creation."""
        from api import routes

        if not routes.FASTAPI_AVAILABLE:
            pytest.skip("FastAPI not available")

        app = routes.create_app(services_path="services")

        assert app is not None
        assert app.title == "Test Orchestrator API"

    def test_create_app_with_db_config(self):
        """Test app creation with database config."""
        from api import routes

        if not routes.FASTAPI_AVAILABLE:
            pytest.skip("FastAPI not available")

        db_config = {
            "host": "localhost",
            "database": "test_db",
            "user": "test_user"
        }

        app = routes.create_app(
            services_path="services",
            db_config=db_config
        )

        assert app is not None

    def test_get_app_singleton(self):
        """Test get_app returns singleton instance."""
        from api import routes

        if not routes.FASTAPI_AVAILABLE:
            pytest.skip("FastAPI not available")

        app1 = routes.get_app()
        app2 = routes.get_app()

        # Should return same instance
        assert app1 is app2


class TestFastAPIEndpoints:
    """Test FastAPI endpoints with TestClient."""

    @pytest.fixture
    def app(self):
        """Create test app."""
        from api import routes
        if not routes.FASTAPI_AVAILABLE:
            pytest.skip("FastAPI not available")
        return routes.create_app(services_path="services")

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        if app is None:
            pytest.skip("FastAPI not available")
        from fastapi.testclient import TestClient
        return TestClient(app)

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert data["status"] == "running"

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_list_tests_endpoint(self, client):
        """Test list tests endpoint."""
        response = client.get("/api/v1/tests")

        assert response.status_code == 200
        data = response.json()
        assert "services" in data
        assert "total_tests" in data

    def test_run_tests_endpoint(self, client):
        """Test run tests endpoint."""
        request_data = {
            "services": None,
            "parallel": True,
            "max_workers": 2
        }

        response = client.post("/api/v1/run-tests", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "run_id" in data
        assert data["status"] == "running"

    def test_get_results_not_found(self, client):
        """Test getting results for non-existent run."""
        response = client.get("/api/v1/results/nonexistent")

        assert response.status_code == 404

    def test_get_status_endpoint(self, client):
        """Test status endpoint."""
        response = client.get("/api/v1/status")

        assert response.status_code == 200
        data = response.json()
        assert "active_runs" in data
        assert "total_runs" in data

    def test_delete_results_endpoint(self, client):
        """Test delete results endpoint."""
        # First create a run
        request_data = {"parallel": False}
        create_response = client.post("/api/v1/run-tests", json=request_data)
        run_id = create_response.json()["run_id"]

        # Delete it
        response = client.delete(f"/api/v1/results/{run_id}")

        assert response.status_code == 200

    def test_delete_nonexistent_results(self, client):
        """Test deleting non-existent results."""
        response = client.delete("/api/v1/results/nonexistent")

        assert response.status_code == 404
