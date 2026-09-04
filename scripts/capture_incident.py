#!/usr/bin/env python3
"""Capture one timing incident, end to end, as a timeline dataset.

Runs the eight-step sequence documented in docs/timestamp_path.md against any
conforming endpoints and writes one JSON record per step (JSONL). Endpoints are
taken from the environment (see .env.example):

    RCA_PLANE_PLATFORM_URL   timing bridge exposing /ptp, /ptp/inject, /ptp/heal,
                             /ptp/cloud-events
    RCA_ORCHESTRATOR_URL     orchestrator exposing /nep/ptp/sync and /nep/rca/trigger
                             (path prefix configurable via RCA_ORCH_PREFIX)

Usage:
    python3 scripts/capture_incident.py [output.jsonl]

The output is the same shape as docs/data/incident_capture.jsonl.
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

PLATFORM = os.environ.get("RCA_PLANE_PLATFORM_URL", "http://localhost:7091").rstrip("/")
ORCH = os.environ.get("RCA_ORCHESTRATOR_URL", "http://localhost:7095").rstrip("/")
PREFIX = os.environ.get("RCA_ORCH_PREFIX", "/nep")


def call(method: str, url: str):
    req = urllib.request.Request(
        url,
        data=b"{}" if method == "POST" else None,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode()
    except Exception as exc:  # capture the failure as data, don't crash the run
        return {"error": str(exc)}
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {"raw": body[:2000]}


STEPS = [
    ("nominal", "GET", f"{PLATFORM}/ptp"),
    ("inject", "POST", f"{PLATFORM}/ptp/inject"),
    ("faulted", "GET", f"{PLATFORM}/ptp"),
    ("cloud-events", "GET", f"{PLATFORM}/ptp/cloud-events"),
    ("orchestrator-view", "GET", f"{ORCH}{PREFIX}/ptp/sync"),
    ("rca-decision", "POST", f"{ORCH}{PREFIX}/rca/trigger"),
    ("heal", "POST", f"{PLATFORM}/ptp/heal"),
    ("restored", "GET", f"{PLATFORM}/ptp"),
]


def main() -> None:
    out_path = sys.argv[1] if len(sys.argv) > 1 else "incident_capture.jsonl"
    with open(out_path, "w") as f:
        for step, method, url in STEPS:
            record = {
                "t": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                "step": step,
                "source": url,
                "data": call(method, url),
            }
            f.write(json.dumps(record) + "\n")
            print(f"{record['t']}  {step}")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
