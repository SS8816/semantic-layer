# Semantic Layer

A comprehensive semantic layer system for exploring, analyzing, and managing database table metadata with AI-powered insights, intelligent relationship discovery, and **natural language semantic search**. Built with FastAPI, React, Starburst/Trino, DynamoDB, Neptune Analytics, HuggingFace Transformers, and Azure OpenAI GPT-5.

## Overview

The Semantic Layer automatically enriches database tables with rich metadata, discovers relationships between tables using advanced AI models, and provides **natural language semantic search** powered by vector embeddings and Neptune Analytics graph database. It provides a complete semantic understanding of your data landscape.

**Key Capabilities:**
-  **Natural Language Semantic Search**: Query tables and columns using natural language (e.g., "POI ID columns")
-  **Dual Search Modes**: Analytics mode (table-level) and Data Mining mode (column-level granular search)
-  **AI-Powered Metadata Generation**: Automatically generate comprehensive metadata for database tables
-  **Geographic Intelligence**: Detect countries, cities, states, coordinates, and geometric data
-  **Smart Aliases & Descriptions**: Generate human-readable aliases and descriptions using AI
-  **Relationship Discovery**: Discover relationships between tables using Azure OpenAI GPT-5
-  **Vector Similarity Search**: Neptune Analytics with 2048-dimensional embeddings
-  **Configurable Search Tags**: Tag tables as "Analytics" or "Data Mining" for optimized search results
-  **Schema Change Monitoring**: Track schema changes with real-time alerts
-  **Intuitive UI**: Visualize table data, metadata, and relationships in a beautiful React interface

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                      React Frontend                            │
│    (Browse, Semantic Search, Enriched Tables, Metadata)        │
└─────────────────────────┬──────────────────────────────────────┘
                          │ REST API
┌─────────────────────────┴──────────────────────────────────────┐
│                     FastAPI Backend                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Services:                                               │  │
│  │  - Semantic Search (Neptune vector similarity)           │  │
│  │  - Embedding Service (Azure OpenAI text-embedding)       │  │
│  │  - Metadata Generator (orchestrator)                     │  │
│  │  - Geographic Detector (countries/cities/states)         │  │
│  │  - Alias Generator (Azure OpenAI GPT-5)                  │  │
│  │  - Relationship Detector (Azure OpenAI GPT-5)            │  │
│  │  - Column Type Detector (dimension/measure/etc.)         │  │
│  │  - Neptune Service (graph database operations)           │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────┬───────────────┬──────────────┬──────────────┬───────────┘
       │               │              │              │
 ┌─────▼─────┐   ┌────▼─────┐  ┌─────▼──────┐  ┌───▼──────────┐
 │ Starburst │   │ DynamoDB │  │  Neptune   │  │ AI Services  │
 │  (Trino)  │   │(3 tables)│  │ Analytics  │  │ - Azure OAI  │
 │           │   │          │  │ (Graph DB) │  │   - GPT-5    │
 │           │   │          │  │  (Vectors) │  │   - Embed    │
 └───────────┘   └──────────┘  └────────────┘  └──────────────┘
