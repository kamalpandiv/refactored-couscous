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
- **Domain-Specific Prompting:** Swap system prompts per use case via a single config variable — no code changes required.
- **External Validator Apps:** A clean HTTP interface allows external scripts and services to use the RAG system as a knowledge backend.

## System Architecture

The system is built on a modular pipeline architecture.

```mermaid
graph LR
    User[Client] --> API[FastAPI Routes]
    ExternalApp[External App e.g. Email Validator] --> API
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
    Engine --> PromptLoader[Prompt Loader]
    PromptLoader --> Embedder
    Engine --> DynDB
    DynDB --> LLM[Local Llama / OpenAI]
    end
```

## Features

- **[+] Vendor Agnostic:** Native support for both `PGVector` (Local) and `Pinecone` (Cloud).
- **[+] Metadata Filtering:** Precise retrieval using file-level filters (e.g., query only within `prospectus.pdf`).
- **[+] Duplicate Detection:** Logic to prevent redundant context from polluting the LLM window.
- **[+] Benchmark Suite:** Included scripts to race database implementations against each other for latency/accuracy testing.
- **[+] Multi-Dimensional Storage:** The system detects your embedding model's output size (e.g., 1536 vs 512) and dynamically generates the correct SQL tables (`knowledge_embeddings_1536`, `knowledge_embeddings_512`).
- **[+] Vector Slicing:** Automatically truncates OpenAI vectors to smaller dimensions (e.g., 512) to reduce storage costs by **66%** while maintaining performance.
- **[+] Markdown Table Extraction:** Extracts tables from PDFs and converts them to Markdown format, ensuring LLMs can "read" financial data row-by-row.
- **[+] Context Preservation:** Preserves the text immediately surrounding tables so the LLM knows _what_ the data represents.
- **[+] Recursive Strategy:** (Default) Robust splitting for data-heavy documents.
- **[+] Semantic Strategy:** (Optional) AI-driven splitting based on topic changes.
- **[+] Safety Guardrails:** A dedicated `TokenSafetyEnforcer` catches chunks that exceed model limits (e.g., >8192 tokens) and recursively splits them before API calls.
- **[+] Local LLM Support:** Native integration with `llama-cpp-python` for running quantized models (GGUF) on CPU/Apple Silicon.
- **[+] Async Wrapper:** Runs synchronous local inference in non-blocking threads to keep the API responsive.
- **[+] Centralized Dependency Injection:** All FastAPI dependencies live in `core/dependencies.py` — zero wiring logic in route files.
- **[+] Domain-Specific System Prompts:** Load per-domain prompts from `app/prompts/system/` via a single `SYSTEM_PROMPT_FILE` env variable. No hardcoded prompts in code.
- **[+] Frontend Configuration:** Dedicated `/api/v1/config` endpoint to expose non-sensitive backend settings to clients.
- **[+] External App Support:** The RAG system exposes a clean HTTP API, allowing external validator scripts or services to use ingested knowledge without modifying the core.

## Getting Started

### 1. Prerequisites

- Python 3.12+
- Docker (Required only if using Local PGVector)
- OpenAI API Key

### 2. Installation

Clone the repository and install dependencies. We recommend using a virtual environment.

```bash
# Clone the repo
git clone https://github.com/kamalpandiv/refactored-couscous.git

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

# --- Prompt Config ---
# Name of the prompt file to load from app/prompts/ (without .txt extension)
# Use 'default' for a general-purpose assistant
SYSTEM_PROMPT_FILE=default
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

**Query with a Translation Strategy**

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the opt-out requirements?",
    "file_name": "can_spam_guide.pdf",
    "translation_strategy": "multi_query"
  }'
```

## Domain-Specific System Prompts

The RAG engine supports swappable system prompts loaded from `app/prompts/system/`. This allows you to repurpose the same RAG system for different compliance domains, assistants, or use cases — without changing any code.

```
app/prompts/
├── system/
│   ├── default.txt       # General-purpose assistant
│   ├── can_spam.txt      # CAN-SPAM Act compliance validator
│   └── ...
└── user/
    ├── multi_query.txt   # User prompts for translation strategies
    └── ...
```

To switch domains, update your `.env`:

```ini
SYSTEM_PROMPT_FILE=can_spam
```

**Prompt design principle:** Keep system prompts short and role-defining. The actual domain knowledge comes from retrieved chunks — do not duplicate rules in the prompt.

Example `can_spam.txt`:

```
You are a CAN-SPAM Act compliance assistant.
Answer questions based strictly on the provided context from the FTC compliance guide.
If the answer is not found in the context, say "I don't have enough information in the provided documents to answer this."
Be concise and cite specific requirements when relevant.
```

