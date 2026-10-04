import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# How to start the server
server = StdioServerParameters(command=sys.executable, args=["mcp_server.py"])

async def main():
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. Ask the server what tools it has
            tools = await session.list_tools()
            print("Tools:", [t.name for t in tools.tools])

            # 2. Call the tool
            result = await session.call_tool(
                "generate_slide_image", {"prompt": "test", "slide_number": 1}
            )
            print("Result:", result.content[0].text)

asyncio.run(main())