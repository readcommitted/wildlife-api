# app/main.py
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from app.ecoregion_tools import router as ecoregion_router
from app.similarity_tools import router as similarity_router
from app.species_tools import router as species_router
from fastapi.responses import HTMLResponse

# Create a combined FastAPI app
app = FastAPI()

# Landing Page
@app.get("/", response_class=HTMLResponse)
async def landing_page():
    return """
    <html>
        <head><title>Wildlife MCP API</title></head>
        <body style="font-family:sans-serif; max-width: 800px; margin: 4rem auto;">
            <h1>🌲 Wildlife MCP API</h1>
            <p>This API powers geospatial and species identification tools using embeddings, AI, and ecoregion logic.</p>
            <h2>Available Tools</h2>
            <ul>
                <li><a href="/docs">Interactive Swagger Docs</a></li>
                <li><a href="/openapi.json">OpenAPI Spec</a></li>
            </ul>
            <p>Try endpoints like <code>/ecoregion/by-coordinates</code> or <code>/species/identify-by-embedding</code>.</p>
        </body>
    </html>
    """
# Register all routers at the root
app.include_router(similarity_router)
app.include_router(ecoregion_router)
app.include_router(species_router)

# Register with FastApiMCP
mcp = FastApiMCP(
    app,
    name="Wildlife MCP",
    description=(
        "An intelligent API powered by FastAPI + FastAPI-MCP. "
        "Supports geospatial ecoregion lookup, species identification via embeddings, "
        "and agentic reasoning workflows using LangGraph-compatible tools."
    ),
    describe_full_response_schema=True,
    describe_all_responses=True,
    include_operations=[
        "get_ecoregion_by_coordinates",
        "identify_species_by_embedding",
        "get_species_by_ecoregion"
    ]
)


# Mount MCP HTTP interface and setup OpenAPI
mcp.mount_http()
mcp.setup_server()

# Run server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