## External Validator Apps

The RAG system is designed to serve as a **knowledge backend** for external applications. External apps construct a query, call the RAG API over HTTP, and receive grounded answers — keeping the RAG system clean and reusable.

```
External App (e.g. Email Validator)
        │
        │  POST /api/v1/query
        ▼
   RAG System API
        │
        ▼
  Vector DB (ingested PDFs)
```

**Example: CAN-SPAM Email Validator**

Place external scripts in `scripts/` — they are standalone consumers of the API, not part of the core framework.

```
scripts/
└── emails/
    └── validator.py    # CAN-SPAM email compliance checker
```

```bash
# Terminal 1 — start the RAG system
python main.py

# Terminal 2 — run the validator against a sample email
python scripts/emails/validator.py
```

The validator script calls `POST /api/v1/query` with the email content and retrieves a structured compliance assessment grounded in the ingested FTC compliance guide.

## Project Structure

The codebase uses a **Modular Component Architecture** to facilitate easy contribution and component swapping.

```text
rag-framework/
├── app/
│   ├── api/             # Modular API Layer
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── config.py
│   │       │   ├── ingest.py
│   │       │   └── query.py
│   │       └── api.py   # API Orchestrator
│   ├── components/      # Interchangeable Modules
...
│   ├── core/            # Config, Interfaces & Dependencies
│   │   ├── config.py
│   │   ├── interfaces.py
│   │   ├── dependencies.py  # Centralized FastAPI Depends()
│   │   └── prompt_loader.py # Loads prompts from app/prompts/
│   ├── models/          # Data Models (API & Frontend Config)
│   │   ├── api_requests.py
│   │   ├── api_response.py
│   │   ├── frontend_config.py
│   │   └── ...

│   ├── prompts/         # Swappable system/user prompt files (.txt)
│   │   ├── system/
│   │   └── user/
│   └── services/        # Orchestration (Ingestion, RAG Engine)
├── scripts/             # Standalone external consumer scripts
│   └── emails/
│       └── validator.py # CAN-SPAM email validator (calls RAG API)
├── main.py
└── requirements.txt
```

## Query Translation Strategies

The `/query` endpoint supports optional query translation to improve retrieval quality for exploratory questions.

| Strategy      | Best For                     | How It Works                                       |
| ------------- | ---------------------------- | -------------------------------------------------- |
| `multi_query` | Broad research questions     | Generates 3 query variations, retrieves across all |
| `step_back`   | Conceptual questions         | Abstracts to a higher-level query                  |
| `rag_fusion`  | Maximum coverage             | Generates 4 queries with RRF score merging         |
| _(none)_      | Specific lookups, validation | Uses raw query directly — fastest and most precise |

> **Tip:** For compliance validation (e.g., checking an email against CAN-SPAM rules), omit the translation strategy. Your query already contains all the specifics needed for precise retrieval.

## Roadmap

- [ ] **Qdrant Support:** Add `QdrantDB` adapter.
- [ ] **Hybrid Search:** Implement keyword + vector search (BM25).
- [ ] **Deduplication:** Add hashing strategy to prevent duplicate chunks.
- [ ] **Graph RAG:** Experiment with Knowledge Graph integration.
- [x] **Centralized Dependencies:** All `Depends()` wiring moved to `core/dependencies.py`.
- [x] **Domain Prompt Loader:** Swappable system prompts via `app/prompts/` and `SYSTEM_PROMPT_FILE` env var.
- [x] **External App Pattern:** Clean separation between RAG core and consumer scripts.
- [x] **Dynamic Vector Tables:** Auto-scaling DB schema.
- [x] **Local LLM:** Llama 3 via `llama.cpp`.
- [x] **Advanced PDF Parsing:** Markdown table extraction.

## Contribution Guidelines

1. **Fork & Clone:** Fork the repo and clone it locally.
2. **Branch:** Create a branch for your feature (`git checkout -b feature/new-adapter`).
3. **Code Style:** Formatted with `ruff`.
4. **Interface Compliance:** If adding a new DB, ensure it inherits from `app.core.interfaces.BaseVectorDB`.
5. **Prompt Files:** If adding a new domain prompt, place it in `app/prompts/` as a `.txt` file.
6. **External Scripts:** Consumer scripts (validators, batch processors) belong in `scripts/`, not in `app/`.
7. **Pull Request:** Submit a PR with a clear description of the changes.

## License

Distributed under the MIT License. See `LICENSE` for more information.
