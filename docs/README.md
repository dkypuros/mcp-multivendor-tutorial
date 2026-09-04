# Documentation

This folder holds the deeper material behind the tutorial — the security architecture, the
vendor landscape, and the reference list. This page explains the narrative that connects it.

## The story so far

The tutorial begins, in the [root README](../README.md) and `examples/`, with the basic
multivendor pattern: every vendor exposes its product knowledge as an MCP server, and an
orchestration platform reaches all of them the same way. Each connection is secured on its own —
mTLS for transport identity, OAuth2 client credentials for application authorization (see
[`security/README.md`](../security/README.md)). That works, and it is exactly how a first
integration with a single vendor should look.

But the moment there are more than a few MCP servers, per-connection security stops scaling, and
the question changes from *"how do I secure this connection?"* to *"where should enforcement
live?"* The answer that has emerged across the industry is: **at more than one point, each
catching what the others cannot see.**

### Layer 1 — the gateway (network boundary)

The first enforcement point is a policy-enforcing gateway in front of the whole fleet of MCP
servers, built on the Kubernetes Gateway API with Kuadrant — the open-source project set behind
Red Hat OpenShift Connectivity Link.
[`kuadrant_authorino_mcp_gateway.md`](kuadrant_authorino_mcp_gateway.md) walks through it: a
`Gateway` and `HTTPRoute` front the MCP servers, an `AuthPolicy` (enforced by Authorino) requires
credentials on every request, and a `RateLimitPolicy` (enforced by Limitador) protects the
backends. The effect is simple to describe: a request without credentials is rejected at the
gateway with `401` and never reaches any MCP server; a request with valid credentials passes
through untouched. Authentication, rate limiting, and observability live in one place instead of
being reimplemented inside every vendor server.

The gateway is powerful precisely because it sits outside the agent — it enforces regardless of
how the agent behaves. But that position is also its limit: **it can only see traffic that
crosses it.**

### Layer 2 — the sandbox (runtime boundary)

The second enforcement point is the agent's runtime environment: pod-level isolation,
deny-by-default egress, and cryptographic workload identity, so that a compromised agent cannot
reach the host or other agents' data. This layer is described publicly in Red Hat and NVIDIA's
work on secure agentic infrastructure (see the [resources page](resources/README.md)). It
isolates — but it does not adjudicate individual tool calls.

### Layer 3 — the in-process policy engine

The third enforcement point sits inside the agent itself. When an agent invokes a tool —
`file.read`, `code.execute`, `network.fetch` — that call may never cross the gateway and is
invisible to it. An embedded policy engine evaluates every tool invocation against policies
stored as Kubernetes custom resources (`AgentPolicy` CRDs), deciding ALLOW or DENY in
microseconds before the tool runs. Policies declare which agent types may use which tools, under
what constraints (path patterns, allowed domains, ports), with deny by default. The pattern is
SELinux applied to agents: the same mandatory-access-control idea, with agent types in place of
process contexts and tools in place of object classes. A reference implementation is
[kuberenetes-agentic-policy-engine](https://github.com/dkypuros/kuberenetes-agentic-policy-engine).

### The layers working together

The narrative lands in one request path. An orchestrator's call approaches the gateway: without
credentials it stops there — `401`, layer 1, nothing behind the gateway is ever touched. With
valid credentials the request passes the gateway and reaches the agent's policy engine, where
the CRD-defined policy has the final word: a permitted tool proceeds (`200`, allowed), a
forbidden one is refused (`403`, denied by policy) even though the caller was fully
authenticated. Authentication at the boundary, authorization at the point of action — each layer
catching exactly what the others cannot see.

## What's in this folder

| Document | What it covers |
|----------|----------------|
| [`kuadrant_authorino_mcp_gateway.md`](kuadrant_authorino_mcp_gateway.md) | Layer 1 in full: Gateway API + Kuadrant installation, `AuthPolicy`, `RateLimitPolicy`, and the OpenShift/Connectivity Link mapping |
| [`multivendor_rca_pattern.md`](multivendor_rca_pattern.md) | What the layers exist *for*: orchestrated, governed root cause analysis across vendor evidence planes |
| [`timing_fault_explained.md`](timing_fault_explained.md) | The timing fault end to end — PTP, Follow_Up messages, LOCKED/FREERUN, and why the evidence spans four organizations |
| [`timestamp_path.md`](timestamp_path.md) | The machinery the fault travels through: nine components from Grandmaster to orchestrator, normal and incident branches, with captured data from both |
| [`fact_packet_schema.md`](fact_packet_schema.md) | The testimony envelope and decision object, mapped to the TM Forum standards (IG1453, GB1087, IG1253, TMF688) they implement |
| [`red_hat_mcp_server_landscape.md`](red_hat_mcp_server_landscape.md) | The vendor side: Red Hat's published MCP servers and API catalog — the concrete endpoints a multivendor integration connects to |
| [`resources/`](resources/README.md) | Annotated public references: Red Hat's MCP gateway articles and docs, the upstream projects, and the catalogs |
| `diagrams/` | The SVG architecture diagrams used across the tutorial |
