"""
Comprehensive Backend API Tests for QA Automation Platform
Tests: Health, Flows, Runs, Secrets, Reports endpoints
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://9750af0c-7d6a-4e8d-bcd5-e8391389a9da.preview.emergentagent.com/api')


class TestHealth:
    """Health check endpoint tests"""
    
    def test_health_check_returns_healthy_status(self):
        """Test /api/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert "timestamp" in data
        assert "services" in data
        
        # Validate services
        services = data["services"]
        assert "api" in services
        assert "database" in services
        assert services["api"]["status"] == "healthy"
        assert services["database"]["status"] == "healthy"
        print(f"Health check passed: {data['status']}")


class TestFlows:
    """Test flow templates CRUD operations"""
    
    def test_list_flows_returns_available_templates(self):
        """Test GET /api/flows returns available test flows"""
        response = requests.get(f"{BASE_URL}/flows")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return a list
        assert isinstance(data, list)
        assert len(data) >= 1  # At least one flow should exist
        
        # Validate flow structure
        for flow in data:
            assert "id" in flow
            assert "name" in flow
            assert "category" in flow
            assert "description" in flow
        
        print(f"Found {len(data)} flow templates")
    
    def test_get_flow_detail_by_id(self):
        """Test GET /api/flows/{flow_id} returns flow with steps"""
        # First, get list to find a valid flow_id
        list_response = requests.get(f"{BASE_URL}/flows")
        assert list_response.status_code == 200
        flows = list_response.json()
        assert len(flows) > 0
        
        flow_id = flows[0]["id"]
        
        # Get flow detail
        response = requests.get(f"{BASE_URL}/flows/{flow_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate detailed flow structure
        assert data["id"] == flow_id
        assert "name" in data
        assert "steps" in data
        assert isinstance(data["steps"], list)
        
        print(f"Flow '{flow_id}' has {len(data['steps'])} steps")
    
    def test_get_nonexistent_flow_returns_404(self):
        """Test GET /api/flows/{flow_id} returns 404 for non-existent flow"""
        response = requests.get(f"{BASE_URL}/flows/nonexistent_flow_12345")
        
        assert response.status_code == 404
        print("Correctly returned 404 for non-existent flow")


class TestRuns:
    """Test run CRUD and execution operations"""
    
    def test_list_runs_returns_test_runs(self):
        """Test GET /api/runs returns test runs list"""
        response = requests.get(f"{BASE_URL}/runs")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "runs" in data
        assert "total" in data
        assert isinstance(data["runs"], list)
        
        print(f"Found {data['total']} total test runs")
    
    def test_start_test_run_with_flow_id(self):
        """Test POST /api/runs starts a test run"""
        # Get a valid flow_id first
        flows_response = requests.get(f"{BASE_URL}/flows")
        assert flows_response.status_code == 200
        flows = flows_response.json()
        assert len(flows) > 0
        
        flow_id = flows[0]["id"]
        
        # Start a test run
        payload = {
            "flow_id": flow_id,
            "variables": {
                "service_location": "TEST_Location_" + uuid.uuid4().hex[:8]
            }
        }
        
        response = requests.post(f"{BASE_URL}/runs", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response
        assert "run_id" in data
        assert "status" in data
        assert data["status"] == "started"
        assert data["flow_id"] == flow_id
        
        run_id = data["run_id"]
        print(f"Started test run: {run_id}")
        
        return run_id
    
    def test_start_run_without_flow_id_returns_400(self):
        """Test POST /api/runs without flow_id or natural_language_input returns 400"""
        payload = {
            "variables": {}
        }
        
        response = requests.post(f"{BASE_URL}/runs", json=payload)
        
        assert response.status_code == 400
        print("Correctly returned 400 for missing flow_id")
    
    def test_get_run_status(self):
        """Test GET /api/runs/{run_id}/status returns run status"""
        # First create a run
        flows_response = requests.get(f"{BASE_URL}/flows")
        flows = flows_response.json()
        flow_id = flows[0]["id"]
        
        create_response = requests.post(f"{BASE_URL}/runs", json={
            "flow_id": flow_id,
            "variables": {"service_location": "TEST_Status_Check"}
        })
        assert create_response.status_code == 200
        run_id = create_response.json()["run_id"]
        
        # Get status
        response = requests.get(f"{BASE_URL}/runs/{run_id}/status")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate status response
        assert data["run_id"] == run_id
        assert "status" in data
        assert data["status"] in ["pending", "running", "passed", "failed", "cancelled"]
        
        print(f"Run {run_id} status: {data['status']}")
    
    def test_get_nonexistent_run_status_returns_404(self):
        """Test GET /api/runs/{run_id}/status returns 404 for non-existent run"""
        response = requests.get(f"{BASE_URL}/runs/nonexistent_run_12345/status")
        
        assert response.status_code == 404
        print("Correctly returned 404 for non-existent run")
    
    def test_cancel_run(self):
        """Test POST /api/runs/{run_id}/cancel cancels a running test"""
        # First create a run
        flows_response = requests.get(f"{BASE_URL}/flows")
        flows = flows_response.json()
        flow_id = flows[0]["id"]
        
        create_response = requests.post(f"{BASE_URL}/runs", json={
            "flow_id": flow_id,
            "variables": {"service_location": "TEST_Cancel_Test"}
        })
        assert create_response.status_code == 200
        run_id = create_response.json()["run_id"]
        
        # Give it a moment to be in pending/running state
        import time
        time.sleep(0.5)
        
        # Check if cancellable
        status_response = requests.get(f"{BASE_URL}/runs/{run_id}/status")
        current_status = status_response.json()["status"]
        
        if current_status in ["pending", "running"]:
            # Cancel the run
            response = requests.post(f"{BASE_URL}/runs/{run_id}/cancel")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["run_id"] == run_id
            assert data["status"] == "cancelled"
            print(f"Successfully cancelled run {run_id}")
        else:
            print(f"Run already completed with status: {current_status}, skipping cancel test")
    
    def test_cancel_nonexistent_run_returns_404(self):
        """Test POST /api/runs/{run_id}/cancel returns 404 for non-existent run"""
        response = requests.post(f"{BASE_URL}/runs/nonexistent_run_12345/cancel")
        
        assert response.status_code == 404
        print("Correctly returned 404 for cancelling non-existent run")


class TestSecrets:
    """Test secrets (test environments) CRUD operations"""
    
    def test_create_and_list_secret(self):
        """Test secrets CRUD - create, list, get, delete"""
        # Create a test secret
        test_env_name = f"TEST_env_{uuid.uuid4().hex[:8]}"
        create_payload = {
            "test_env": test_env_name,
            "release_branch": "main",
            "url": "https://test.example.com",
            "username": "test_user",
            "password": "test_pass"
        }
        
        create_response = requests.post(f"{BASE_URL}/secrets", json=create_payload)
        
        assert create_response.status_code == 200
        created = create_response.json()
        
        assert "env_id" in created
        assert created["test_env"] == test_env_name
        env_id = created["env_id"]
        print(f"Created secret with env_id: {env_id}")
        
        # List secrets
        list_response = requests.get(f"{BASE_URL}/secrets")
        assert list_response.status_code == 200
        secrets = list_response.json()
        assert isinstance(secrets, list)
        
        # Find our created secret
        found = False
        for secret in secrets:
            if secret["env_id"] == env_id:
                found = True
                break
        assert found, f"Created secret {env_id} not found in list"
        print(f"Verified secret {env_id} in list")
        
        # Get specific secret
        get_response = requests.get(f"{BASE_URL}/secrets/{env_id}")
        assert get_response.status_code == 200
        retrieved = get_response.json()
        assert retrieved["test_env"] == test_env_name
        print(f"Retrieved secret: {retrieved['test_env']}")
        
        # Delete the secret
        delete_response = requests.delete(f"{BASE_URL}/secrets/{env_id}")
        assert delete_response.status_code == 200
        print(f"Deleted secret: {env_id}")
        
        # Verify deletion
        verify_response = requests.get(f"{BASE_URL}/secrets/{env_id}")
        assert verify_response.status_code == 404
        print("Verified secret deletion (404)")
    
    def test_get_nonexistent_secret_returns_404(self):
        """Test GET /api/secrets/{env_id} returns 404 for non-existent secret"""
        response = requests.get(f"{BASE_URL}/secrets/nonexistent_secret_12345")
        
        assert response.status_code == 404
        print("Correctly returned 404 for non-existent secret")
    
    def test_delete_nonexistent_secret_returns_404(self):
        """Test DELETE /api/secrets/{env_id} returns 404 for non-existent secret"""
        response = requests.delete(f"{BASE_URL}/secrets/nonexistent_secret_12345")
        
        assert response.status_code == 404
        print("Correctly returned 404 for deleting non-existent secret")


class TestReports:
    """Test reporting endpoints"""
    
    def test_get_reports_summary(self):
        """Test GET /api/reports/summary returns statistics"""
        response = requests.get(f"{BASE_URL}/reports/summary?days=7")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "period_days" in data
        assert "overall" in data
        assert "flows" in data
        
        overall = data["overall"]
        assert "total_runs" in overall
        assert "passed" in overall
        assert "failed" in overall
        assert "pass_rate" in overall
        
        print(f"Reports summary: {overall['total_runs']} total runs, {overall['pass_rate']}% pass rate")
    
    def test_get_run_history(self):
        """Test GET /api/reports/runs returns paginated run history"""
        response = requests.get(f"{BASE_URL}/reports/runs?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "total" in data
        assert "runs" in data
        assert isinstance(data["runs"], list)
        
        print(f"Run history: {data['total']} total runs, showing {len(data['runs'])}")


class TestNaturalLanguageRun:
    """Test natural language test execution"""
    
    def test_start_run_with_natural_language(self):
        """Test POST /api/runs with natural_language_input"""
        payload = {
            "natural_language_input": "run login customer selection flow",
            "variables": {
                "url": "https://test.example.com",
                "username": "test",
                "password": "test"
            }
        }
        
        response = requests.post(f"{BASE_URL}/runs", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "run_id" in data
        assert "status" in data
        assert data["status"] == "started"
        
        print(f"Started NL run: {data['run_id']} with flow: {data.get('flow_id', 'auto-detected')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