```

### Data Stores

**DynamoDB Tables:**
1. **table_metadata** - Table-level metadata, search mode tags, and status tracking
2. **column_metadata** - Column-level metadata with enrichments and sample values
3. **table_relationships** - Discovered relationships between tables

**Neptune Analytics Graph:**
- **Table Nodes**: Table metadata with 2048-dim vector embeddings
- **Column Nodes**: Column metadata with 2048-dim vector embeddings
- **Relationships**: HAS_COLUMN edges connecting tables to columns
- **Properties**: search_mode tags, custom_instructions, metadata fields

## Features

###  Semantic Search (NEW!)

**Natural Language Querying:**
- Search tables and columns using plain English (e.g., "geographic data", "customer IDs")
- Powered by Azure OpenAI embeddings and Neptune Analytics vector similarity
- Cosine similarity with configurable thresholds (default: 0.40)

**Dual Search Modes:**
1. **Analytics Mode (Table-Level)**
   - Returns entire tables when relevant
   - Best for broad data exploration
   - Shows ALL columns from matched tables
   - Filters weak matches (requires 3+ columns OR 2+ with 55%+ avg similarity)
   - Top 1 table logic when relationships disabled

2. **Data Mining Mode (Column-Level)**
   - Returns individual columns that match the query
   - Best for finding specific attributes across tables
   - Granular column-level filtering
   - Returns only columns above threshold

**Smart Table Filtering:**
- Tables tagged as "Analytics" only appear in Analytics mode
- Tables tagged as "Data Mining" only appear in Data Mining mode
- NULL tags (Auto) appear in both modes
- Prevents irrelevant results across modes

**Search Features:**
- Similarity scores for tables and columns
- Relationship discovery between matched tables
- Real-time updates via Neptune graph sync
- Query validation and vagueness detection

###  Metadata Generation

**Automatic Table Enrichment:**
- Statistical analysis (min, max, avg, cardinality, null counts)
- Distinct sample values (up to 10, with fallback to random)
- Column type detection (identifier, dimension, measure, timestamp, detail)
- Semantic type detection (14+ types including geographic and coordinate types)
- Auto-detected search mode based on schema complexity

**Geographic Intelligence:**
- Country detection with ISO code support
- State/province detection (administrative level 2)
- City detection (administrative level 3)
- Latitude/longitude detection with range validation
- WKT and GeoJSON geometry detection

**AI-Powered Enrichment:**
- Human-readable alias generation using Azure OpenAI GPT-5
- Business-context descriptions with table context
- Combined generation (2x faster than separate calls)
- Fallback to rule-based generation for reliability

###  Relationship Discovery

**Intelligent Detection:**
- Azure OpenAI GPT-5 relationship analysis
- Three main relationship types: foreign_key, semantic, name_based
- Custom subtypes for granular classification
- Confidence scoring (0-1 scale)
- Column filtering: excludes geospatial and measure columns

**Background Processing:**
- Non-blocking detection (runs in separate thread)
- Real-time status updates in UI
- Can navigate away and return later

###  Configuration & Tagging

**Search Mode Tags:**
- Tag tables as "Analytics" or "Data Mining"
- Auto-detected based on schema (nested types → Data Mining, flat → Analytics)
- Configurable via MetadataViewer UI
- Syncs to both DynamoDB and Neptune

**Custom Instructions:**
- Add custom SQL examples or usage notes
- Stored in both DynamoDB and Neptune
- Displayed in search results

###  Frontend Features

**Semantic Search Page:**
- Natural language query input
- Mode selector (Analytics vs Data Mining)
- Similarity threshold slider
- Relationship toggle
- Results with similarity scores
- Table selector for quick filtering

**Metadata Viewer:**
- Beautiful card-based metadata display
- Search mode tag editor (syncs to Neptune)
- Custom instructions editor
- Inline editing for aliases, descriptions, column types
- Statistics modal for detailed column information
- Raw JSON view for debugging

**Enriched Tables Page:**
- Grid view of all tables with metadata
- Search mode badges
- Enrichment status tracking
- Neptune import status indicators

**Dual Navigation:**
- Browse Page: Sidebar navigation with focused single-table view
- Enriched Tables Page: Grid view with filtering

**UI/UX:**
- Dark/light mode with warm beige background (light mode)
- Searchable table selector with cascade (catalog → schema → table)
- Schema change alerts
- Responsive design for all devices

## Prerequisites

### Backend
- Python 3.10+
- Access to Starburst/Trino cluster
- AWS credentials with DynamoDB and Neptune Analytics access
- Azure OpenAI API access (GPT-5, text-embedding-3-small)

### Frontend
- Node.js 16+
- npm or yarn

## Quick Start

### 1. Clone the Repository

```bash
git clone https://main.gitlab.in.here.com/analytics-foundation/intern-projects/semantic-layer.git
cd semantic-layer
```

### 2. Setup Backend

```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration (see Configuration section below)

