# 🐾 Wildlife MCP API 🐾

The **Wildlife MCP API** powers geospatial and species identification tools using embeddings, AI, and ecoregion logic.  
It is designed for intelligent orchestration with AI agents and supports spatial queries, similarity search, and species lookups.  

---

## 🚨 Notes

- **Supported species**: Currently limited to **North American mammals and birds**.  
- Additional ecoregions and species classes (e.g. reptiles, amphibians) are coming soon.  

---

## 🔎 About MCP

This API is wrapped by **[FastAPI-MCP](https://github.com/modelcontextprotocol/fastapi-mcp)**, making endpoints **LLM-native tools**.  

- Endpoints are **discoverable via the OpenAPI spec**.  
- Compatible with **agentic workflows** (e.g., LangGraph, LangChain).  
- Enables **reasoning + orchestration** by AI systems.  

---

## 📡 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/ecoregion/by-coordinates` | Lookup an ecoregion by latitude/longitude |
| `/species/by-ecoregion` | Get species present in a given ecoregion |
| `/species/identify-by-embedding` | Identify species using image embeddings |

---

## 🛠 Developer Resources

- 📘 **Interactive Redoc** – Explore and test API endpoints  
- 📜 **OpenAPI Spec** – For programmatic discovery and agent integration  

---

## ⚡ Powered By

- 🌍 **WildFinder Database** — World Wildlife Fund (WWF)  
- 🔌 **FastAPI-MCP** — LLM-native tool wrapper for intelligent workflows  
- 🐍 **Python + FastAPI** — Core server logic and routing  
- 🗺 **PostgreSQL + PostGIS + PGVector** — Spatial + similarity search  
- 🧠 **OpenCLIP** — Multimodal embeddings for image + text similarity  
- 🔗 **LangGraph** — Agentic orchestration and decision-making  

---

## 🚀 Getting Started

1. Clone the repo:  
   ```bash
   git clone https://github.com/readcommitted/wildlife-vision-pipeline.git
   cd wildlife-vision-pipeline

## 📜 License

MIT License – See [LICENSE](./LICENSE) for details.
