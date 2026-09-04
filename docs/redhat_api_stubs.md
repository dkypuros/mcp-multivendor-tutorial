# The Red Hat API Tools: What's Live, What's a Fixture, and How the Fixture Tracks the Official API

Example 04 ([`examples/04_redhat_api_mcp_server/server.py`](../examples/04_redhat_api_mcp_server/server.py))
wraps three of Red Hat's published APIs as MCP tools. This page documents exactly how each tool
relates to the official API — which calls are live against production endpoints, which are
fixtures, and field by field, where the fixture's shape comes from. Every response carries an
`emulated` marker, so the distinction travels inside the data itself.

## Why this server exists

Agentic access to vendor knowledge doesn't require a conversational product with a headless
mode — it requires the structured APIs underneath, and Red Hat publishes those in the
[API catalog](https://developers.redhat.com/api-catalog). An agent asking "is this CVE relevant
to my platform?" or "has anyone seen this fault before?" is better served by typed JSON from
the source-of-truth API than by a chat transcript.

## Tool 1: `rh_cve_lookup` — live

| | |
|---|---|
| Official API | [Red Hat Security Data API](https://docs.redhat.com/en/documentation/red_hat_security_data_api/) |
| Endpoint | `GET https://access.redhat.com/hydra/rest/securitydata/cve/{CVE}.json` |
| Auth | None — public |
| Status in this tutorial | **Live.** Every call fetches production data |

The tool trims the (large) official response to the agent-relevant core: `threat_severity`,
`public_date`, CVSSv3 score, the Bugzilla description, affected releases with advisories, and
the vendor statement. All field values pass through unmodified from the API.

## Tool 2: `rh_product_lifecycle` — live

| | |
|---|---|
| Official API | [Product Life Cycle API](https://access.redhat.com/product-life-cycles) |
| Endpoint | `GET https://access.redhat.com/product-life-cycles/api/v1/products?name={product}` |
| Auth | None — public |
| Status in this tutorial | **Live.** Every call fetches production data |

Returns each version's current phase and its phase dates (general availability, maintenance,
extended life…) exactly as published.

## Tool 3: `rh_case_search` — live with credentials, accurate fixture without

| | |
|---|---|
| Official API | [Case Management API](https://developers.redhat.com/api-catalog/api/case-management) |
| Endpoint | `POST https://api.access.redhat.com/support/v1/cases/filter` |
| Auth | OAuth2 client credentials — a [Red Hat service account](https://access.redhat.com/articles/3626371) token from `sso.redhat.com` (the same flow as [example 03](../examples/03_red_hat_mcp_client/)) |
| Status in this tutorial | **Live when `RH_SSO_CLIENT_ID`/`RH_SSO_CLIENT_SECRET` are set; labeled fixture otherwise** |

### How the fixture tracks the official API

The endpoint path, HTTP method, and request fields come directly from the
[Customer Portal Integration Guide](https://docs.redhat.com/en/documentation/red_hat_customer_portal/1/html/customer_portal_integration_guide/examples2):

| Element | Source |
|---------|--------|
| `POST /support/v1/cases/filter` for search | Integration Guide, "List Cases" example |
| Request fields `product`, `maxResults` (also documented: `offset`, `startDate`, `endDate`) | Integration Guide filter examples |
| Case fields `product`, `version`, `summary`, `description` | Integration Guide create/update examples — these are the documented case field names |
| Case fields `caseNumber`, `severity`, `status`, `createdDate`, `lastModifiedDate` | Modeled on the case representation shown throughout the [Customer Portal case UI and docs](https://access.redhat.com/articles/2390851); not quoted from a machine-readable schema |

Honest boundaries of the fixture, stated plainly:

- The fixture's **shape** follows the documented API; the response envelope of the live
  `/cases/filter` call may nest cases differently (the tool returns the live payload verbatim
  when credentials are present, so no fixture assumption can distort real data).
- The fixture's **content** (three closed timing-related cases) is invented for the tutorial's
  RCA scenario and is plausible, not historical. It exists so the case-history plane of the
  [RCA pattern](multivendor_rca_pattern.md) can be exercised end to end without credentials.
- Red Hat has announced a [transition to v3 REST and GraphQL case APIs](https://access.redhat.com/articles/7146730);
  the v1 paths documented above remain the ones in the public integration guide. When moving to
  v3, only the `case_search` function body changes — the tool contract and fixture semantics
  hold.

### Switching the fixture off

Create a service account (console.redhat.com → Service Accounts), grant it case visibility, and
set two environment variables on the deployment:

```
RH_SSO_CLIENT_ID=<service-account-client-id>
RH_SSO_CLIENT_SECRET=<service-account-secret>
```

No code changes: the same tool, same contract, `"emulated": false`, production data.

## Feeding the RCA orchestrator

Behind the tutorial's [MCP gateway](kuadrant_authorino_mcp_gateway.md), these tools slot into
the gateway's routing policy as a backend with a `rh_*` tool glob, added to the orchestrator's
authorized scope. The vendor-knowledge plane of the
[evidence chain](multivendor_rca_pattern.md) then answers with a mix the response labels
honestly: live CVE and lifecycle data, and case history that is either live or a declared
fixture.