# Start API server
python -m app.main
```

Backend will run at `http://localhost:8000`

**API Documentation:** http://localhost:8000/docs

### 3. Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
echo "REACT_APP_API_URL=http://localhost:8000" > .env

# Start development server
npm start
```

Frontend will open at `http://localhost:3000`

### 4. Initial Setup

**Create DynamoDB Tables:**
```bash
cd backend
# Use AWS Console or CLI to create:
# - table_metadata (partition key: catalog_schema_table)
# - column_metadata (partition key: catalog_schema_table, sort key: column_name)
# - table_relationships (partition key: source_table, sort key: target_table)
```

**Create Neptune Analytics Graph:**
```bash
# Use AWS Console to create a Neptune Analytics graph
# Note the graph endpoint URL for .env configuration
```

**Generate Initial Metadata:**
```bash
cd backend
# Use the API endpoints or admin interface to generate metadata for tables
# POST /api/admin/generate-metadata
# This will enrich tables and import them to Neptune
```

## Configuration

### Backend Environment Variables (.env)

Create a `.env` file in the `backend/` directory with the following:

```env
# Starburst/Trino Configuration
STARBURST_HOST=your-starburst-host.com
STARBURST_PORT=443
STARBURST_CATALOG=here_explorer
STARBURST_SCHEMA=explorer_datasets
STARBURST_USER=your_username
STARBURST_PASSWORD=your_password
STARBURST_HTTP_SCHEME=https

# DynamoDB Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key  # Optional (uses default credentials if not provided)
AWS_SECRET_ACCESS_KEY=your_secret  # Optional
AWS_SESSION_TOKEN=your_token       # Optional
DYNAMODB_TABLE_METADATA_TABLE=table_metadata
DYNAMODB_COLUMN_METADATA_TABLE=column_metadata

# Neptune Analytics Configuration
NEPTUNE_ENDPOINT=g-xxxxx.us-east-1.neptune-graph.amazonaws.com
NEPTUNE_PORT=443
NEPTUNE_USE_IAM=True

# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-5
AZURE_OPENAI_API_VERSION=2024-12-01-preview
OPENAI_EMBEDDING_MODEL=text-embedding-3-small  # Deployment name in Azure

# Authentication
SESSION_SECRET_KEY=your-32-byte-secret-key-for-encryption

# AI Models (HuggingFace - Optional fallback)
ALIAS_MODEL=google/flan-t5-base
DESCRIPTION_MODEL=google/flan-t5-base
NER_MODEL=dslim/bert-base-NER
SENTENCE_TRANSFORMER_MODEL=sentence-transformers/all-MiniLM-L6-v2

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

### Frontend Environment Variables (.env)

Create a `.env` file in the `frontend/` directory with:

```env
REACT_APP_API_URL=http://localhost:8000
```

## Project Structure

```
semantic-layer/
├── backend/
│   ├── app/
│   │   ├── api/                    # API endpoints
│   │   │   ├── search.py          # Semantic search 
│   │   │   ├── tables.py          # Table listing and data
│   │   │   ├── metadata.py        # Metadata CRUD + Neptune sync
│   │   │   ├── relationships_api.py # Relationship queries
│   │   │   ├── enriched_tables_api.py # Enriched tables listing
│   │   │   ├── auth.py            # Authentication
│   │   │   └── admin.py           # Background tasks
│   │   ├── models/                # Pydantic models
│   │   │   ├── table.py           # Table metadata models
│   │   │   ├── column.py          # Column metadata models
│   │   │   └── api.py             # API request/response models
│   │   ├── services/              # Business logic
│   │   │   ├── embedding_service.py       # Azure OpenAI embeddings 
│   │   │   ├── neptune_service.py         # Neptune graph operations 
│   │   │   ├── metadata_generator.py      # Main orchestrator
│   │   │   ├── relationship_detector.py   # Azure OpenAI relationships
│   │   │   ├── relationship_tasks.py      # Background thread runner
│   │   │   ├── geographic_detector.py     # Geographic detection
│   │   │   ├── column_type_detector.py    # Column classification
│   │   │   ├── alias_generator.py         # AI alias generation
│   │   │   ├── azure_openai_generator.py  # Azure OpenAI wrapper 
│   │   │   ├── dynamodb.py                # DynamoDB operations
│   │   │   ├── dynamodb_relationships.py  # Relationship storage
│   │   │   ├── starburst.py               # Trino/Starburst client
│   │   │   ├── auth_service.py            # Authentication
│   │   │   └── schema_comparator.py       # Schema change detection
│   │   ├── middleware/            # Request middleware
│   │   ├── utils/                 # Utilities
│   │   ├── config.py              # Configuration management
│   │   └── main.py                # FastAPI app
│   ├── scripts/
│   │   ├── initial_setup.py               # Initial metadata generation
│   │   └── worker_schema_checker.py       # Schema change worker
│   ├── cleanup_stale_neptune_nodes.py     # Neptune cleanup utility (NEW!)
│   ├── verify_neptune_tags.py             # Neptune verification utility (NEW!)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── SemanticSearchPage.jsx    # Semantic search UI 
│   │   │   ├── MetadataViewer.jsx         # Metadata viewer + tag editor
│   │   │   ├── EnrichedTablesPage.jsx     # Table listing
│   │   │   ├── RelationshipsViewer.jsx    # Relationship display
│   │   │   └── ui/                        # Reusable UI components
│   │   ├── services/
│   │   │   └── api.js                     # Axios API client
│   │   └── App.jsx                        # Main app with routing
│   └── package.json
└── README.md
```

## Semantic Search Workflow

### 1. Embedding Generation
```
User Query: "POI ID columns"
    ↓
