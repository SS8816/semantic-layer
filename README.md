# Semantic Layer

A comprehensive semantic layer system for exploring, analyzing, and managing database table metadata with AI-powered insights and intelligent relationship discovery. Built with FastAPI, React, Starburst/Trino, DynamoDB, HuggingFace Transformers, and Azure OpenAI.

## Overview

The Semantic Layer automatically enriches database tables with rich metadata and discovers relationships between tables using advanced AI models. It provides a complete semantic understanding of your data landscape.

**Key Capabilities:**
- Automatically generate comprehensive metadata for database tables
- Detect geographic data (countries, cities, states, coordinates)
- Generate human-readable aliases and descriptions using AI
- Discover relationships between tables using Azure OpenAI GPT-5
- Track schema changes with monitoring
- Visualize table data and metadata in an intuitive UI
- Filter relationships to focus on SQL join-relevant columns
- Real-time status tracking for background processes

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     React Frontend                           │
│          (Browse, Enriched Tables, Metadata Viewer)          │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST API
┌──────────────────────────┴──────────────────────────────────┐
│                    FastAPI Backend                           │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Services:                                              │ │
│  │  - Metadata Generator (orchestrator)                   │ │
│  │  - Geographic Detector (countries/cities/states)       │ │
│  │  - Lat/Lon Detector (coordinate identification)        │ │
│  │  - Alias Generator (HuggingFace FLAN-T5)              │ │
│  │  - Relationship Detector (Azure OpenAI GPT-5)        │ │
│  │  - Column Type Detector (dimension/measure/etc.)       │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────┬──────────────────────┬────────────────┬──────────┘
           │                      │                │
    ┌──────▼──────┐       ┌──────▼──────┐  ┌─────▼──────────┐
    │  Starburst  │       │  DynamoDB   │  │  AI Services   │
    │   (Trino)   │       │  (3 tables) │  │  - HuggingFace │
    │             │       │             │  │  - Azure OpenAI│
    └─────────────┘       └─────────────┘  └────────────────┘
```

### DynamoDB Tables
1. **table_metadata** - Table-level metadata and relationship detection status
2. **column_metadata** - Column-level metadata with enrichments
3. **table_relationships** - Discovered relationships between tables

## Features

### Backend Features

**Metadata Generation**
- Automatic metadata generation for database tables
- Statistical analysis (min, max, avg, cardinality, null counts)
- Sample data extraction (1000 rows) for analysis
- Column type detection (identifier, dimension, measure, timestamp, detail)
- Semantic type detection (14+ types including geographic and coordinate types)

**Geographic Intelligence**
- Country detection with ISO code support
- State/province detection (administrative level 2)
- City detection (administrative level 3)
- Latitude/longitude detection with range validation
- WKT and GeoJSON geometry detection
- Geometry type classification

**AI-Powered Enrichment**
- Human-readable alias generation using HuggingFace FLAN-T5
- Business-context descriptions using AI
- Fallback to rule-based generation for reliability
- 40+ abbreviation expansions

**Relationship Discovery**
- Intelligent relationship detection using Azure OpenAI GPT-5
- Three main relationship types: foreign_key, semantic, name_based
- Custom subtypes for granular classification
- Confidence scoring (0-1 scale)
- Column filtering: excludes geospatial and measure columns from analysis
- Focuses on SQL join-relevant columns for RAG/SQL generation

**Schema Management**
- Schema change detection (new columns, removed columns, type changes)
- Status tracking (CURRENT vs SCHEMA_CHANGED)
- Daily monitoring with worker script

**Performance & Scalability**
- Non-blocking relationship detection (runs in separate thread)
- Batch processing for large column counts (15 columns per statistics query)
- Efficient DynamoDB queries with proper indexing
- Lazy-loading of AI models

**Authentication & Security**
- Token-based authentication with 3-day expiration
- Integration with corporate auth endpoint
- Request middleware for authorization
- Fernet encryption for tokens

### Frontend Features

**Dual Navigation**
- Browse Page: Sidebar navigation with focused single-table view
- Enriched Tables Page: Grid view of all tables with metadata

**Metadata Viewer**
- Beautiful card-based metadata display
- Inline editing for aliases, descriptions, column types, and semantic types
- Statistics modal for detailed column information
- Raw JSON view for debugging
- Collapsible sections for better organization

**Table Data Viewer**
- Sample data display (100 rows, expandable)
- Column type icons and visual indicators
- Responsive table with horizontal scrolling

**Relationship Viewer**
- Automatic relationship discovery display
- Grouped by relationship type (foreign_key, semantic, name_based)
- Confidence badges (high/medium/low)
- Expandable cards with reasoning
- Real-time updates when relationships complete

**Status Tracking**
- Real-time status banners for background processes
- Blue banner: "Finding Relationships" (can navigate away)
- Green banner: "Relationships Ready"
- Red banner: "Relationship Detection Failed"
- Automatic refresh when relationships complete

**UI/UX**
- Dark/light mode with warm beige background (light mode)
- Searchable table selector with cascade (catalog -> schema -> table)
- Schema change alerts
- Responsive design for all devices
- Clean, minimalistic interface

## Prerequisites

### Backend
- Python 3.10+
- Access to Starburst/Trino cluster
- AWS credentials with DynamoDB access
- Azure OpenAI API access (GPT-5)
- Corporate authentication endpoint (HERE)

### Frontend
- Node.js 16+
- npm or yarn

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd semantic-layer
```

