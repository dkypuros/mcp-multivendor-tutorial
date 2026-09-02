# Security Setup: mTLS and OAuth2

This guide walks through the security layers used to protect MCP connections
between an orchestrator (MCP client) and a vendor knowledge agent (MCP server)
in a multivendor environment.

## Architecture

```
+-------------------+          mTLS + OAuth2          +-------------------+
|   MCP Client      | -----------------------------> |   MCP Server      |
|   (Orchestrator)  |                                 |   (Vendor Agent)  |
|                   |  Client cert (per-partner)      |                   |
|                   |  Bearer token (OAuth2)           |                   |
|                   |  IP allowlist (optional)         |                   |
+-------------------+                                 +-------------------+
```

Two independent security layers:

1. **mTLS (mutual TLS)** -- transport-level identity. Both client and server
   present certificates signed by a shared CA chain. This proves the client
   is an authorized partner before any application data is exchanged.

2. **OAuth2 client credentials** -- application-level authorization. The client
   obtains a short-lived access token from the vendor's SSO and includes it as
   a Bearer token on every MCP request.

A third optional layer is **IP allowlisting** or VPN tunnel, restricting which
source IPs can reach the MCP server endpoint.

## 1. mTLS Certificate Chain

### Generate test certificates

```bash
chmod +x generate_certs.sh
./generate_certs.sh
```

This creates a three-tier PKI chain in `../certs/`:

```
Root CA
  └── Intermediate CA
        ├── Server certificate  (CN=mcp-server.example.com)
        └── Client certificate  (OU=partner-name, CN=mcp-client.partner.com)
```

### What each file does

| File | Who holds it | Purpose |
|------|-------------|---------|
| `root_ca.crt` | Both sides | Trust anchor. Never leaves your PKI infra. |
| `intermediate_ca.crt` | Both sides | Signs server and client certs. Allows root key to stay offline. |
| `ca.crt` | Both sides | CA bundle (intermediate + root). Used for verification. |
| `server.crt` + `server.key` | MCP server | Server identity. Includes SAN for `localhost` and the server hostname. |
| `client.crt` + `client.key` | MCP client | Client (partner) identity. OU field identifies the partner. |

### Per-partner onboarding

In production, onboarding a new partner means:
1. Generate a new client cert with a unique OU (partner name)
2. Sign it with the intermediate CA
3. Deliver the client cert + key to the partner via secure channel
4. The same MCP server image serves all partners (no custom code)

## 2. OAuth2 Client Credentials Flow

### How it works

```
MCP Client                     SSO Server                    MCP Server
    |                              |                              |
    |-- POST /token -------------->|                              |
    |   grant_type=client_creds    |                              |
    |   client_id=xxx              |                              |
    |   client_secret=xxx          |                              |
    |                              |                              |
    |<-- access_token -------------|                              |
    |                              |                              |
    |-- MCP request (Bearer token) --------------------------->  |
    |                              |                              |
    |<-- MCP response ------------------------------------------ |
```

### Configuration

Set these in your `.env`:

```
RH_SSO_TOKEN_URL=https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token
RH_SSO_CLIENT_ID=your-client-id
RH_SSO_CLIENT_SECRET=your-client-secret
```

### Token lifecycle

- Tokens are short-lived (typically 5-15 minutes)
- The client should refresh before expiry
- No refresh token is issued for client credentials grants; request a new token

## 3. IP Allowlisting (Optional)

If the MCP server is behind a firewall or reverse proxy, configure allowlisted
source IPs:

```
# In .env (optional)
ALLOWED_CLIENT_IPS=10.0.0.0/8,192.168.1.0/24
```

In a production deployment with a reverse proxy (e.g., Caddy, Envoy, HAProxy),
configure the allowlist at the proxy layer before traffic reaches the MCP server.

## 4. Defense in Depth Summary

| Layer | Mechanism | What it proves |
|-------|-----------|---------------|
| Transport | mTLS (PKI cert chain) | Client is a registered partner; server is the real vendor |
| Application | OAuth2 Bearer token | Client is authorized for this session |
| Network | IP allowlist / VPN | Client is connecting from an approved network |
| Data | Query-only boundary | No vendor proprietary data leaves the server; only answers cross |

## Production vs Tutorial

| Aspect | This tutorial | Production |
|--------|--------------|------------|
| CA | Self-signed, local | Organizational PKI or public CA |
| Key storage | Filesystem | HSM, Vault, or K8s secrets |
| Token rotation | Manual | Automated (SDK or sidecar) |
| IP allowlist | Optional | Required |
| Cert revocation | Not implemented | CRL or OCSP |
