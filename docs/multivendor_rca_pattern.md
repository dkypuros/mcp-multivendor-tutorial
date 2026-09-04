# Multivendor Root Cause Analysis: The Evidence-Chain Pattern

Some faults cannot be diagnosed by any single vendor, because the evidence is scattered across
domains that no one party can see end to end. A timing fault is the canonical example: the RAN
layer sees a cell go unavailable, the platform layer sees a clock offset spike, packet forensics
show a missing sync message, and the true root cause sits in a NIC's hardware timestamping path.
Four views, four owners, one fault.

This document describes a generic pattern for orchestrated, governed root cause analysis across
vendor boundaries, using MCP as the interface to each vendor's evidence.

<img src="diagrams/evidence_chain.svg" alt="Four evidence planes — RAN alerts, platform timing, packet forensics, hardware counters — corroborated by an orchestrating agent that concludes a root cause" width="740" />

## The evidence-plane model

Each participating party exposes its diagnostic capability as an MCP server returning
**structured testimony** — facts from its own domain, never raw access to its systems:

Testimony is **typed JSON, not log prose**, and each answer carries its own fidelity marker
(`"emulated": true` where a surface is synthesized) — the evidence declares what kind of evidence
it is:

| Plane | Owned by | Testimony (actual shapes) |
|-------|----------|---------------------------|
| **Service/RAN** | RAN vendor | `{"signal": "ran_sync_followup_anomaly", "findings": ["RX: Follow_Up of Sync X missing", "GM TX: Follow_Up X never sent", …]}` plus live element state (`{"phase": "Running", "ready": true, "restarts": 0}`) |
| **Platform timing** | Platform vendor | `{"port_state": "FREERUN", "du_port_state": "UNCALIBRATED", "phc_offset_ns": -50000198, "clock_class": 6}` + a CloudEvent (`event.ptp.sync.state-change`) on every transition |
| **Hardware/NIC** | Silicon vendor | `{"signal": "nic_firmware_suspect", "counters": {"tx_hwtstamp_timeouts": 1, "ptp_tx_carryover": 1, "ptp_ts_fifo_overflow": 1}, "delta_ms": 74.4}` |
| **Cluster** | Platform vendor | Managed-cluster conditions — `Available`, `Joined`, `ClockSynced` — the cluster-level echo of the timing chain |

The orchestrator's output is equally typed — an auditable decision object:

```json
{
  "eventType": "RcaConcludedEvent",
  "traceId": "tr-…",
  "trigger": "PTP sync fault (cell unavailable, FREERUN<->LOCKED)",
  "corroboration": "2/3",
  "faultClass": "egress-hw-timestamp-miss",
  "decision": "CONCLUDE"
}
```

Below the corroboration bar the same object carries `"decision": "HOLD — a human signs"` — the
refusal is itself an auditable event, with the evidence array preserved:

```json
"evidence": [
  {"plane": "cluster",  "tool": "cluster_health",     "signals": [],
   "evidence": "managed cluster unavailable"},
  {"plane": "ran",      "tool": "ran_element_status", "signals": [],
   "evidence": "gNB Running; protective RF shutdown (lossOfRealTimeSynchronization)"},
  {"plane": "platform", "tool": "ptp_operator_status","signals": ["ptp_offset_exceeded"],
   "evidence": "ptp4l MASTER, offset excursion during incident"},
  {"plane": "hardware", "tool": "nic_timestamp_counters", "signals": ["nic_firmware_suspect"],
   "evidence": "~74 ms phase jump on dropped Follow_Up"}
]
```

### The audit trail speaks standards

Every step of the pipeline is emitted as a span mapped to a public specification, so the audit
trail reads as a standards document rather than an application log:

| Span | Specification | Typical latency |
|------|---------------|-----------------|
| Fault alarm ingest | O-RAN WG10 / 3GPP TS 28.532 (O1 FM) | ~50 ms |
| Security authorization | 3GPP TS 29.222 (CAPIF) / O-RAN WG11 | ~35 ms |
| Tool execution | O-RAN R1 + Model Context Protocol | ~250 ms |
| Deterministic routing decision | O-RAN WG2 rApp safety/policy | **~0.03 ms** |
| LLM narrative synthesis | OpenAI-compatible inference, traced | ~8 s |
| Audit event emission | TM Forum TMF688 (v4) | ~1.5 ms |

Two latencies carry the governance argument on their own: the *decision* takes 30 microseconds
of deterministic table lookup, while the LLM's 8 seconds buy only a human-readable narrative.
The slow, probabilistic component is demonstrably outside the decision path.

The security properties come from the layers described elsewhere in this tutorial: every
cross-boundary call passes the [MCP gateway](kuadrant_authorino_mcp_gateway.md) (authentication,
rate limiting), and each agent's own tool use is bounded by in-process policy (see the
[three-layer narrative](README.md)).

## The orchestration pipeline

An orchestrating agent walks the planes in sequence, escalating only when the current plane's
testimony points beyond itself:

1. **Trigger** — a service-plane alarm (cell unavailable) starts the investigation.
2. **Platform analysis** — timing telemetry confirms a synchronization disturbance and brackets
   the incident window.
3. **Protocol forensics** — packet-level analysis inside the window identifies *which* message
   in the sync protocol went wrong, and in which direction.
4. **Hardware analysis** — driver/NIC evidence explains *why*: e.g. an egress hardware timestamp
   was never produced, so the follow-up message was sent with a stale origin time.
5. **Conclusion** — the orchestrator emits an auditable RCA event naming the root cause and the
   evidence chain that supports it.

## Governance rules (what makes this production-credible)

- **Corroboration threshold.** The orchestrator only concludes when independent planes agree
  (e.g. at least 2 of 3 corroborating planes). Below the bar, it emits **HOLD — a human signs**.
  An agent that declines to act without proof is a feature, not a failure.
- **Deterministic decision path.** The routing between planes and the conclusion logic are
  deterministic tables. An LLM may *narrate* and *rank* the evidence for human readers — it never
  makes the decision.
- **Mutually blind planes.** Each vendor's server sees only its own domain. No plane can read
  another's testimony; only the orchestrator holds the assembled chain. Vendor knowledge never
  crosses the boundary — only conclusions do.
- **Every hop audited.** Each tool call is authorized (gateway policy + delegated identity, see
  the token-exchange discussion in [`resources/`](resources/README.md)) and the final RCA event
  records the full evidence chain for later review.

## Configuration contract

A plane-agnostic orchestrator needs only endpoint wiring and a threshold — see the
`RCA Orchestrator` section of [`.env.example`](../.env.example):

```
MCP_GATEWAY_URL=            # the policy-enforcing gateway all tool calls pass through
MCP_GATEWAY_API_KEY=        # credential for the gateway AuthPolicy (placeholder only)
RCA_PLANE_RAN_URL=          # MCP server: service/RAN alerts plane
RCA_PLANE_PLATFORM_URL=     # MCP server: platform timing plane
RCA_PLANE_FORENSICS_URL=    # MCP server: protocol forensics plane
RCA_PLANE_HARDWARE_URL=     # MCP server: hardware/NIC plane
RCA_CORROBORATION_MIN=2     # planes that must agree before concluding
```

Roles, not brands: any vendor can occupy any column. The pattern requires only that each party
publish structured testimony over MCP and accept the gateway's authentication — which is the
whole point of using a standard protocol at the boundary.
