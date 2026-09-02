/**
 * Red Hat MCP Server Client Example (TypeScript)
 *
 * Connects to a published Red Hat MCP server from the Red Hat ecosystem catalog
 * using OAuth2 client credentials for authentication. Discovers tools and
 * invokes them.
 *
 * Prerequisites:
 *   - Red Hat SSO client credentials (see .env.example)
 *   - Network access to the Red Hat MCP server endpoint
 *   - Optional: mTLS certificates (see security/generate_certs.sh)
 *
 * Red Hat MCP servers available at:
 *   https://catalog.redhat.com (search "MCP server")
 */

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import { config } from "dotenv";
import * as fs from "fs";
import * as https from "https";

config();

async function getOAuth2Token(): Promise<string> {
  const tokenUrl = process.env.RH_SSO_TOKEN_URL!;
  const clientId = process.env.RH_SSO_CLIENT_ID!;
  const clientSecret = process.env.RH_SSO_CLIENT_SECRET!;

  const body = new URLSearchParams({
    grant_type: "client_credentials",
    client_id: clientId,
    client_secret: clientSecret,
  });

  const response = await fetch(tokenUrl, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: body.toString(),
  });

  if (!response.ok) {
    throw new Error(`OAuth2 token request failed: ${response.status} ${response.statusText}`);
  }

  const data = (await response.json()) as { access_token: string };
  return data.access_token;
}

function buildTlsOptions(): https.AgentOptions | undefined {
  const caCert = process.env.MTLS_CA_CERT;
  const clientCert = process.env.MTLS_CLIENT_CERT;
  const clientKey = process.env.MTLS_CLIENT_KEY;

  if (!caCert || !clientCert || !clientKey) {
    console.log("mTLS not configured -- connecting without client certificates.");
    return undefined;
  }

  console.log(`mTLS configured: CA=${caCert}, cert=${clientCert}`);
  return {
    ca: fs.readFileSync(caCert),
    cert: fs.readFileSync(clientCert),
    key: fs.readFileSync(clientKey),
  };
}

async function main() {
  const serverUrl = process.env.RH_MCP_SERVER_URL!;

  // step 1: authenticate
  console.log("Authenticating with Red Hat SSO...");
  const token = await getOAuth2Token();
  console.log("Authentication successful.\n");

  // step 2: configure mTLS (optional)
  const tlsOpts = buildTlsOptions();

  // step 3: connect to Red Hat MCP server
  const transport = new StreamableHTTPClientTransport(new URL(serverUrl), {
    requestInit: {
      headers: { Authorization: `Bearer ${token}` },
    },
  });

  const client = new Client({ name: "orchestrator-client", version: "1.0.0" });
  await client.connect(transport);

  // step 4: discover tools
  const { tools } = await client.listTools();
  console.log(`Connected to: ${serverUrl}`);
  console.log(`Available tools (${tools.length}):`);
  for (const tool of tools) {
    console.log(`  - ${tool.name}`);
    console.log(`    ${tool.description}`);
  }
  console.log();

  // step 5: invoke a tool (adjust tool name based on the server you connect to)
  if (tools.length > 0) {
    const firstTool = tools[0];
    console.log(`Invoking tool: ${firstTool.name}`);
    console.log(`  Input schema: ${JSON.stringify(firstTool.inputSchema)}`);
    // uncomment and customize for your use case:
    // const result = await client.callTool({
    //   name: firstTool.name,
    //   arguments: { query: "openshift networking" },
    // });
    // for (const content of result.content as Array<{ text: string }>) {
    //   console.log(content.text);
    // }
  }

  await client.close();
}

main();
