from mcp.server.fastmcp import FastMCP
from tools import generate_slide_image as make_image

# 1. Create the server
mcp = FastMCP("carousel-tools")

# 2. Publish the tool
@mcp.tool()
def generate_slide_image(prompt: str, slide_number: int) -> str:
    """Generate one image for one carousel slide from an English image prompt. Returns the saved file path."""
    return make_image(prompt, slide_number)

# 3. Start the server
if __name__ == "__main__":
    mcp.run()