Azure OpenAI Embedding API
    ↓
1536-dimensional vector
    ↓
Padded to 2048 dimensions (Neptune requirement)
```

### 2. Neptune Vector Search
```
Analytics Mode:
  ├── Search Table Nodes (cosine similarity > threshold)
  ├── Search Column Nodes (cosine similarity > threshold)
  ├── Filter by search_mode tags (analytics or NULL)
  ├── Apply smart filtering (3+ cols OR 2+ with 55%+ avg)
  └── Return ALL columns from matched tables

Data Mining Mode:
  ├── Search Table Nodes (cosine similarity > threshold)
  ├── Search Column Nodes (cosine similarity > threshold)
  ├── Filter by search_mode tags (datamining or NULL)
  └── Return ONLY matched columns
```

### 3. Result Enrichment
```
Neptune Results
    ↓
Fetch full metadata from DynamoDB
    ↓
Calculate similarity scores (table or max column)
    ↓
Fetch relationships (if enabled)
    ↓
Return enriched results to frontend
```

## Neptune Management

### Verify Neptune Tags

Check if search_mode tags are correctly synced between DynamoDB and Neptune:

```bash
cd backend
python verify_neptune_tags.py
```

This will show:
- All tables in Neptune with their search_mode values
- Mismatched tags between DynamoDB and Neptune
- Stale nodes (in Neptune but marked as 'not_imported' in DynamoDB)

### Cleanup Stale Neptune Nodes

Remove Neptune nodes for tables marked as 'not_imported' in DynamoDB:

```bash
cd backend
# Dry run (preview what would be deleted)
python cleanup_stale_neptune_nodes.py

