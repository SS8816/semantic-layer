# Metadata Explorer - Backend

Backend API for the Metadata Explorer project. Built with FastAPI, Trino/Starburst, DynamoDB, and HuggingFace Transformers.

## Features

- 🔍 **Automatic Metadata Generation**: Analyzes tables and generates rich metadata
- 🌍 **Geographic Detection**: Automatically detects country, city, and state columns
- 📍 **Lat/Lon Detection**: Identifies latitude and longitude columns
- 🤖 **AI-Powered Aliases**: Uses HuggingFace models to generate human-readable column aliases
- 📊 **Statistical Analysis**: Calculates min, max, avg, cardinality, null counts
- 🔄 **Schema Change Detection**: Daily worker script to detect schema changes
- 💾 **DynamoDB Storage**: Efficient metadata storage and retrieval

## Architecture

```
FastAPI Backend
├── Starburst/Trino (Data Source)
├── DynamoDB (Metadata Storage)
└── HuggingFace Models (AI Aliases & Descriptions)
```

## Prerequisites

- Python 3.10+
- Access to Starburst/Trino cluster
- AWS credentials with DynamoDB access
- DDL files for tables in `schema/` directory

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
# Starburst Configuration
STARBURST_HOST=your-starburst-host.com
STARBURST_PORT=443
STARBURST_CATALOG=your_catalog
STARBURST_SCHEMA=your_schema
STARBURST_USER=your_username
STARBURST_PASSWORD=your_password

# DynamoDB Configuration
AWS_REGION=us-east-1
DYNAMODB_TABLE_METADATA_TABLE=table_metadata
DYNAMODB_COLUMN_METADATA_TABLE=column_metadata
```

### 3. Create DynamoDB Tables

Create two DynamoDB tables:

**Table 1: `table_metadata`**
- Partition Key: `table_name` (String)

**Table 2: `column_metadata`**
- Partition Key: `table_name` (String)
- Sort Key: `column_name` (String)

### 4. Add Schema Files

Place your DDL files in the `schema/` directory:

```
schema/
├── table1.sql
├── table2.sql
└── ...
```

Each file should contain a `CREATE TABLE` statement for one table.

## Usage

### Running the API Server

```bash
# Development mode with auto-reload
python -m app.main

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Initial Metadata Generation

Generate metadata for all tables:

```bash
python scripts/initial_setup.py
```

Generate for specific table:

```bash
python scripts/initial_setup.py --table your_table_name
```

Force regeneration:

```bash
python scripts/initial_setup.py --force
```

List all available tables:

```bash
python scripts/initial_setup.py --list
```

### Schema Change Detection (Worker Script)

Run the worker script to check for schema changes:

```bash
python scripts/worker_schema_checker.py
```

Check specific table:

```bash
python scripts/worker_schema_checker.py --table your_table_name
```

**Schedule with cron (daily at 2 AM):**

```bash
0 2 * * * cd /path/to/backend && /path/to/python scripts/worker_schema_checker.py
```

## API Endpoints

### Tables

- `GET /api/tables` - Get list of all tables
- `GET /api/table-data/{table_name}?limit=1000` - Get sample data from table

### Metadata

- `GET /api/metadata/{table_name}` - Get complete metadata for a table
- `POST /api/refresh-metadata/{table_name}` - Refresh metadata for a table
- `PATCH /api/column/{table_name}/{column_name}/alias` - Update column aliases

### Admin

- `POST /api/admin/generate-metadata` - Generate metadata (background task)
- `GET /api/admin/task-status/{task_id}` - Check task status

### Example API Calls

