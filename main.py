# app/main.py
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from app.ecoregion_tools import router as ecoregion_router
from app.similarity_tools import router as similarity_router
from app.species_tools import router as species_router

# Create a combined FastAPI app
app = FastAPI()

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
