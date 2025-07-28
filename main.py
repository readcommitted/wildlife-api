# app/main.py
from fastapi_mcp import FastApiMCP
from app.ecoregion_tools import app


mcp = FastApiMCP(
    app,
    name="Wildlife MCP",
    description="Provides wildlife geospatial tools for ecoregion lookup and species identification.",
    describe_full_response_schema=True,
    describe_all_responses=True,
    include_operations=["get_ecoregion_by_coordinates"]  # Optional — filter to just callable tools
)
# Add MCP server to the FastAPI app
mcp.mount_http()  # MCP server

mcp.setup_server()

# Step 4: run it
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


