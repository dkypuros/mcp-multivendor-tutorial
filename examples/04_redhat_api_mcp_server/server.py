#!/usr/bin/env python3
"""MCP server exposing Red Hat's published APIs as agent tools.

Three tools, three levels of liveness — each response says which it is:

  rh_cve_lookup         REAL   Red Hat Security Data API (public, no auth)
  rh_product_lifecycle  REAL   Product Life Cycle API (public, no auth)
  rh_case_search        REAL when RH_SSO_CLIENT_ID/RH_SSO_CLIENT_SECRET are set
                        (OAuth2 client credentials against sso.redhat.com, then
                        POST /support/v1/cases/filter);
                        otherwise an accurate FIXTURE labeled "emulated": true,
                        shaped after the official Case Management API
                        (see docs/redhat_api_stubs.md for the field mapping).

Transport: JSON-RPC over HTTP POST /mcp (initialize, tools/list, tools/call),
matching the minimal MCP surface used across this tutorial. Stdlib only.

Environment:
  PORT                    listen port (default 8854)
  RH_SSO_TOKEN_URL        default: the redhat-external realm token endpoint
  RH_SSO_CLIENT_ID        service account client id (optional)
  RH_SSO_CLIENT_SECRET    service account secret (optional)
"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("PORT", "8854"))
SECURITYDATA = "https://access.redhat.com/hydra/rest/securitydata"
LIFECYCLE = "https://access.redhat.com/product-life-cycles/api/v1/products"
CASE_FILTER = "https://api.access.redhat.com/support/v1/cases/filter"
SSO_TOKEN_URL = os.environ.get(
    "RH_SSO_TOKEN_URL",
    "https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token",
)

SERVER_INFO = {"name": "redhat-api", "version": "1.0.0"}


def _get(url, headers=None, data=None, method="GET", timeout=20):
    h = {"User-Agent": "mcp-redhat-api/1.0 (+https://github.com/dkypuros/mcp-multivendor-tutorial)",
         "Accept": "application/json"}
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


# ---------------------------------------------------------------- tools

def cve_lookup(args):
    cve = (args.get("cve") or "").strip().upper()
    if not cve.startswith("CVE-"):
        return {"error": "pass a CVE id like CVE-2024-6387"}
    d = _get(f"{SECURITYDATA}/cve/{cve}.json")
    return {
        "plane": "platform-vendor",
        "emulated": False,
        "source": "Red Hat Security Data API (access.redhat.com/hydra/rest/securitydata)",
        "cve": cve,
        "severity": d.get("threat_severity"),
        "public_date": d.get("public_date"),
        "cvss3_score": (d.get("cvss3") or {}).get("cvss3_base_score"),
        "description": (d.get("bugzilla") or {}).get("description"),
        "affected_releases": [
            {"product": r.get("product_name"), "advisory": r.get("advisory"), "package": r.get("package")}
            for r in (d.get("affected_release") or [])[:8]
        ],
        "statement": (d.get("statement") or "")[:600] or None,
    }


def product_lifecycle(args):
    product = (args.get("product") or "").strip()
    if not product:
        return {"error": "pass a product name, e.g. 'OpenShift Container Platform 4'"}
    d = _get(f"{LIFECYCLE}?name={urllib.parse.quote(product)}")
    out = []
    for p in (d.get("data") or [])[:3]:
        out.append({
            "name": p.get("name"),
            "versions": [
                {"version": v.get("name"), "phase": (v.get("phases") or [{}])[-1].get("name"),
                 "dates": {ph.get("name"): ph.get("date") for ph in (v.get("phases") or [])[:6]}}
                for v in (p.get("versions") or [])[:6]
            ],
        })
    return {
        "plane": "platform-vendor",
        "emulated": False,
        "source": "Red Hat Product Life Cycle API (access.redhat.com/product-life-cycles)",
        "query": product,
        "products": out,
    }


CASE_FIXTURE = [
    # Shape follows the official Case Management API (POST /support/v1/cases/filter);
    # field-by-field mapping documented in docs/redhat_api_stubs.md.
    {"caseNumber": "04102931", "summary": "PTP ptp4l servo FREERUN after NIC firmware update",
     "product": "Red Hat OpenShift Container Platform", "version": "4.16",
     "severity": "2 (High)", "status": "Closed",
     "createdDate": "2025-11-04T09:12:00Z", "lastModifiedDate": "2025-11-18T16:40:00Z",
     "resolution": "NIC firmware rollback restored egress hardware timestamping; vendor advisory referenced."},
    {"caseNumber": "04188457", "summary": "lossOfRealTimeSynchronization alarms on vDU nodes, tx_hwtstamp_timeouts incrementing",
     "product": "Red Hat OpenShift Container Platform", "version": "4.17",
     "severity": "1 (Urgent)", "status": "Closed",
     "createdDate": "2026-01-22T02:47:00Z", "lastModifiedDate": "2026-02-02T11:05:00Z",
     "resolution": "Egress timestamp misses under burst load; mitigated via PTP Operator holdover tuning pending driver fix."},
    {"caseNumber": "04231170", "summary": "Cloud Event Proxy not emitting ptp state-change events after node reboot",
     "product": "Red Hat OpenShift Container Platform", "version": "4.16",
     "severity": "3 (Normal)", "status": "Closed",
     "createdDate": "2026-03-10T14:30:00Z", "lastModifiedDate": "2026-03-14T08:22:00Z",
     "resolution": "linuxptp daemonset restart ordering; fixed in subsequent operator release."},
]


def case_search(args):
    query = (args.get("query") or "").lower()
    client_id = os.environ.get("RH_SSO_CLIENT_ID")
    client_secret = os.environ.get("RH_SSO_CLIENT_SECRET")
    if client_id and client_secret:
        tok = _get(SSO_TOKEN_URL, method="POST",
                   headers={"Content-Type": "application/x-www-form-urlencoded"},
                   data=urllib.parse.urlencode({
                       "grant_type": "client_credentials",
                       "client_id": client_id, "client_secret": client_secret,
                   }).encode())["access_token"]
        body = {"maxResults": 10}
        if args.get("product"):
            body["product"] = args["product"]
        d = _get(CASE_FILTER, method="POST",
                 headers={"Authorization": f"Bearer {tok}",
                          "Content-Type": "application/json"},
                 data=json.dumps(body).encode())
        return {"plane": "platform-vendor", "emulated": False,
                "source": "Red Hat Case Management API (api.access.redhat.com/support/v1/cases/filter)",
                "cases": d}
    hits = [c for c in CASE_FIXTURE if not query
            or query in c["summary"].lower() or query in c["resolution"].lower()]
    return {
        "plane": "platform-vendor",
        "emulated": True,
        "source": "fixture shaped after the Case Management API (POST /support/v1/cases/filter); "
                  "set RH_SSO_CLIENT_ID/RH_SSO_CLIENT_SECRET for live queries",
        "query": query or None,
        "cases": hits,
    }


TOOLS = {
    "rh_cve_lookup": (
        "Look up a CVE in the Red Hat Security Data API (live, public). Args: {cve}",
        {"type": "object", "properties": {"cve": {"type": "string"}}, "required": ["cve"]},
        cve_lookup,
    ),
    "rh_product_lifecycle": (
        "Product life-cycle phases and dates from the Red Hat Product Life Cycle API (live, public). Args: {product}",
        {"type": "object", "properties": {"product": {"type": "string"}}, "required": ["product"]},
        product_lifecycle,
    ),
    "rh_case_search": (
        "Search support case history via the Case Management API (live with service-account "
        "credentials; otherwise an accurate labeled fixture). Args: {query, product}",
        {"type": "object", "properties": {"query": {"type": "string"}, "product": {"type": "string"}}},
        case_search,
    ),
}


# ---------------------------------------------------------------- transport

class Handler(BaseHTTPRequestHandler):
    def _send(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.rstrip("/") in ("", "/healthz"):
            self._send({"status": "ok", "server": SERVER_INFO, "tools": list(TOOLS)})
        else:
            self._send({"error": "not found"}, 404)

    def do_POST(self):
        if self.path.rstrip("/") != "/mcp":
            self._send({"error": "not found"}, 404)
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            req = json.loads(self.rfile.read(length).decode())
        except json.JSONDecodeError:
            self._send({"jsonrpc": "2.0", "id": None,
                        "error": {"code": -32700, "message": "parse error"}})
            return
        rid, method, params = req.get("id"), req.get("method"), req.get("params") or {}
        if method == "initialize":
            result = {"protocolVersion": "2024-11-05", "serverInfo": SERVER_INFO,
                      "capabilities": {"tools": {}}}
        elif method == "tools/list":
            result = {"tools": [
                {"name": n, "description": d, "inputSchema": s}
                for n, (d, s, _) in TOOLS.items()]}
        elif method == "tools/call":
            name = params.get("name")
            if name not in TOOLS:
                self._send({"jsonrpc": "2.0", "id": rid,
                            "error": {"code": -32601, "message": f"unknown tool {name}"}})
                return
            try:
                data = TOOLS[name][2](params.get("arguments") or {})
            except urllib.error.HTTPError as exc:
                data = {"error": f"upstream API returned HTTP {exc.code}", "url": exc.url}
            except Exception as exc:
                data = {"error": str(exc)}
            result = {"content": [{"type": "text", "text": json.dumps(data, indent=2)}]}
        else:
            self._send({"jsonrpc": "2.0", "id": rid,
                        "error": {"code": -32601, "message": f"unknown method {method}"}})
            return
        self._send({"jsonrpc": "2.0", "id": rid, "result": result})

    def log_message(self, fmt, *a):  # quiet
        pass


if __name__ == "__main__":
    print(f"redhat-api MCP server on :{PORT} — tools: {', '.join(TOOLS)}")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
