# Modular RAG Framework

**A vendor-agnostic, production-ready Retrieval-Augmented Generation pipeline built with FastAPI, PostgreSQL (PGVector), and Pinecone.**

## Project Overview

This framework provides a robust backend for RAG applications, designed with a strict "Separation of Concerns" philosophy. Unlike tightly coupled RAG scripts, this project uses an interface-based architecture that allows developers to swap components (Vector Databases, Embedders, LLMs) with zero friction.

**Core Value Proposition:**

- **Dual-Database Strategy:** Develop locally using **PGVector** (Docker) for zero cost and total privacy, then deploy to **Pinecone** for cloud scalability—toggled via a single environment variable.
- **Asynchronous Processing:** Heavy ingestion tasks (PDF parsing, semantic chunking) run via FastAPI Background Tasks to prevent API blocking.
- **Layout-Aware Parsing:** Utilizes `pdfplumber` to correctly handle multi-column layouts and tables in financial/technical documents.
- **Fintech-Optimized Parsing:** Uses a "Crop & Stitch" algorithm to detect PDF tables, convert them to **Markdown**, and preserve their context for superior LLM reasoning.
- **Self-Healing Ingestion:** A modular chunking engine with a safety layer that automatically detects and splits oversized chunks to prevent API errors.
- **Hybrid Deployment:** Develop locally with **Llama 3** (via `llama.cpp`) and **PGVector** for zero cost, then scale to OpenAI and Pinecone with a config switch.
- **Dynamic Vector Store:** Automatically creates database tables based on embedding dimensions (e.g., `knowledge_embeddings_512`), allowing you to mix OpenAI, Cohere, and Local models in the same system without schema conflicts.

## System Architecture

The system is built on a modular pipeline architecture.

```mermaid
graph LR
    User[Client] --> API[FastAPI Routes]
    API --> Ingest[Ingestion Service]
    API --> Engine[RAG Engine]

    subgraph "Smart Data Pipeline"
    Ingest --> Parser[Layout-Aware PDF Parser]
    Parser --> ChunkerFactory[Chunking Factory]
    ChunkerFactory --> Safety[Token Safety Layer]
    Safety --> Embedder[OpenAI/Local Embedder]
    Embedder --> DynDB[Dynamic Table Factory]
    end

    subgraph "Inference Pipeline"
    Engine --> Embedder
    Engine --> DynDB
    DynDB --> LLM[Local Llama / OpenAI]
    end

```

## Features

- **[+] Vendor Agnostic:** Native support for both `PGVector` (Local) and `Pinecone` (Cloud).
- **[+] Metadata Filtering:** Precise retrieval using file-level filters (e.g., query only within `prospectus.pdf`).
- **[+] Duplicate Detection:** (Planned) Logic to prevent redundant context from polluting the LLM window.
- **[+] Benchmark Suite:** Included scripts to race database implementations against each other for latency/accuracy testing.
- **[+]Multi-Dimensional Storage:** The system detects your embedding model's output size (e.g., 1536 vs 512) and dynamically generates the correct SQL tables (`knowledge_embeddings_1536`, `knowledge_embeddings_512`).
- **[+]Vector Slicing:** Automatically truncates OpenAI vectors to smaller dimensions (e.g., 512) to reduce storage costs by **66%** while maintaining performance.
- **[+]Markdown Table Extraction:** Extracts tables from PDFs and converts them to Markdown format, ensuring LLMs can "read" financial data row-by-row.
- **[+]Context Preservation:** Preserves the text immediately surrounding tables so the LLM knows *what* the data represents.
- **[+]Recursive Strategy:** (Default) Robust splitting for data-heavy documents.
- **[+]Semantic Strategy:** (Optional) AI-driven splitting based on topic changes.
- **[+]Safety Guardrails:** A dedicated `TokenSafetyEnforcer` catches chunks that exceed model limits (e.g., >8192 tokens) and recursively splits them before API calls.
- **[+]Local LLM Support:** Native integration with `llama-cpp-python` for running quantized models (GGUF) on CPU/Apple Silicon.
- **[+]Async Wrapper:** Runs synchronous local inference in non-blocking threads to keep the API responsive.
## Getting Started

### 1. Prerequisites

- Python 3.12+
- Docker (Required only if using Local PGVector)
- OpenAI API Key

### 2. Installation

Clone the repository and install dependencies. We recommend using a virtual environment.

