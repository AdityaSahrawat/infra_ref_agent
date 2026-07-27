"""
Kubernetes executor module using the official Kubernetes Python SDK.
Supports both live cluster operations and controlled simulated fallback when no cluster is reachable.
"""

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.services.logger import get_logger
from kubernetes import client
from kubernetes import config

logger = get_logger(__name__)

# Global mock state for offline testing / demo simulation
_MOCK_DEPLOYMENTS: Dict[str, Dict[str, Any]] = {
    "auth-api": {
        "namespace": "default",
        "replicas": 1,
        "available_replicas": 1,
        "restarted_at": None,
        "status": "Running",
    },
    "payment-service": {
        "namespace": "default",
        "replicas": 2,
        "available_replicas": 2,
        "restarted_at": None,
        "status": "Running",
    },
}

_MOCK_PODS: Dict[str, Dict[str, Any]] = {
    "auth-api-7b89f4c5d-x9z1a": {
        "namespace": "default",
        "deployment": "auth-api",
        "status": "Running",
        "restarts": 0,
        "logs": "2026-07-27T08:00:00Z [INFO] Service started\n2026-07-27T08:05:00Z [INFO] Health check HTTP 200 OK",
    },
    "auth-api-7b89f4c5d-w2k8b": {
        "namespace": "default",
        "deployment": "auth-api",
        "status": "Running",
        "restarts": 0,
        "logs": "2026-07-27T08:00:00Z [INFO] Service started\n2026-07-27T08:05:00Z [INFO] Health check HTTP 200 OK",
    },
    "payment-service-5d6e7f8-a1b2c": {
        "namespace": "default",
        "deployment": "payment-service",
        "status": "Running",
        "restarts": 1,
        "logs": "2026-07-27T08:00:00Z [INFO] Payment gateway connected",
    },
}


def _is_live_k8s_available() -> bool:
    """Check if Kubernetes client config can be loaded."""
    if os.getenv("KUBERNETES_FORCE_MOCK", "").lower() in ("1", "true", "yes"):
        return False
    try:
        try:
            config.load_incluster_config()
            return True
        except Exception:
            pass
        try:
            config.load_kube_config()
            return True
        except Exception:
            return False
    except Exception:
        return False


def _get_api_clients():
    """Retrieve CoreV1Api and AppsV1Api clients."""
    return client.CoreV1Api(), client.AppsV1Api()


def restart_deployment(
    deployment: str, namespace: str = "default", **_kwargs: Any
) -> Dict[str, Any]:
    """Restart a Kubernetes deployment by triggering a rollout restart."""
    now_iso = datetime.now(timezone.utc).isoformat()
    if _is_live_k8s_available():
        try:
            _, apps_api = _get_api_clients()
            patch_body = {
                "spec": {
                    "template": {
                        "metadata": {
                            "annotations": {
                                "kubectl.kubernetes.io/restartedAt": now_iso
                            }
                        }
                    }
                }
            }
            apps_api.patch_namespaced_deployment(
                name=deployment, namespace=namespace, body=patch_body
            )
            logger.info("Restarted deployment '%s' in namespace '%s'", deployment, namespace)
            return {
                "success": True,
                "action": "restart_deployment",
                "deployment": deployment,
                "namespace": namespace,
                "restarted_at": now_iso,
                "message": f"Deployment '{deployment}' rollout restart triggered successfully.",
            }
        except Exception as exc:
            logger.exception("Failed to restart deployment '%s'", deployment)
            return {
                "success": False,
                "action": "restart_deployment",
                "deployment": deployment,
                "namespace": namespace,
                "error": str(exc),
            }
    else:
        # Mock implementation
        dep = _MOCK_DEPLOYMENTS.get(deployment)
        if not dep:
            _MOCK_DEPLOYMENTS[deployment] = {
                "namespace": namespace,
                "replicas": 1,
                "available_replicas": 1,
                "restarted_at": now_iso,
                "status": "Running",
            }
        else:
            dep["restarted_at"] = now_iso
            dep["status"] = "Running"

        # Refresh mock pods for deployment
        for pod_name, pod in list(_MOCK_PODS.items()):
            if pod.get("deployment") == deployment:
                pod["restarts"] += 1
                pod["status"] = "Running"

        logger.info("[MOCK] Restarted deployment '%s' in namespace '%s'", deployment, namespace)
        return {
            "success": True,
            "action": "restart_deployment",
            "deployment": deployment,
            "namespace": namespace,
            "restarted_at": now_iso,
            "message": f"[MOCK] Deployment '{deployment}' rollout restart triggered successfully.",
            "mode": "simulated",
        }


