# Modular RAG Framework

**A vendor-agnostic, production-ready Retrieval-Augmented Generation pipeline built with FastAPI, PostgreSQL (PGVector), and Pinecone.**

## Project Overview

This framework provides a robust backend for RAG applications, designed with a strict "Separation of Concerns" philosophy. Unlike tightly coupled RAG scripts, this project uses an interface-based architecture that allows developers to swap components (Vector Databases, Embedders, LLMs) with zero friction.

**Core Value Proposition:**

- **Dual-Database Strategy:** Develop locally using **PGVector** (Docker) for zero cost and total privacy, then deploy to **Pinecone** for cloud scalability—toggled via a single environment variable.
- **Asynchronous Processing:** Heavy ingestion tasks (PDF parsing, semantic chunking) run via FastAPI Background Tasks to prevent API blocking.
- **Layout-Aware Parsing:** Utilizes `pdfplumber` to correctly handle multi-column layouts and tables in financial/technical documents.

## System Architecture

The system is built on a modular pipeline architecture.

```mermaid
graph LR
    User[Client] --> API[FastAPI Routes]
    API --> Ingest[Ingestion Service]
    API --> Engine[RAG Engine]

    subgraph "Data Pipeline"
    Ingest --> Loaders[PDF/Web Loaders]
    Loaders --> Chunker[Semantic Chunking]
    Chunker --> Embedder[OpenAI/Local Embedder]
    Embedder --> VectorDB[(Vector Store)]
    end

    subgraph "Inference Pipeline"
    Engine --> Embedder
    Engine --> VectorDB
    VectorDB --> LLM[LLM Synthesis]
    end

```

## Features

- **[+] Vendor Agnostic:** Native support for both `PGVector` (Local) and `Pinecone` (Cloud).
- **[+] Metadata Filtering:** Precise retrieval using file-level filters (e.g., query only within `prospectus.pdf`).
- **[+] Duplicate Detection:** (Planned) Logic to prevent redundant context from polluting the LLM window.
- **[+] Benchmark Suite:** Included scripts to race database implementations against each other for latency/accuracy testing.

## Getting Started

### 1. Prerequisites

- Python 3.10+
- Docker (Required only if using Local PGVector)
- OpenAI API Key

### 2. Installation

Clone the repository and install dependencies. We recommend using a virtual environment.

```bash
git clone https://github.com/yourusername/rag-framework.git
cd rag-framework

# Setup virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

```

### 3. Configuration

Create a `.env` file in the root directory.

```ini
# --- Core Config ---
OPENAI_API_KEY=sk-your-key-here

# --- Database Selection ---
# Set to 'True' for Local Docker Postgres
# Set to 'False' for Cloud Pinecone
USE_LOCAL_DB=True

# --- Postgres Config (If USE_LOCAL_DB=True) ---
DATABASE_URL=postgresql://user:password@localhost:5432/rag_db

# --- Pinecone Config (If USE_LOCAL_DB=False) ---
PINECONE_API_KEY=your-pinecone-key
PINECONE_ENV=us-east-1

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

The codebase is organized to facilitate easy contribution and component swapping.

```text
rag-framework/
├── app/
│   ├── api/             # API Route definitions
│   ├── components/      # Interchangeable modules
│   │   ├── embedders/   # Interface for embedding providers
│   │   ├── loaders/     # Document parsing logic
│   │   ├── vector_dbs/  # Database adapters (PGVector, Pinecone)
│   │   └── llms/        # LLM interaction layer
│   ├── core/            # Abstract Base Classes (Interfaces) & Config
│   ├── models/          # Pydantic data models
│   └── services/        # Orchestration logic (Ingestion, RAG Loop)
├── main.py              # Application entry point
├── benchmark.py         # Performance testing script
└── requirements.txt

```

## Development & Benchmarking

To compare the performance of the Local DB vs. Cloud DB, run the included benchmark script. This script bypasses the API to test raw insertion and retrieval speeds.

```bash
python benchmark.py

```

**Sample Output:**

```text
Metric          | Pinecone        | PGVector
--------------------------------------------------
Time (ms)       | 250.45 ms       | 15.20 ms
Accuracy        | 0.8512          | 0.8511

```

## Roadmap

We welcome contributions to extend the framework. Current priorities:

- [ ] **Qdrant Support:** Add `QdrantDB` adapter.
- [ ] **Local LLM:** Add `LlamaCPP` or `Ollama` support to `app/components/llms/`.
- [ ] **Hybrid Search:** Implement keyword + vector search (BM25).
- [ ] **Deduplication:** Add hashing strategy to prevent duplicate chunks in the vector store.

## Contribution Guidelines

1. **Fork & Clone:** Fork the repo and clone it locally.
2. **Branch:** Create a branch for your feature (`git checkout -b feature/new-adapter`).
3. **Code Style:** Ensure code is typed (`mypy`) and formatted (PEP8).
4. **Interface Compliance:** If adding a new DB, ensure it inherits from `app.core.interfaces.BaseVectorDB`.
5. **Pull Request:** Submit a PR with a clear description of the changes.

## License

Distributed under the MIT License. See `LICENSE` for more information.
