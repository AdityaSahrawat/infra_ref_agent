# Autonomous Infrastructure Maintainer (MVP)

## Overview
This project is a **basic autonomous DevOps agent** that monitors system metrics, detects issues, and performs simple maintenance actions automatically.

The goal of the MVP is to prove that **monitor → detect → act** works end-to-end.

---

## What This Does (MVP)
- Collects system metrics (CPU, memory, uptime)
- Detects issues using simple threshold rules
- Executes predefined maintenance actions (e.g., restart a service)
- Logs incidents and actions

---

## What This Does NOT Do 
- No machine learning or prediction
- No complex root-cause analysis
- No self-healing optimization
- No production-grade security

---

## Basic Architecture (MVP)
1. Metrics source (Prometheus / exporters)
2. Rule-based detector
3. Maintenance agent
4. Command executor
5. Logging system

---

## Example Flow
1. CPU usage exceeds threshold
2. Alert is detected
3. Agent decides an action
4. Action is executed
5. Event is logged

---

## Tech Stack (MVP)
- Python
- Prometheus
- Docker / Docker Compose
- Shell commands

---

## How to Run
1. Start Prometheus
2. Run the agent
3. Simulate a failure (high CPU or crash)
4. Observe automatic remediation

---

## Purpose
- Validate autonomous infrastructure maintenance
- Demonstrate end-to-end automation
- Provide a base for future intelligence
