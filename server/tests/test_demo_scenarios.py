"""
Unit tests for Demo Scenarios runner.
"""

from app.services.demo_scenarios import (
    run_all_demo_scenarios,
    run_scenario_1_high_cpu,
    run_scenario_2_pod_recovery,
    run_scenario_3_crash_remediation,
)


def test_scenario_1():
    res = run_scenario_1_high_cpu()
    assert res["status"] == "Success"
    assert res["recommended_tool"] == "scale_deployment"
    assert res["final_replicas"] == 3


def test_scenario_2():
    res = run_scenario_2_pod_recovery()
    assert "Recovery Observed" in res["status"]
    assert res["delete_execution"]["success"] is True


def test_scenario_3():
    res = run_scenario_3_crash_remediation()
    assert "Healthy" in res["status"]
    assert res["restart_execution"]["success"] is True
    assert res["health_verification"]["is_healthy"] is True


def test_run_all():
    summary = run_all_demo_scenarios()
    assert len(summary["scenarios"]) == 3
    assert "completed successfully" in summary["summary"]
