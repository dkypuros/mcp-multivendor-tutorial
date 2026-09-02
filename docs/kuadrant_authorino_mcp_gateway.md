# Securing a Multivendor MCP Gateway with Gateway API + Kuadrant

This guide shows how to put a policy-enforcing gateway in front of a set of vendor MCP servers,
using the Kubernetes [Gateway API](https://gateway-api.sigs.k8s.io/) and
[Kuadrant](https://kuadrant.io/) — the open-source project set that Red Hat productizes as
**OpenShift Connectivity Link**. Kuadrant is built from three components:

| Component | Role |
|-----------|------|
| **Gateway API** | Standard Kubernetes API for exposing services (`Gateway`, `HTTPRoute`) |
| **Authorino** | Authentication/authorization enforcement (`AuthPolicy`) |
| **Limitador** | Rate limiting enforcement (`RateLimitPolicy`) |

On OpenShift, these ship as part of **Connectivity Link**, installed via OperatorHub, with the
same `AuthPolicy`/`RateLimitPolicy` custom resources described below. See Red Hat's public docs:
[Connectivity Link documentation](https://docs.redhat.com/en/documentation/red_hat_connectivity_link)
and the upstream projects at [github.com/Kuadrant](https://github.com/Kuadrant).

<img src="diagrams/auth_gateway.svg" alt="Orchestrator connects through a Gateway API gateway enforcing AuthPolicy and RateLimitPolicy to reach Vendor A, B, and C MCP servers" width="740" />

## Why a policy gateway, not per-server auth

In the basic multivendor pattern (see the [root README](../README.md)), the orchestrator talks
directly to each vendor's MCP server. As the number of vendors grows, repeating auth, rate
limiting, and observability logic in every vendor server doesn't scale. A Gateway API gateway
centralizes those cross-cutting concerns in front of the whole fleet of vendor MCP servers,
so each vendor server stays focused on its own domain knowledge.

## 1. Install the Gateway API and a gateway implementation

```bash
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.2.1/standard-install.yaml
```

Any [conformant Gateway API implementation](https://gateway-api.sigs.k8s.io/implementations/)
works. On OpenShift, Connectivity Link's supported gateway is deployed for you as part of the
operator install.

## 2. Install Kuadrant

```bash
helm repo add kuadrant https://kuadrant.io/helm-charts/
helm install kuadrant-operator kuadrant/kuadrant-operator -n kuadrant-system --create-namespace
kubectl apply -f - <<EOF
apiVersion: kuadrant.io/v1beta1
kind: Kuadrant
metadata:
  name: kuadrant
  namespace: kuadrant-system
spec: {}
EOF
```

This brings up Authorino and Limitador automatically. On OpenShift, installing the Connectivity
Link operator from OperatorHub does the equivalent.

## 3. Route to the MCP servers

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: mcp-gateway
  namespace: mcp
spec:
  gatewayClassName: <your-gatewayclass>
  listeners:
  - name: http
    protocol: HTTP
    port: 80
    allowedRoutes:
      namespaces:
        from: Same
---
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: mcp-gateway-route
  namespace: mcp
spec:
  parentRefs:
  - name: mcp-gateway
  rules:
  - backendRefs:
    - name: mcp-gateway-service
      port: 8800
```

On OpenShift, a `Route` typically fronts the Gateway for external access; internally the
`Gateway`/`HTTPRoute` pair is unchanged.

## 4. Require an API key with AuthPolicy

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: orchestrator-api-key
  namespace: kuadrant-system
  labels:
    authorino.kuadrant.io/managed-by: authorino
    kuadrant.io/apikeys-by: mcp-gateway
stringData:
  api_key: <generate-a-real-key>
type: Opaque
---
apiVersion: kuadrant.io/v1
kind: AuthPolicy
metadata:
  name: mcp-gateway-auth
  namespace: mcp
spec:
  targetRef:
    group: gateway.networking.k8s.io
    kind: HTTPRoute
    name: mcp-gateway-route
  rules:
    authentication:
      "api-key-orchestrator":
        apiKey:
          selector:
            matchLabels:
              kuadrant.io/apikeys-by: mcp-gateway
        credentials:
          authorizationHeader:
            prefix: APIKEY
```

Requests without a valid `Authorization: APIKEY <key>` header are rejected with `401` before they
reach any vendor MCP server. For production, prefer OAuth2/OIDC authentication (Authorino
supports it natively) over static API keys — see the
[Authorino documentation](https://github.com/Kuadrant/authorino) for the `identity.oidc` field.

> **Note:** the `AuthConfig` Authorino generates from an `AuthPolicy` is created in the same
> namespace as the Kuadrant install (e.g. `kuadrant-system`) unless the Authorino instance is
> configured cluster-wide. API-key `Secret`s referenced by `selector.matchLabels` must live in
> that same namespace, not the application namespace, unless `allNamespaces: true` is set.

## 5. Add rate limiting with RateLimitPolicy

```yaml
apiVersion: kuadrant.io/v1
kind: RateLimitPolicy
metadata:
  name: mcp-gateway-limits
  namespace: mcp
spec:
  targetRef:
    group: gateway.networking.k8s.io
    kind: HTTPRoute
    name: mcp-gateway-route
  limits:
    orchestrator-limit:
      rates:
      - limit: 100
        window: 1m
```

## Mapping to production concerns

| Concern | Mechanism here | OpenShift/Connectivity Link equivalent |
|---------|----------------|------------------------------------------|
| AuthN/AuthZ | Authorino `AuthPolicy` (API key or OIDC) | Same CRD, via Connectivity Link |
| Rate limiting | Limitador `RateLimitPolicy` | Same CRD, via Connectivity Link |
| External exposure | Gateway API `Gateway`/`HTTPRoute` | `Route` in front of the same Gateway |
| Zero-trust / mTLS | Gateway API `BackendTLSPolicy` | Same, plus OpenShift service mesh integration |
| Per-vendor knowledge isolation | Separate MCP server per vendor, single Gateway | Same pattern |

## Further reading

- [Advanced authentication and authorization for MCP Gateway](https://developers.redhat.com/articles/2025/12/12/advanced-authentication-authorization-mcp-gateway)
  — Red Hat Developer article on this same pattern, extended with identity-based tool filtering,
  OAuth2 token exchange, and Vault integration
- [Connectivity Link 1.4 MCP gateway docs](https://docs.redhat.com/en/documentation/red_hat_connectivity_link/1.4/html/mcp_gateway/mcp-gateway-introduction)
- [Kuadrant documentation](https://docs.kuadrant.io)
- [Kuadrant Operator (GitHub)](https://github.com/Kuadrant/kuadrant-operator)
- [Authorino (GitHub)](https://github.com/Kuadrant/authorino)
- [Limitador (GitHub)](https://github.com/Kuadrant/limitador)
- [Gateway API](https://gateway-api.sigs.k8s.io/)
- More in [`docs/resources/`](resources/README.md)