```bash
# Get all tables
curl http://localhost:8000/api/tables

# Get metadata for a specific table
curl http://localhost:8000/api/metadata/navigable_road_attributes_2024

# Get sample data
curl http://localhost:8000/api/table-data/navigable_road_attributes_2024?limit=100

# Generate metadata for all tables
curl -X POST http://localhost:8000/api/admin/generate-metadata \
  -H "Content-Type: application/json" \
  -d '{"force_refresh": false}'

# Update column aliases
curl -X PATCH http://localhost:8000/api/column/my_table/my_column/alias \
  -H "Content-Type: application/json" \
  -d '{"aliases": ["New Alias 1", "New Alias 2"]}'
```

## Project Structure

```
backend/
├── app/
│   ├── api/              # API endpoints
│   │   ├── admin.py      # Admin endpoints
│   │   ├── metadata.py   # Metadata endpoints
│   │   └── tables.py     # Table endpoints
│   ├── models/           # Pydantic models
│   │   ├── api.py        # API request/response models
│   │   ├── column.py     # Column metadata models
│   │   └── table.py      # Table metadata models
│   ├── services/         # Business logic
│   │   ├── alias_generator.py      # HuggingFace alias generation
│   │   ├── dynamodb.py             # DynamoDB operations
│   │   ├── geographic_detector.py  # Geographic detection
│   │   ├── latlon_detector.py      # Lat/Lon detection
│   │   ├── metadata_generator.py   # Main orchestrator
│   │   ├── schema_comparator.py    # Schema comparison
│   │   └── starburst.py            # Starburst/Trino client
│   ├── utils/            # Utilities
│   │   ├── ddl_parser.py # DDL file parser
│   │   └── logger.py     # Logging configuration
│   ├── config.py         # Configuration management
│   └── main.py           # FastAPI app entry point
├── scripts/
│   ├── initial_setup.py           # Initial metadata generation
│   └── worker_schema_checker.py   # Schema change detection
├── schema/               # DDL files (*.sql)
└── requirements.txt      # Python dependencies
```

## Metadata Generation Process

1. **Parse DDL**: Extract schema from DDL files
2. **Query Statistics**: Run single query to get min/max/avg/cardinality/nulls
3. **Sample Data**: Get random 1000 rows for detection
4. **Geographic Detection**: Check if columns contain countries/cities/states
5. **Lat/Lon Detection**: Check if numeric columns are coordinates
6. **Alias Generation**: Use HuggingFace models to generate readable aliases
7. **Description Generation**: Use HuggingFace to generate column descriptions
8. **Store Metadata**: Save to DynamoDB

## HuggingFace Models Used

- **Alias Generation**: `google/flan-t5-base`
- **Description Generation**: `google/flan-t5-base`
- **NER (future)**: `dslim/bert-base-NER`

Models are loaded lazily on first use and cached in memory.

## Logging

Logs are written to:
- Console (colored output)
- `logs/app.log` (all logs)
- `logs/error.log` (errors only)

## Troubleshooting

### Can't connect to Starburst

- Check `STARBURST_HOST`, `STARBURST_PORT`, `STARBURST_USER`, `STARBURST_PASSWORD`
- Verify network connectivity
- Check if using correct `http` vs `https`

### DynamoDB access denied

- Verify AWS credentials are configured
- Check IAM permissions for DynamoDB
- Use `gimme-aws-creds` if using temporary credentials

### DDL parsing errors

- Ensure DDL files are valid SQL
- Check file encoding (should be UTF-8)
- Verify file names match table names

### HuggingFace model loading slow

- Models download on first use (~250MB each)
- Subsequent loads use cached models
- Consider using GPU for faster inference

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

```bash
# Format code
black app/ scripts/

# Lint
flake8 app/ scripts/

# Type checking
mypy app/ scripts/
```

## Deployment Considerations

- Use environment variables for sensitive configuration
- Consider using Redis for task tracking instead of in-memory dict
- Add authentication/authorization for production
- Use reverse proxy (nginx) for production
- Consider using Celery for background tasks
- Monitor DynamoDB read/write capacity
- Cache frequently accessed metadata

## License

Internal company tool - not for public distribution

## Support

For questions or issues, contact the development team.