### 2. Setup Backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration (see Configuration section)

# Create DynamoDB tables
# See backend/README.md for table creation scripts

# Start API server
python -m app.main
```

Backend will run at `http://localhost:8000`

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

## Project Structure

```
semantic-layer/
├── backend/
│   ├── app/
│   │   ├── api/                    # API endpoints (6 routers)
│   │   │   ├── tables.py          # Table listing and data
│   │   │   ├── metadata.py        # Metadata CRUD
│   │   │   ├── relationships_api.py # Relationship queries
│   │   │   ├── enriched_tables_api.py # Enriched tables listing
│   │   │   ├── auth.py            # Authentication
│   │   │   └── admin.py           # Background tasks
│   │   ├── models/                # Pydantic models
│   │   │   ├── table.py           # Table metadata models
│   │   │   ├── column.py          # Column metadata models
│   │   │   └── api.py             # API request/response models
│   │   ├── services/              # Business logic (11 services)
│   │   │   ├── metadata_generator.py      # Main orchestrator
│   │   │   ├── relationship_detector.py   # Azure OpenAI relationships
│   │   │   ├── relationship_tasks.py      # Background thread runner
│   │   │   ├── geographic_detector.py     # Geographic detection
│   │   │   ├── column_type_detector.py    # Column classification
│   │   │   ├── alias_generator.py         # AI alias generation
│   │   │   ├── dynamodb.py                # DynamoDB operations
│   │   │   ├── dynamodb_relationships.py  # Relationship storage
│   │   │   ├── starburst.py               # Trino/Starburst client
│   │   │   ├── auth_service.py            # Authentication
│   │   │   └── schema_comparator.py       # Schema change detection
│   │   ├── middleware/            # Request middleware
│   │   │   └── auth_middleware.py # Authentication middleware
│   │   ├── utils/                 # Utilities
│   │   │   ├── logger.py          # Loguru logging
│   │   │   ├── auth_utils.py      # Auth helpers
│   │   │   └── ddl_parser.py      # SQL DDL parsing
│   │   ├── config.py              # Configuration management
│   │   └── main.py                # FastAPI app
│   ├── scripts/
│   │   ├── initial_setup.py               # Initial metadata generation
│   │   └── worker_schema_checker.py       # Schema change worker
│   ├── schema/                    # DDL files
│   └── requirements.txt
├── frontend/
│   ├── public/
│   │   └── index.html             # HTML template (title: Semantic Layer)
│   ├── src/
│   │   ├── components/            # React components
│   │   │   ├── Login.jsx          # Authentication UI
│   │   │   ├── Header.jsx         # Top navigation
│   │   │   ├── LeftRail.jsx       # Collapsible sidebar
│   │   │   ├── TableSelector.jsx  # Catalog/Schema/Table selector
│   │   │   ├── TableDataViewer.jsx # Sample data display
│   │   │   ├── MetadataViewer.jsx  # Metadata display and editing
│   │   │   ├── RelationshipsViewer.jsx # Relationship display
│   │   │   ├── EnrichedTablesPage.jsx  # Table listing page
│   │   │   ├── MetadataEditModal.jsx   # Modal wrapper
│   │   │   ├── SchemaChangeAlert.jsx   # Schema change banner
│   │   │   └── ui/                # Reusable UI components
│   │   ├── contexts/
│   │   │   └── ThemeContext.jsx   # Dark/light mode
│   │   ├── services/
│   │   │   └── api.js             # Axios API client
│   │   ├── App.jsx                # Main app with routing
│   │   ├── index.js               # Entry point
│   │   └── index.css              # Tailwind configuration
│   └── package.json
└── README.md
```

## Configuration

### Backend Environment Variables (.env)

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
AWS_ACCESS_KEY_ID=your_access_key  # Optional (uses default credentials)
AWS_SECRET_ACCESS_KEY=your_secret  # Optional
AWS_SESSION_TOKEN=your_token       # Optional
DYNAMODB_TABLE_METADATA_TABLE=table_metadata
DYNAMODB_COLUMN_METADATA_TABLE=column_metadata

