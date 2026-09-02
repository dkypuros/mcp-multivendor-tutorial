/**
 * Basic MCP Server Example (TypeScript)
 *
 * A minimal MCP server that exposes two tools:
 *   1. query_knowledge_base - search a product knowledge base
 *   2. search_case_history  - search past support case resolutions
 *
 * This demonstrates the pattern a vendor uses to expose product knowledge
 * to an external orchestrator via MCP.
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({
  name: "vendor-knowledge-agent",
  version: "1.0.0",
});

const SAMPLE_KB: Record<string, string> = {
  openshift: "OpenShift is a Kubernetes-based container platform for enterprise workloads.",
  rhel: "Red Hat Enterprise Linux is a commercial Linux distribution for servers and workloads.",
  ansible: "Ansible is an agentless automation platform for configuration management.",
  ai: "OpenShift AI provides MLOps capabilities for training and serving models on Kubernetes.",
};

const SAMPLE_CASES = [
  { id: "CASE-001", summary: "OCP node not ready after upgrade", resolution: "Drain node, clear kubelet certs, restart kubelet." },
  { id: "CASE-002", summary: "RHEL kernel panic on boot", resolution: "Boot from rescue kernel, rebuild initramfs with dracut." },
  { id: "CASE-003", summary: "Ansible playbook timeout on large inventory", resolution: "Increase forks, enable pipelining, use mitogen strategy." },
];

server.tool(
  "query_knowledge_base",
  "Search the vendor product knowledge base for platform documentation and guidance.",
  { query: z.string().describe("Search query (e.g., 'openshift networking', 'rhel security')") },
  async ({ query }) => {
    const q = query.toLowerCase();
    const matches = Object.entries(SAMPLE_KB).filter(([k]) => k.includes(q) || q.includes(k));
    const text = matches.length > 0
      ? matches.map(([k, v]) => `- ${k}: ${v}`).join("\n")
      : `No knowledge base entries found for '${query}'.`;
    return { content: [{ type: "text" as const, text }] };
  }
);

server.tool(
  "search_case_history",
  "Search past support case resolutions by keyword similarity.",
  {
    query: z.string().describe("Describe the issue to find similar past cases."),
    max_results: z.number().default(3).describe("Maximum number of results to return."),
  },
  async ({ query, max_results }) => {
    const q = query.toLowerCase();
    const matches = SAMPLE_CASES
      .filter((c) => c.summary.toLowerCase().includes(q) || c.resolution.toLowerCase().includes(q))
      .slice(0, max_results);
    const text = matches.length > 0
      ? matches.map((c) => `- [${c.id}] ${c.summary}\n  Resolution: ${c.resolution}`).join("\n")
      : `No similar cases found for '${query}'.`;
    return { content: [{ type: "text" as const, text }] };
  }
);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main();
