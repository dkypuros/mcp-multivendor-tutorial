"""
Red Hat MCP Server Client Example (Python)

Connects to a published Red Hat MCP server from the Red Hat ecosystem catalog
using OAuth2 client credentials for authentication. Discovers tools and
invokes them.

Prerequisites:
  - Red Hat SSO client credentials (see .env.example)
  - Network access to the Red Hat MCP server endpoint
  - Optional: mTLS certificates (see security/generate_certs.sh)

Red Hat MCP servers available at:
  https://catalog.redhat.com (search "MCP server")

  - MCP Server for RHEL
  - MCP Server for Red Hat OpenShift
  - Red Hat Lightspeed MCP Server
  - MCP Server for Red Hat Security Content
  - MCP Server for Red Hat Product Information
"""

import asyncio
import os
import ssl

import httpx
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

load_dotenv()


async def get_oauth2_token() -> str:
    """Obtain an OAuth2 access token using client credentials grant."""
    token_url = os.environ["RH_SSO_TOKEN_URL"]
    client_id = os.environ["RH_SSO_CLIENT_ID"]
    client_secret = os.environ["RH_SSO_CLIENT_SECRET"]

    async with httpx.AsyncClient() as http:
        response = await http.post(
            token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            },
        )
        response.raise_for_status()
        return response.json()["access_token"]


def build_ssl_context() -> ssl.SSLContext | None:
    """Build mTLS SSL context if certificates are configured."""
    ca_cert = os.environ.get("MTLS_CA_CERT")
    client_cert = os.environ.get("MTLS_CLIENT_CERT")
    client_key = os.environ.get("MTLS_CLIENT_KEY")

    if not all([ca_cert, client_cert, client_key]):
        print("mTLS not configured -- connecting without client certificates.")
        return None

    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.load_verify_locations(ca_cert)
    ctx.load_cert_chain(certfile=client_cert, keyfile=client_key)
    print(f"mTLS configured: CA={ca_cert}, cert={client_cert}")
    return ctx


async def main():
    server_url = os.environ["RH_MCP_SERVER_URL"]

    # step 1: authenticate
    print("Authenticating with Red Hat SSO...")
    token = await get_oauth2_token()
    print("Authentication successful.\n")

    # step 2: configure mTLS (optional)
    ssl_ctx = build_ssl_context()

    # step 3: connect to Red Hat MCP server
    headers = {"Authorization": f"Bearer {token}"}

    async with streamablehttp_client(
        url=server_url,
        headers=headers,
        ssl_context=ssl_ctx,
    ) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # step 4: discover tools
            tools = await session.list_tools()
            print(f"Connected to: {server_url}")
            print(f"Available tools ({len(tools.tools)}):")
            for tool in tools.tools:
                print(f"  - {tool.name}")
                print(f"    {tool.description}")
            print()

            # step 5: invoke a tool (adjust tool name based on the server you connect to)
            if tools.tools:
                first_tool = tools.tools[0]
                print(f"Invoking tool: {first_tool.name}")
                print(f"  Input schema: {first_tool.inputSchema}")
                # uncomment and customize for your use case:
                # result = await session.call_tool(first_tool.name, {"query": "openshift networking"})
                # for content in result.content:
                #     print(content.text)


if __name__ == "__main__":
    asyncio.run(main())