# Azure OpenAI Configuration (for relationship detection)
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-5
AZURE_OPENAI_API_VERSION=2024-12-01-preview

# Authentication
SESSION_SECRET_KEY=your-32-byte-secret-key-for-encryption

# AI Models (HuggingFace)
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

```env
REACT_APP_API_URL=http://localhost:8000
```

## Metadata Generation Process

The system follows a comprehensive pipeline to generate metadata:

### Phase 1: Metadata Generation (1-2 minutes)

1. **Schema Extraction**
   - Connect to Starburst/Trino
   - Execute DESCRIBE command to get column names and data types

2. **Statistics Collection**
   - Query row count for the table
   - Batch process columns (15 per query) for statistics:
     - MIN, MAX, AVG values
     - APPROX_DISTINCT for cardinality
     - NULL counts and percentages

3. **Sample Data Retrieval**
   - Extract 1000 random rows using ORDER BY RANDOM()
   - Used for pattern analysis and validation

4. **Column Analysis** (for each column)
   - **Type Detection**: Classify as identifier, dimension, measure, timestamp, or detail
   - **Semantic Detection**: Identify geographic types, coordinates, geometries
   - **Alias Generation**: Use HuggingFace FLAN-T5 to create human-readable names
   - **Description Generation**: Generate business-context descriptions with AI

5. **Storage**
   - Save table metadata to DynamoDB (table_metadata table)
   - Save column metadata to DynamoDB (column_metadata table)
   - Set relationship_detection_status to IN_PROGRESS

### Phase 2: Relationship Detection (3-5 minutes, runs in background)

1. **Column Filtering**
   - Exclude geospatial columns (latitude, longitude, wkt_geometry, geojson_geometry, geometry_type)
   - Exclude measure columns (aggregated values, metrics)
   - Focus on join-relevant columns (identifiers, dimensions)

2. **Comparison Processing**
   - Load metadata for the new table
   - Load metadata for all existing enriched tables
   - Process source columns in batches of 20
   - Compare against each target table individually

3. **AI Relationship Detection**
   - Call Azure OpenAI GPT-5 with column metadata
   - Provide context: column names, types, semantic types, descriptions, cardinality
   - Detect three main types:
     - **foreign_key**: Traditional referential integrity (subtypes: one_to_many, many_to_many, etc.)
     - **semantic**: Same business meaning (subtypes: geographic, temporal, hierarchical, etc.)
     - **name_based**: Similar naming patterns (subtypes: exact_match, partial_match, etc.)
   - Calculate confidence scores (0-1 scale)

4. **Filtering and Storage**
   - Filter relationships by confidence threshold (default: 0.6)
   - Store relationships to DynamoDB (table_relationships table)
   - Update relationship_detection_status to COMPLETED

### User Experience

- Users see metadata after Phase 1 completes (1-2 minutes)
- Blue status banner shows "Finding Relationships" during Phase 2
- Users can navigate away and return later
- Green banner appears when relationships are ready
- Relationships section auto-populates when detection completes

## Schema Change Detection

Monitor tables for schema changes with the worker script:

```bash
# Run manually
cd backend
python scripts/worker_schema_checker.py

# Schedule with cron (daily at 2 AM)
0 2 * * * cd /path/to/semantic-layer/backend && python scripts/worker_schema_checker.py
```

**Detects:**
- New columns added
- Columns removed
- Data type changes

**Status Updates:**
- Sets schema_status to SCHEMA_CHANGED
- Stores detailed change information
- Frontend displays visual alerts

## API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

**Authentication**
```
POST   /api/auth/login                        # Login with credentials
GET    /api/auth/me                           # Get current user
POST   /api/auth/logout                       # Logout
```

**Catalogs & Tables**
```
GET    /api/catalogs                          # List all catalogs
GET    /api/catalogs/{catalog}/schemas        # List schemas in catalog
GET    /api/catalogs/{catalog}/schemas/{schema}/tables  # List tables
GET    /api/tables                            # Get tables with metadata
GET    /api/enriched-tables                   # Get enriched tables list
GET    /api/table-data/{catalog}/{schema}/{table}?limit=1000  # Sample data
```

**Metadata Operations**
```
GET    /api/metadata/{catalog}/{schema}/{table}        # Get complete metadata
POST   /api/refresh-metadata/{catalog}/{schema}/{table} # Regenerate metadata
PATCH  /api/column/{catalog}/{schema}/{table}/{column}/alias  # Update aliases
PATCH  /api/column/{catalog}/{schema}/{table}/{column}/metadata  # Update metadata
```

