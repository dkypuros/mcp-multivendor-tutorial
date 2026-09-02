# Resources

Public references for the patterns used in this tutorial. Each entry notes which part of the
tutorial it supports.

Everything in this tutorial rests on one idea: when an orchestration platform needs product
knowledge from many vendors, each vendor exposes that knowledge as an MCP server, and the
orchestrator reaches all of them the same way — one protocol, many specialized endpoints. That
idea is simple to demo but raises immediate questions the moment it heads toward production. Who
is allowed to call a vendor's MCP server? How does a vendor keep one partner's traffic from
crowding out another's? Where do authentication, rate limiting, and observability live when the
number of MCP servers grows past two or three — in every server, or in one place in front of all
of them?

The industry answer that has emerged is the **MCP gateway**: a policy-enforcing front door,
built on the Kubernetes Gateway API, that centralizes those cross-cutting concerns so the MCP
servers behind it stay focused on their domain knowledge. Red Hat has been one of the most
public voices on this pattern — it ships the underlying open-source projects (Kuadrant,
Authorino, Limitador), productizes them as Connectivity Link, and has published both engineering
deep-dives and official product documentation on running MCP traffic through exactly this kind
of gateway.

The references below are organized to follow that arc. The first group covers the gateway
security pattern itself — start with the Red Hat Developer article if you want the engineering
detail, or the Red Hat blog post if you want the strategic framing first. The second group lists
the upstream open-source projects the pattern is built from, and the third points to Red Hat's
published MCP servers and APIs — the concrete endpoints a multivendor integration would actually
connect to.

## MCP gateway security (Gateway API + Kuadrant)

These three references cover the same architecture described in
[`docs/kuadrant_authorino_mcp_gateway.md`](../kuadrant_authorino_mcp_gateway.md): a Gateway
API gateway with Kuadrant policies (`AuthPolicy`/Authorino, `RateLimitPolicy`/Limitador)
enforcing authentication and rate limiting in front of a fleet of MCP servers.

### [Advanced authentication and authorization for MCP Gateway](https://developers.redhat.com/articles/2025/12/12/advanced-authentication-authorization-mcp-gateway)

**Red Hat Developer · Guilherme Cassolato · December 2025.**
The closest match to this tutorial's gateway pattern — Gateway API + Kuadrant `AuthPolicy`
securing an Envoy-based MCP gateway that aggregates multiple MCP servers. Goes further than this
tutorial in three directions worth knowing for production:

- **Identity-based tool filtering** — cryptographically signed JWT "wristbands"
  (`x-authorized-tools` header) so different users see different tool sets
- **OAuth2 token exchange (RFC 8693)** — converting a broad access token into narrowly scoped
  per-backend tokens, preventing privilege escalation across MCP servers
- **Vault integration** — per-user, per-service credentials for backend MCP servers that don't
  support OAuth2

### [Control your AI agent traffic at scale: MCP gateway for Red Hat OpenShift (technology preview)](https://www.redhat.com/en/blog/control-your-ai-agent-traffic-scale-model-context-protocol-gateway-red-hat-openshift-now-technology-preview)

**Red Hat blog.**
The executive-level framing of the same MCP gateway: server federation behind a single endpoint,
policy and RBAC enforcement, rate limits, and consistent observability for agent traffic on
OpenShift. Useful for a non-implementation audience.

### [Red Hat Connectivity Link 1.4 — MCP gateway documentation](https://docs.redhat.com/en/documentation/red_hat_connectivity_link/1.4/html/mcp_gateway/mcp-gateway-introduction)

**Official product documentation.**
Confirms the MCP gateway is a first-class Connectivity Link 1.4 feature — the productized form of
the Kuadrant-based pattern in this tutorial. This is the reference to follow for a supported
OpenShift deployment.

## Upstream projects

| Project | URL | Used for |
|---------|-----|----------|
| Kuadrant Operator | <https://github.com/Kuadrant/kuadrant-operator> | Policy attachment (`AuthPolicy`, `RateLimitPolicy`) |
| Authorino | <https://github.com/Kuadrant/authorino> | AuthN/AuthZ engine (API key, OIDC) |
| Limitador | <https://github.com/Kuadrant/limitador> | Rate limiting engine |
| Gateway API | <https://gateway-api.sigs.k8s.io/> | `Gateway` / `HTTPRoute` resources |
| Kuadrant docs | <https://docs.kuadrant.io> | Installation and policy guides |

## Red Hat MCP servers and APIs

- [Red Hat API Catalog](https://developers.redhat.com/api-catalog) — the published REST APIs;
  see [`docs/red_hat_mcp_server_landscape.md`](../red_hat_mcp_server_landscape.md)
- [Red Hat Ecosystem Catalog](https://catalog.redhat.com) — search "MCP server" for the published
  containerized MCP servers
