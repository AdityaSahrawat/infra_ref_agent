"""
Unit tests for Kubernetes Executor and Tool Registry.
"""

from app.executor.executor import execute_action_payload, execute_tool
from app.executor.kubernetes import (
    delete_pod,
    get_pod_logs,
    get_pod_status,
    list_pods,
    restart_deployment,
    scale_deployment,
    verify_deployment_health,
)
from app.executor.tools import TOOLS, get_tool, list_tools


def test_tools_registry():
    """Verify tool registry entries."""
    assert "restart_deployment" in TOOLS
    assert "scale_deployment" in TOOLS
    assert "delete_pod" in TOOLS
    assert "get_pod_logs" in TOOLS
    assert "list_pods" in TOOLS
    assert "get_pod_status" in TOOLS
    assert "verify_deployment_health" in TOOLS

    assert get_tool("restart_deployment") == restart_deployment
    assert get_tool("non_existent") is None

    available = list_tools()
    assert "scale_deployment" in available


def test_scale_deployment():
    """Test scale deployment tool."""
    res = scale_deployment("auth-api", replicas=3)
    assert res["success"] is True
    assert res["action"] == "scale_deployment"
    assert res["deployment"] == "auth-api"
    assert res["replicas"] == 3


def test_restart_deployment():
    """Test restart deployment tool."""
    res = restart_deployment("auth-api")
    assert res["success"] is True
    assert res["action"] == "restart_deployment"
    assert res["deployment"] == "auth-api"
    assert "restarted_at" in res


def test_delete_pod():
    """Test delete pod tool."""
    res = delete_pod("auth-api-7b89f4c5d-x9z1a")
    assert res["success"] is True
    assert res["action"] == "delete_pod"
    assert res["pod_name"] == "auth-api-7b89f4c5d-x9z1a"


def test_get_pod_logs():
    """Test get pod logs tool."""
    res = get_pod_logs("auth-api-7b89f4c5d-w2k8b")
    assert res["success"] is True
    assert res["action"] == "get_pod_logs"
    assert "logs" in res


def test_list_pods():
    """Test list pods tool."""
    res = list_pods()
    assert res["success"] is True
    assert res["action"] == "list_pods"
    assert "pods" in res
    assert isinstance(res["pods"], list)


def test_get_pod_status():
    """Test get pod status tool."""
    res = get_pod_status(deployment="auth-api")
    assert res["success"] is True
    assert res["action"] == "get_pod_status"


def test_verify_deployment_health():
    """Test verify deployment health tool."""
    res = verify_deployment_health("auth-api")
    assert res["success"] is True
    assert res["is_healthy"] is True


def test_executor_wrapper():
    """Test executor execute_tool and execute_action_payload."""
    res = execute_tool("scale_deployment", {"deployment": "auth-api", "replicas": 4})
    assert res["success"] is True
    assert res["tool"] == "scale_deployment"
    assert res["result"]["replicas"] == 4

    # Test payload wrapper
    payload = {
        "tool": "restart_deployment",
        "args": {"deployment": "auth-api"},
    }
    payload_res = execute_action_payload(payload)
    assert payload_res["success"] is True
    assert payload_res["tool"] == "restart_deployment"

    # Test invalid tool
    invalid_res = execute_tool("invalid_tool_name", {})
    assert invalid_res["success"] is False
    assert "not registered" in invalid_res["error"]