**Relationships**
```
GET    /api/relationships/{catalog}/{schema}/{table}           # All relationships
GET    /api/relationships/{catalog}/{schema}/{table}/type/{type}  # Filter by type
GET    /api/relationships/{catalog}/{schema}/{table}/count     # Count by type
```

**Admin & Background Tasks**
```
POST   /api/admin/generate-metadata           # Start metadata generation
GET    /api/admin/task-status/{task_id}       # Check task progress
```

**Threading Considerations:**
The relationship detection system uses Python threading to run background tasks without blocking metadata generation. This works perfectly on EC2/ECS but may have issues on Lambda.


## Monitoring

### Backend Logs

**Log Files:**
- `logs/app.log` - All application logs (INFO and above)
- `logs/error.log` - Error logs only (ERROR and above)
- Console output - Real-time logging during development

**Log Format:**
- Timestamp, log level, module, function, line number
- Detailed context for debugging
- Exception tracebacks with full stack traces

### Key Metrics to Monitor

**Performance Metrics:**
- API response times (target: <500ms for most endpoints)
- Metadata generation duration (typical: 1-2 minutes per table)
- Relationship detection duration (typical: 3-5 minutes per table)
- DynamoDB read/write latency
- Starburst/Trino query execution time

**Resource Metrics:**
- CPU usage (threading may increase CPU load)
- Memory usage (AI models: ~250MB each)
- DynamoDB read/write capacity units
- API request rate
- Error rate and types

**Business Metrics:**
- Tables with enriched metadata
- Relationships discovered per table
- Schema change detection rate
- User activity and adoption

## Troubleshooting

### Backend Issues

**Can't connect to Starburst/Trino**
- Verify credentials in `.env` file
- Check network connectivity and firewall rules
- Test connection with `trino-cli`
- Ensure correct host, port, and scheme (http vs https)

**DynamoDB access denied**
- Check AWS credentials configuration
- Verify IAM permissions (GetItem, PutItem, Query, Scan)
- Use `gimme-aws-creds` for temporary credentials
- Ensure DynamoDB tables exist and are in the correct region

**Azure OpenAI errors**
- Verify API key is correct and active
- Check endpoint URL format
- Ensure deployment name matches configured model
- Monitor rate limits and quotas

**HuggingFace models slow or hanging**
- Models download on first use (~250MB each)
- Check internet connectivity for initial download
- Models are cached locally after first load
- Consider using GPU for faster inference (optional)

**Relationship detection not starting**
- Check logs for threading errors
- Verify relationship_detection_status in DynamoDB
- Ensure Azure OpenAI credentials are configured
- Check for background thread exceptions in logs

**Background threads not completing**
- Review deployment platform (EC2/ECS recommended, not Lambda)
- Check thread daemon status in logs
- Monitor for exceptions in relationship detection thread
- Verify DynamoDB write permissions

### Frontend Issues

**CORS errors**
- Ensure backend CORS settings include frontend URL
- Check `REACT_APP_API_URL` in frontend `.env`
- Verify backend is configured to accept requests from frontend domain

**API connection failed**
- Verify backend is running (check http://localhost:8000/docs)
- Check network connectivity and firewall rules
- Confirm `REACT_APP_API_URL` is correct
- Review browser console for detailed error messages

**Metadata not loading**
- Check browser console for API errors
- Verify authentication token is valid
- Try logging out and logging back in
- Check backend logs for error details

**Relationships not appearing**
- Wait for relationship detection to complete (3-5 minutes)
- Check relationship_detection_status via API
- Verify relationships were stored in DynamoDB
- Refresh the page to trigger component remount

**Status banner stuck on "Finding Relationships"**
- Check backend logs for relationship detection errors
- Verify Azure OpenAI is accessible and responding
- Monitor DynamoDB for status updates
- Check browser console for polling errors

## Testing

### Backend Tests

```bash
cd backend
pytest tests/
```

### Frontend Tests

```bash
cd frontend
npm test
```

## Contributing

This is an internal company tool. For contributions:

1. Create a feature branch from main
2. Make your changes with clear commit messages
3. Test thoroughly (unit tests, integration tests, manual testing)
4. Submit a pull request with detailed description
5. Ensure all tests pass and no regressions

## Support

For questions or issues:
- Check documentation in `/backend/README.md` and `/frontend/README.md`
- Review API documentation at http://localhost:8000/docs
- Contact shubham.singh@here.com
- File an issue in the repository

## Acknowledgments

- FastAPI for the excellent web framework
- HuggingFace for transformer models and FLAN-T5
- Azure OpenAI for GPT-5 relationship detection
- TanStack Table for the React table component
- Tailwind CSS for utility-first styling
- React community for inspiration and best practices
- Trino/Starburst for high-performance SQL engine

---

Built by shubham.singh@here.com