def scale_deployment(
    deployment: str, replicas: int, namespace: str = "default", **_kwargs: Any
) -> Dict[str, Any]:
    """Scale a Kubernetes deployment to the specified replica count."""
    if replicas < 0:
        return {
            "success": False,
            "action": "scale_deployment",
            "deployment": deployment,
            "error": "Replicas must be a non-negative integer",
        }

    if _is_live_k8s_available():
        try:
            _, apps_api = _get_api_clients()
            patch_body = {"spec": {"replicas": replicas}}
            apps_api.patch_namespaced_deployment(
                name=deployment, namespace=namespace, body=patch_body
            )
            logger.info("Scaled deployment '%s' to %d replicas", deployment, replicas)
            return {
                "success": True,
                "action": "scale_deployment",
                "deployment": deployment,
                "namespace": namespace,
                "replicas": replicas,
                "message": f"Deployment '{deployment}' scaled to {replicas} replicas.",
            }
        except Exception as exc:
            logger.exception("Failed to scale deployment '%s'", deployment)
            return {
                "success": False,
                "action": "scale_deployment",
                "deployment": deployment,
                "namespace": namespace,
                "error": str(exc),
            }
    else:
        # Mock implementation
        dep = _MOCK_DEPLOYMENTS.get(deployment)
        prev_replicas = dep["replicas"] if dep else 1
        _MOCK_DEPLOYMENTS[deployment] = {
            "namespace": namespace,
            "replicas": replicas,
            "available_replicas": replicas,
            "restarted_at": dep.get("restarted_at") if dep else None,
            "status": "Running",
        }

        # Update or generate mock pods to match scale
        existing_pods = [p for p, data in _MOCK_PODS.items() if data.get("deployment") == deployment]
        if len(existing_pods) < replicas:
            for i in range(len(existing_pods), replicas):
                new_pod_name = f"{deployment}-7b89f4c5d-gen{i+1}"
                _MOCK_PODS[new_pod_name] = {
                    "namespace": namespace,
                    "deployment": deployment,
                    "status": "Running",
                    "restarts": 0,
                    "logs": f"2026-07-27T08:10:00Z [INFO] Scaled pod {new_pod_name} online.",
                }
        elif len(existing_pods) > replicas:
            for pod_name in existing_pods[replicas:]:
                _MOCK_PODS.pop(pod_name, None)

        logger.info(
            "[MOCK] Scaled deployment '%s' from %d to %d replicas",
            deployment,
            prev_replicas,
            replicas,
        )
        return {
            "success": True,
            "action": "scale_deployment",
            "deployment": deployment,
            "namespace": namespace,
            "previous_replicas": prev_replicas,
            "replicas": replicas,
            "message": f"[MOCK] Deployment '{deployment}' scaled from {prev_replicas} to {replicas} replicas.",
            "mode": "simulated",
        }


def delete_pod(
    pod_name: str, namespace: str = "default", **_kwargs: Any
) -> Dict[str, Any]:
    """Delete a specific pod in Kubernetes."""
    if _is_live_k8s_available():
        try:
            core_api, _ = _get_api_clients()
            core_api.delete_namespaced_pod(name=pod_name, namespace=namespace)
            logger.info("Deleted pod '%s' in namespace '%s'", pod_name, namespace)
            return {
                "success": True,
                "action": "delete_pod",
                "pod_name": pod_name,
                "namespace": namespace,
                "message": f"Pod '{pod_name}' deleted successfully.",
            }
        except Exception as exc:
            logger.exception("Failed to delete pod '%s'", pod_name)
            return {
                "success": False,
                "action": "delete_pod",
                "pod_name": pod_name,
                "namespace": namespace,
                "error": str(exc),
            }
    else:
        # Mock implementation
        pod = _MOCK_PODS.pop(pod_name, None)
        if pod:
            deployment = pod.get("deployment")
            # Auto-recreate pod if it belongs to a mock deployment (Simulating ReplicaSet auto-healing)
            if deployment and deployment in _MOCK_DEPLOYMENTS:
                recreated_pod_name = f"{deployment}-7b89f4c5d-auto{len(_MOCK_PODS)+1}"
                _MOCK_PODS[recreated_pod_name] = {
                    "namespace": namespace,
                    "deployment": deployment,
                    "status": "Running",
                    "restarts": 0,
                    "logs": f"2026-07-27T08:15:00Z [INFO] ReplicaSet automatically created replacement pod {recreated_pod_name}.",
                }
                msg = f"[MOCK] Pod '{pod_name}' deleted. ReplicaSet automatically created replacement '{recreated_pod_name}'."
            else:
                msg = f"[MOCK] Pod '{pod_name}' deleted."
        else:
            msg = f"[MOCK] Pod '{pod_name}' deleted or already removed."

        logger.info("[MOCK] Deleted pod '%s'", pod_name)
        return {
            "success": True,
            "action": "delete_pod",
            "pod_name": pod_name,
            "namespace": namespace,
            "message": msg,
            "mode": "simulated",
        }