```bash
git clone [https://github.com/yourusername/rag-framework.git](https://github.com/kamalpandiv/refactored-couscous.git)
cd rag-framework

# Setup virtual environment
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
uv sync

```

### 3. Configuration

Create a `.env` file in the root directory.

```ini
# --- Core Config ---
OPENAI_API_KEY=sk-your-key-here
# Path to your local GGUF model
LOCAL_MODEL_PATH=./models/Hermes-2-Pro-Llama-3-8B.Q4_K_M.gguf

# --- Database Selection ---
USE_LOCAL_DB=True

# --- Postgres Config (PGVector) ---
DATABASE_URL=postgresql://user:password@localhost:5432/rag_db

# --- Ingestion Settings ---
# 'recursive' (Financial/Technical) or 'semantic' (Prose)
CHUNKING_STRATEGY=recursive
BATCH_SIZE=100

```

### 4. Database Setup (Local Mode)

If running locally, spin up the PGVector container. This command creates a persistent volume so data survives restarts.

```bash
docker run -d \
  --name rag-postgres \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=rag_db \
  -p 5432:5432 \
  -v rag_data:/var/lib/postgresql/data \
  pgvector/pgvector:pg16

```

### 5. Running the API

```bash
python main.py

```

- Server running at: `http://0.0.0.0:8000`
- Swagger UI: `http://0.0.0.0:8000/docs`

## Llama cpp setup using huggingface

```bash
huggingface-cli download NousResearch/Hermes-2-Pro-Llama-3-8B-GGUF \
  Hermes-2-Pro-Llama-3-8B-Q4_K_M.gguf \
  --local-dir models
```

## Usage Examples

**Ingest a Document (Non-Blocking)**

```bash
curl -X POST "http://localhost:8000/api/v1/ingest/file" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/annual_report.pdf"

```

**Query the Knowledge Base**

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the risks mentioned in the report?",
    "file_name": "annual_report.pdf"
  }'

```

## Project Structure

The codebase uses a **Modular Component Architecture** to facilitate easy contribution and component swapping.

```text
rag-framework/
├── app/
│   ├── api/             # API Routes
│   ├── components/      # Interchangeable Modules
│   │   ├── chunking/    # Modular Chunking Strategies
│   │   │   ├── base.py
│   │   │   ├── factory.py
│   │   │   ├── recursive.py
│   │   │   ├── semantic.py
│   │   │   └── safety.py  # Token limit enforcer
│   │   ├── embedders/   # OpenAI / Local Embedders
│   │   ├── loaders/     # PDF Plumber (Crop & Stitch logic)
│   │   ├── vector_dbs/  # Dynamic Table Factory
│   │   └── llms/        # BaseLLM, OpenAILLM, LocalLlamaLLM
│   ├── core/            # Config & Interfaces
│   ├── models/          # Database Models (Dynamic)
│   └── services/        # Orchestration (Ingestion, Search)
├── main.py
└── requirements.txt

```

## Roadmap

We welcome contributions to extend the framework. Current priorities:

- [ ] **Qdrant Support:** Add `QdrantDB` adapter.
- [ ] **Local LLM:** Add `LlamaCPP` or `Ollama` support to `app/components/llms/`.
- [ ] **Hybrid Search:** Implement keyword + vector search (BM25).
- [x] **Deduplication:** Add hashing strategy to prevent duplicate chunks in the vector store.
* [x] **Dynamic Vector Tables:** Auto-scaling DB schema.
* [x] **Local LLM:** Llama 3 via `llama.cpp`.
* [x] **Advanced PDF Parsing:** Markdown table extraction.
* [ ] **Hybrid Search:** Implement keyword + vector search (BM25).
* [ ] **Deduplication:** Add hashing strategy to prevent duplicate chunks.
* [ ] **Graph RAG:** Experiment with Knowledge Graph integration.

## Contribution Guidelines

1. **Fork & Clone:** Fork the repo and clone it locally.
2. **Branch:** Create a branch for your feature (`git checkout -b feature/new-adapter`).
3. **Code Style:** formatted (ruff).
4. **Interface Compliance:** If adding a new DB, ensure it inherits from `app.core.interfaces.BaseVectorDB`.
5. **Pull Request:** Submit a PR with a clear description of the changes.

## License

Distributed under the MIT License. See `LICENSE` for more information.
