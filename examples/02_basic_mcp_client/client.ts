/**
 * Basic MCP Client Example (TypeScript)
 *
 * Connects to the basic MCP server via STDIO transport, discovers available
 * tools, and invokes them. This demonstrates how an orchestrator (e.g., an
 * orchestration platform's agent fabric) would interact with a vendor
 * knowledge agent.
 */

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

async function main() {
  const transport = new StdioClientTransport({
    command: "npx",
    args: ["tsx", "../01_basic_mcp_server/server.ts"],
  });

  const client = new Client({ name: "orchestrator-client", version: "1.0.0" });
  await client.connect(transport);

  // step 1: discover available tools
  const { tools } = await client.listTools();
  console.log("Available tools:");
  for (const tool of tools) {
    console.log(`  - ${tool.name}: ${tool.description}`);
  }
  console.log();

  // step 2: query the knowledge base
  console.log("--- Query: 'openshift' ---");
  const kbResult = await client.callTool({
    name: "query_knowledge_base",
    arguments: { query: "openshift" },
  });
  for (const content of kbResult.content as Array<{ text: string }>) {
    console.log(content.text);
  }
  console.log();

  // step 3: search case history
  console.log("--- Case search: 'upgrade' ---");
  const caseResult = await client.callTool({
    name: "search_case_history",
    arguments: { query: "upgrade", max_results: 5 },
  });
  for (const content of caseResult.content as Array<{ text: string }>) {
    console.log(content.text);
  }
  console.log();

  // step 4: query something not in the KB
  console.log("--- Query: 'satellite' ---");
  const missResult = await client.callTool({
    name: "query_knowledge_base",
    arguments: { query: "satellite" },
  });
  for (const content of missResult.content as Array<{ text: string }>) {
    console.log(content.text);
  }

  await client.close();
}

main();