def get_pod_logs(
    pod_name: str, namespace: str = "default", tail_lines: int = 100, **_kwargs: Any
) -> Dict[str, Any]:
    """Retrieve logs from a specific pod."""
    if _is_live_k8s_available():
        try:
            core_api, _ = _get_api_clients()
            logs = core_api.read_namespaced_pod_log(
                name=pod_name, namespace=namespace, tail_lines=tail_lines
            )
            return {
                "success": True,
                "action": "get_pod_logs",
                "pod_name": pod_name,
                "namespace": namespace,
                "logs": logs,
            }
        except Exception as exc:
            logger.exception("Failed to get logs for pod '%s'", pod_name)
            return {
                "success": False,
                "action": "get_pod_logs",
                "pod_name": pod_name,
                "namespace": namespace,
                "logs": "",
                "error": str(exc),
            }
    else:
        # Mock implementation
        pod = _MOCK_PODS.get(pod_name)
        if pod:
            logs = pod.get("logs", f"Sample log output for {pod_name}")
            return {
                "success": True,
                "action": "get_pod_logs",
                "pod_name": pod_name,
                "namespace": namespace,
                "logs": logs,
                "mode": "simulated",
            }
        else:
            # Check if matching deployment pod prefix
            matching = [data for p, data in _MOCK_PODS.items() if p.startswith(pod_name)]
            if matching:
                return {
                    "success": True,
                    "action": "get_pod_logs",
                    "pod_name": pod_name,
                    "namespace": namespace,
                    "logs": matching[0].get("logs", ""),
                    "mode": "simulated",
                }
            return {
                "success": True,
                "action": "get_pod_logs",
                "pod_name": pod_name,
                "namespace": namespace,
                "logs": f"2026-07-27T08:00:00Z [INFO] Simulated logs for {pod_name}\n2026-07-27T08:01:00Z [WARN] High memory consumption detected",
                "mode": "simulated",
            }


def list_pods(
    namespace: str = "default", label_selector: Optional[str] = None, **_kwargs: Any
) -> Dict[str, Any]:
    """List pods in a namespace."""
    if _is_live_k8s_available():
        try:
            core_api, _ = _get_api_clients()
            kwargs = {"namespace": namespace}
            if label_selector:
                kwargs["label_selector"] = label_selector
            pod_list = core_api.list_namespaced_pod(**kwargs)
            result = []
            for item in pod_list.items:
                result.append(
                    {
                        "name": item.metadata.name,
                        "namespace": item.metadata.namespace,
                        "status": item.status.phase,
                        "node_name": item.spec.node_name,
                        "pod_ip": item.status.pod_ip,
                        "start_time": (
                            item.status.start_time.isoformat()
                            if item.status.start_time
                            else None
                        ),
                    }
                )
            return {
                "success": True,
                "action": "list_pods",
                "namespace": namespace,
                "pods": result,
                "count": len(result),
            }
        except Exception as exc:
            logger.exception("Failed to list pods in namespace '%s'", namespace)
            return {
                "success": False,
                "action": "list_pods",
                "namespace": namespace,
                "pods": [],
                "error": str(exc),
            }
    else:
        # Mock implementation
        pods = []
        for name, data in _MOCK_PODS.items():
            if data["namespace"] == namespace:
                pods.append(
                    {
                        "name": name,
                        "namespace": namespace,
                        "deployment": data.get("deployment"),
                        "status": data.get("status", "Running"),
                        "restarts": data.get("restarts", 0),
                    }
                )
        return {
            "success": True,
            "action": "list_pods",
            "namespace": namespace,
            "pods": pods,
            "count": len(pods),
            "mode": "simulated",
        }


