import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import os

HERE = os.path.dirname(os.path.abspath(__file__))

SERVER = StdioServerParameters(
    command=sys.executable,
    args=[os.path.join(HERE, "mcp_server.py")],
    env=dict(os.environ),  # pass the API key and settings to the server
    cwd=HERE,              # run the server from the project folder
)
# ---------- 1. Get tool schemas from the server ----------
async def _list_tools():
    async with stdio_client(SERVER) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            return result.tools

def get_tool_schemas():
    tools = asyncio.run(_list_tools())
    # Convert MCP format → OpenAI function-calling format
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.inputSchema,
            },
        }
        for t in tools
    ]

# ---------- 2. Call tools through the server ----------
async def _call_tools(calls):
    results = []
    async with stdio_client(SERVER) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for name, args in calls:
                result = await session.call_tool(name, args)
                if result.isError:
                    raise RuntimeError(f"Tool {name} failed: {result.content[0].text}")
                results.append(result.content[0].text)
    return results

def call_tools(calls):
    return asyncio.run(_call_tools(calls))