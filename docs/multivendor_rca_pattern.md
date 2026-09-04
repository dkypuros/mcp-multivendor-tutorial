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

| Plane | Owned by | Example testimony |
|-------|----------|-------------------|
| **Service/RAN alerts** | RAN vendor | Cell state (3GPP TS 28.532 alarms, e.g. `lossOfRealTimeSynchronization`), clock-state history (LOCKED ↔ FREERUN oscillation) |
| **Platform timing** | Platform vendor | PTP daemon logs: master offset spike, servo state transitions, timing CloudEvents |
| **Protocol forensics** | RAN vendor | IEEE 1588 packet analysis: Sync/Follow_Up sequence gaps, `preciseOriginTimestamp` mismatches |
| **Hardware** | Silicon/NIC vendor | Kernel and driver evidence: egress hardware-timestamp timeouts, descriptor-level status, error counters incrementing |

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