def get_pod_status(
    pod_name: Optional[str] = None,
    deployment: Optional[str] = None,
    namespace: str = "default",
    **_kwargs: Any
) -> Dict[str, Any]:
    """Get pod status details."""
    if _is_live_k8s_available():
        try:
            core_api, _ = _get_api_clients()
            if pod_name:
                pod = core_api.read_namespaced_pod_status(name=pod_name, namespace=namespace)
                return {
                    "success": True,
                    "action": "get_pod_status",
                    "pod_name": pod_name,
                    "status": pod.status.phase,
                    "pod_ip": pod.status.pod_ip,
                    "host_ip": pod.status.host_ip,
                    "container_statuses": [
                        {
                            "name": cs.name,
                            "ready": cs.ready,
                            "restart_count": cs.restart_count,
                            "state": str(cs.state),
                        }
                        for cs in (pod.status.container_statuses or [])
                    ],
                }
            else:
                label_selector = f"app={deployment}" if deployment else None
                return list_pods(namespace=namespace, label_selector=label_selector)
        except Exception as exc:
            logger.exception("Failed to get pod status for '%s'", pod_name or deployment)
            return {
                "success": False,
                "action": "get_pod_status",
                "pod_name": pod_name,
                "error": str(exc),
            }
    else:
        # Mock implementation
        if pod_name:
            if pod_name in _MOCK_PODS:
                pod_info = _MOCK_PODS[pod_name]
                return {
                    "success": True,
                    "action": "get_pod_status",
                    "pod_name": pod_name,
                    "status": pod_info.get("status", "Running"),
                    "restarts": pod_info.get("restarts", 0),
                    "ready": pod_info.get("status") == "Running",
                    "mode": "simulated",
                }
            else:
                return {
                    "success": False,
                    "action": "get_pod_status",
                    "pod_name": pod_name,
                    "error": f"Pod '{pod_name}' not found",
                    "mode": "simulated",
                }
        elif deployment:
            pods = [
                {"name": name, **data}
                for name, data in _MOCK_PODS.items()
                if data.get("deployment") == deployment
            ]
            return {
                "success": True,
                "action": "get_pod_status",
                "deployment": deployment,
                "pods": pods,
                "ready": len(pods) > 0 and all(p.get("status") == "Running" for p in pods),
                "mode": "simulated",
            }
        else:
            return list_pods(namespace=namespace)


def verify_deployment_health(
    deployment: str, namespace: str = "default", **_kwargs: Any
) -> Dict[str, Any]:
    """Verify if all pods in a deployment are in healthy Ready state."""
    if _is_live_k8s_available():
        try:
            _, apps_api = _get_api_clients()
            dep = apps_api.read_namespaced_deployment(name=deployment, namespace=namespace)
            spec_replicas = dep.spec.replicas if (dep.spec and dep.spec.replicas is not None) else 1
            ready_replicas = dep.status.ready_replicas if (dep.status and dep.status.ready_replicas is not None) else 0
            is_healthy = ready_replicas >= spec_replicas
            return {
                "success": True,
                "action": "verify_deployment_health",
                "deployment": deployment,
                "namespace": namespace,
                "spec_replicas": spec_replicas,
                "ready_replicas": ready_replicas,
                "is_healthy": is_healthy,
                "status": "Healthy" if is_healthy else "Degraded",
            }
        except Exception as exc:
            return {
                "success": False,
                "action": "verify_deployment_health",
                "deployment": deployment,
                "is_healthy": False,
                "error": str(exc),
            }
    else:
        dep_info = _MOCK_DEPLOYMENTS.get(deployment, {})
        replicas = dep_info.get("replicas", 1)
        available = dep_info.get("available_replicas", 1)
        is_healthy = available >= replicas
        return {
            "success": True,
            "action": "verify_deployment_health",
            "deployment": deployment,
            "namespace": namespace,
            "spec_replicas": replicas,
            "ready_replicas": available,
            "is_healthy": is_healthy,
            "status": "Healthy" if is_healthy else "Degraded",
            "mode": "simulated",
        }