# Actually delete
python cleanup_stale_neptune_nodes.py --execute
```

This keeps Neptune in sync with DynamoDB and prevents stale data in search results.

## API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

**Semantic Search (NEW!)**
```
POST   /api/search/semantic                # Semantic search with NL queries
```

Request body:
```json
{
  "query": "POI ID columns",
  "threshold": 0.40,
  "mode": "analytics",
  "include_relationships": true
}
```

**Metadata Operations**
```
GET    /api/metadata/{catalog}/{schema}/{table}        # Get complete metadata
PATCH  /api/metadata/{catalog}/{schema}/{table}/config # Update search_mode/custom_instructions
POST   /api/refresh-metadata/{catalog}/{schema}/{table} # Regenerate metadata
```

**Tables & Catalogs**
```
GET    /api/catalogs                          # List all catalogs
GET    /api/enriched-tables                   # Get enriched tables list
GET    /api/table-data/{catalog}/{schema}/{table}  # Sample data
```

**Relationships**
```
GET    /api/relationships/{catalog}/{schema}/{table}  # All relationships
```

## Troubleshooting

### Neptune Issues

**Stale nodes appearing in search results**
- Run `python verify_neptune_tags.py` to check for stale nodes
- Run `python cleanup_stale_neptune_nodes.py --execute` to clean them up
- This happens when tables are deleted/reimported but Neptune nodes aren't cleaned

**Search mode tags not working**
- Tags must be synced to Neptune when changed in UI
- Use MetadataViewer (not EnrichedTablesPage) to update tags
- Changes trigger Neptune update automatically via PATCH endpoint

**Tables with wrong tags showing in search**
- Verify tags: `python verify_neptune_tags.py`
- Update tags in MetadataViewer UI
- If still wrong, check Neptune directly or reimport table

**Neptune connection errors**
- Verify NEPTUNE_ENDPOINT in .env
- Check AWS credentials have Neptune access
- Ensure Neptune graph is in same region as DynamoDB

### Backend Issues

**Can't connect to Starburst/Trino**
- Verify credentials in `.env` file
- Check network connectivity and firewall rules
- Ensure correct host, port, and scheme (http vs https)

**DynamoDB access denied**
- Check AWS credentials configuration
- Verify IAM permissions (GetItem, PutItem, Query, Scan)
- Ensure DynamoDB tables exist and are in the correct region

**Azure OpenAI errors**
- Verify API key is correct and active
- Check endpoint URL format
- Ensure deployment names match configured models (gpt-5, text-embedding-3-small)
- Monitor rate limits and quotas

**Embeddings generation slow**
- Azure OpenAI embeddings are called for each query
- Consider caching frequently used embeddings
- Check network latency to Azure endpoint

### Frontend Issues

**Semantic search not working**
- Check backend logs for Neptune connection errors
- Verify embeddings are being generated (check logs)
- Ensure threshold is not too high (try 0.3-0.4)

**Similarity scores showing 0.0%**
- This was fixed in recent updates
- Restart backend server to pick up latest code
- Tables found via column search now use max column similarity

**No results for valid queries**
- Tables may not be imported to Neptune
- Check neptune_import_status in table metadata
- Import tables using admin interface or API

## Performance Considerations

**Vector Similarity Search:**
- Neptune Analytics provides millisecond-latency vector search
- 2048-dimensional embeddings require padding from 1536-dim Azure embeddings
- Cosine similarity is computationally efficient

**Smart Filtering:**
- Analytics mode filters weak matches (< 3 columns with < 55% avg similarity)
- Reduces noise in results
- Configurable thresholds in code (lines 192-193 in search.py)

## Support

For questions or issues:
- Check API documentation at http://localhost:8000/docs
- Review Neptune utility outputs (`verify_neptune_tags.py`)
- Contact: shubham.singh@here.com

## Acknowledgments

- FastAPI for the excellent web framework
- Azure OpenAI for GPT-5 and embeddings
- AWS Neptune Analytics for vector similarity search
- HuggingFace for transformer models (fallback)
- TanStack Table for the React table component
- Tailwind CSS for utility-first styling
- Trino/Starburst for high-performance SQL engine

---
