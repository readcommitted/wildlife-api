# app/main.py
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from app.ecoregion_tools import router as ecoregion_router
from app.similarity_tools import router as similarity_router
from app.species_tools import router as species_router
from app.rerank_with_weights_tool import router as rerank_with_weights_router
from tools.seed_router import router as seed_router
from fastapi.responses import HTMLResponse


# Create a combined FastAPI app
app = FastAPI(
    docs_url=None,
    redoc_url="/docs"
)

# Landing Page
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def landing_page():
    return """
    <html>
        <head>
            <title>Wildlife MCP API</title>
            <style>
                body { font-family: sans-serif; max-width: 900px; margin: 4rem auto; line-height: 1.6; }
                code { background: #f2f2f2; padding: 2px 4px; border-radius: 4px; }
                pre { background: #f9f9f9; padding: 1rem; border-left: 4px solid #4CAF50; overflow-x: auto; }
            </style>
        </head>
        <body>
            <h1>🐾 Wildlife MCP API 🐾</h1>
            <p>This API powers geospatial and species identification tools using embeddings, AI, and ecoregion logic.</p>

            <h2>Notes</h2>
            <p>
                <strong>Supported species:</strong> Currently limited to <strong>North American mammals and birds</strong>.
                Additional ecoregions and species classes (e.g. reptiles, amphibians) are coming soon.
            </p>
            <p>
                <strong>About MCP:</strong> This API is wrapped by <code>FastAPI-MCP</code>, making its endpoints
                compatible with AI agents. Tools are discoverable through the OpenAPI spec and can be used in Agentic 
                workflows for intelligent orchestration and reasoning.
            </p>
            
            <h2>API Endpoints</h2>
            <ul>
                <li><code>/ecoregion/by-coordinates</code> – Lookup ecoregion using lat/lon</li>
                <li><code>/species/by-ecoregion</code> – Get species in a given ecoregion</li>
                <li><code>/species/identify-by-embedding</code> – Identify species using image embedding</li>
            </ul>

            <h2>Example CURL Commands</h2>
            <h3>Get ecoregion by coordinates</h3>
            <pre><code>curl -X GET "https://api.wildlife.readcommitted.com/ecoregion/by-coordinates?lat=44.6&lon=-110.5" \\
     -H "accept: application/json"</code></pre>

            <h3>Get species by ecoregion</h3>
            <pre><code>curl -X GET "https://api.wildlife.readcommitted.com/species/by-ecoregion?eco_code=NA0528" \\
     -H "accept: application/json"</code></pre>

            <h2>🔎 Developer Resources</h2>
            <ul>
                <li><a href="/docs">Interactive Redoc</a></li>
                <li><a href="/openapi.json">OpenAPI Spec</a></li>
            </ul>
            <h2>⚙Powered By</h2>
            
            <ul>
                <li><strong>WildFinder Database</strong> — <a href="https://www.worldwildlife.org/publications/wildfinder-database" target="_blank">World Wildlife Fund (WWF)</a></li>
                <li><strong>FastAPI-MCP</strong> — LLM-native tool wrapper for intelligent API workflows</li>
                <li><strong>Python + FastAPI</strong> — Core server logic and routing</li>
                <li><strong>PostgreSQL + PostGIS + PGVector</strong> — Spatial queries and similarity search</li>
                <li><strong>OpenCLIP</strong> — Multimodal embeddings for image + text similarity</li>
                <li><strong>LangGraph</strong> — Orchestration layer for agentic decision-making</li>
            </ul>

        </body>
    </html>
    """


# Register all routers at the root
app.include_router(similarity_router)
app.include_router(ecoregion_router)
app.include_router(species_router)
app.include_router(rerank_with_weights_router)

app.include_router(seed_router)


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
        "get_species_by_ecoregion",
        "rerank_with_weights_router"
    ]
)


# Mount MCP HTTP interface and setup OpenAPI
mcp.mount_http()
mcp.setup_server()

# Run server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
