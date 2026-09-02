"""
Basic MCP Client Example (Python)

Connects to the basic MCP server via STDIO transport, discovers available
tools, and invokes them. This demonstrates how an orchestrator (e.g., a
NOS Agent Fabric) would interact with a vendor knowledge agent.
"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["../01_basic_mcp_server/server.py"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # step 1: discover available tools
            tools = await session.list_tools()
            print("Available tools:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")
            print()

            # step 2: query the knowledge base
            print("--- Query: 'openshift' ---")
            result = await session.call_tool("query_knowledge_base", {"query": "openshift"})
            for content in result.content:
                print(content.text)
            print()

            # step 3: search case history
            print("--- Case search: 'upgrade' ---")
            result = await session.call_tool("search_case_history", {"query": "upgrade", "max_results": 5})
            for content in result.content:
                print(content.text)
            print()

            # step 4: query something not in the KB
            print("--- Query: 'satellite' ---")
            result = await session.call_tool("query_knowledge_base", {"query": "satellite"})
            for content in result.content:
                print(content.text)


if __name__ == "__main__":
    asyncio.run(main())
