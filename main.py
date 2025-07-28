# app/main.py
from fastapi_mcp import FastApiMCP
from app.ecoregion_tools import app


mcp = FastApiMCP(app)  # Add MCP server to the FastAPI app
mcp.mount_http()  # MCP server

mcp.setup_server()


# Step 4: run it
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


