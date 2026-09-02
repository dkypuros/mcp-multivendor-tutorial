"""
Basic MCP Server Example (Python)

A minimal MCP server that exposes two tools:
  1. query_knowledge_base - search a product knowledge base
  2. search_case_history  - search past support case resolutions

This demonstrates the pattern a vendor uses to expose product knowledge
to an external orchestrator via MCP.
"""

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

app = Server("vendor-knowledge-agent")

SAMPLE_KB = {
    "openshift": "OpenShift is a Kubernetes-based container platform for enterprise workloads.",
    "rhel": "Red Hat Enterprise Linux is a commercial Linux distribution for servers and workloads.",
    "ansible": "Ansible is an agentless automation platform for configuration management.",
    "ai": "OpenShift AI provides MLOps capabilities for training and serving models on Kubernetes.",
}

SAMPLE_CASES = [
    {"id": "CASE-001", "summary": "OCP node not ready after upgrade", "resolution": "Drain node, clear kubelet certs, restart kubelet."},
    {"id": "CASE-002", "summary": "RHEL kernel panic on boot", "resolution": "Boot from rescue kernel, rebuild initramfs with dracut."},
    {"id": "CASE-003", "summary": "Ansible playbook timeout on large inventory", "resolution": "Increase forks, enable pipelining, use mitogen strategy."},
]


@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="query_knowledge_base",
            description="Search the vendor product knowledge base for platform documentation and guidance.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g., 'openshift networking', 'rhel security')",
                    }
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="search_case_history",
            description="Search past support case resolutions by keyword similarity.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Describe the issue to find similar past cases.",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 3).",
                        "default": 3,
                    },
                },
                "required": ["query"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "query_knowledge_base":
        query = arguments["query"].lower()
        matches = {k: v for k, v in SAMPLE_KB.items() if k in query or query in k}
        if matches:
            result = "\n".join(f"- {k}: {v}" for k, v in matches.items())
        else:
            result = f"No knowledge base entries found for '{arguments['query']}'."
        return [TextContent(type="text", text=result)]

    elif name == "search_case_history":
        query = arguments["query"].lower()
        max_results = arguments.get("max_results", 3)
        matches = [c for c in SAMPLE_CASES if query in c["summary"].lower() or query in c["resolution"].lower()]
        matches = matches[:max_results]
        if matches:
            result = "\n".join(f"- [{c['id']}] {c['summary']}\n  Resolution: {c['resolution']}" for c in matches)
        else:
            result = f"No similar cases found for '{arguments['query']}'."
        return [TextContent(type="text", text=result)]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
