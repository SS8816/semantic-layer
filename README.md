# Metadata Explorer

A comprehensive metadata management system for exploring, analyzing, and managing database table metadata with AI-powered insights. Built with FastAPI, React, Starburst/Trino, DynamoDB, and HuggingFace Transformers.

## 🎯 Overview

Metadata Explorer helps you:
- **Automatically generate rich metadata** for database tables
- **Detect geographic data** (countries, cities, states)
- **Identify coordinates** (latitude/longitude columns)
- **Generate human-readable aliases** using AI
- **Track schema changes** with daily monitoring
- **Visualize table data** and metadata in a clean UI

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     React Frontend                           │
│              (Table Explorer & Metadata Viewer)              │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST API
┌──────────────────────────┴──────────────────────────────────┐
│                    FastAPI Backend                           │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Services: Metadata Generator, Geographic Detector,    │ │
│  │  Lat/Lon Detector, Alias Generator (HuggingFace)      │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────┬──────────────────────┬────────────────┬──────────┘
           │                      │                │
    ┌──────▼──────┐       ┌──────▼──────┐  ┌─────▼──────┐
    │  Starburst  │       │  DynamoDB   │  │ HuggingFace│
    │   (Trino)   │       │  (Metadata) │  │   Models   │
    └─────────────┘       └─────────────┘  └────────────┘
```

## 🚀 Features

### Backend Features
- ✅ **Automatic Metadata Generation**: Analyzes 232 tables and generates comprehensive metadata
- 🌍 **Geographic Detection**: Identifies country, city, and state columns
- 📍 **Coordinate Detection**: Detects latitude and longitude columns
- 🤖 **AI-Powered Aliases**: Uses FLAN-T5 to generate human-readable column names
- 📊 **Statistical Analysis**: Computes min, max, avg, cardinality, null counts
- 🔄 **Schema Change Detection**: Daily worker script monitors schema changes
- 💾 **DynamoDB Storage**: Efficient metadata storage and retrieval
- 📝 **Comprehensive Logging**: Detailed logs for debugging and monitoring

### Frontend Features
- 🔍 **Searchable Table Selector**: 232 tables, instantly searchable
- 📋 **Table Data Viewer**: View sample data with 100 rows
- 📊 **Metadata Viewer**: Beautiful card-based metadata display
- ✏️ **Inline Alias Editing**: Update aliases directly in the UI
- 🔔 **Schema Change Alerts**: Visual alerts when schemas change
- 🎨 **Clean, Minimalistic UI**: Functional and easy to use
- 📱 **Responsive Design**: Works on all devices

## 📋 Prerequisites

### Backend
- Python 3.10+
- Access to Starburst/Trino cluster
- AWS credentials with DynamoDB access
- DDL files for all 232 tables

### Frontend
- Node.js 16+
- npm or yarn

## 🛠️ Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd metadata-explorer
```

### 2. Setup Backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Create DynamoDB tables (see backend/README.md)

# Generate initial metadata
python scripts/initial_setup.py

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

## 📁 Project Structure

```
metadata-explorer/
├── backend/
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   ├── models/           # Pydantic models
│   │   ├── services/         # Business logic
│   │   ├── utils/            # Utilities
│   │   ├── config.py         # Configuration
│   │   └── main.py           # FastAPI app
│   ├── scripts/
│   │   ├── initial_setup.py          # Initial metadata generation
│   │   └── worker_schema_checker.py  # Schema change detection
│   ├── schema/               # DDL files (232 .sql files)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── services/         # API client
│   │   ├── App.jsx           # Main app
│   │   └── index.js          # Entry point
│   └── package.json
└── README.md
```

## 🔧 Configuration

### Backend (.env)

```env
# Starburst Configuration
STARBURST_HOST=your-starburst-host.com
STARBURST_CATALOG=your_catalog
STARBURST_SCHEMA=your_schema
STARBURST_USER=your_username
STARBURST_PASSWORD=your_password

# DynamoDB
AWS_REGION=us-east-1
DYNAMODB_TABLE_METADATA_TABLE=table_metadata
DYNAMODB_COLUMN_METADATA_TABLE=column_metadata

# HuggingFace Models
ALIAS_MODEL=google/flan-t5-base
DESCRIPTION_MODEL=google/flan-t5-base
```

### Frontend (.env)

```env
REACT_APP_API_URL=http://localhost:8000
```

## 📊 Metadata Generation Process

1. **Parse DDL**: Extract schema from DDL files
2. **Query Statistics**: Run aggregate queries (min/max/avg/cardinality)
3. **Sample Data**: Get random 1000 rows for analysis
4. **Geographic Detection**: Check for countries/cities/states
5. **Lat/Lon Detection**: Identify coordinate columns
6. **AI Generation**: Generate aliases and descriptions using FLAN-T5
7. **Store Metadata**: Save to DynamoDB

## 🔄 Schema Change Detection

Daily worker script checks all tables for schema changes:

```bash
# Run manually
python scripts/worker_schema_checker.py

# Schedule with cron (daily at 2 AM)
0 2 * * * cd /path/to/backend && python scripts/worker_schema_checker.py
```

Detects:
- New columns
- Removed columns
- Data type changes

## 📖 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

```
GET  /api/tables                           # Get all tables
GET  /api/table-data/{table_name}          # Get sample data
GET  /api/metadata/{table_name}            # Get metadata
POST /api/refresh-metadata/{table_name}    # Refresh metadata
PATCH /api/column/{table}/{column}/alias   # Update aliases
POST /api/admin/generate-metadata          # Generate metadata
```

## 🧪 Testing

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

## 🚀 Deployment

### Backend Deployment

1. **Containerize with Docker**:
```dockerfile
FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-m", "app.main"]
```

2. **Deploy to AWS ECS/EC2**
3. **Configure environment variables**
4. **Setup DynamoDB tables**
5. **Schedule worker script**

### Frontend Deployment

1. **Build production bundle**:
```bash
npm run build
```

2. **Deploy to S3 + CloudFront** or any static hosting
3. **Configure API URL**

## 📈 Monitoring

### Backend Logs

Logs are written to:
- `logs/app.log` - All logs
- `logs/error.log` - Errors only
- Console output

### Metrics to Monitor

- API response times
- Metadata generation duration
- DynamoDB read/write capacity
- HuggingFace model inference time
- Schema change detection frequency

## 🐛 Troubleshooting

### Backend Issues

**Can't connect to Starburst**
- Check credentials in `.env`
- Verify network connectivity
- Test with `trino-cli`

**DynamoDB access denied**
- Check AWS credentials
- Verify IAM permissions
- Use `gimme-aws-creds` for temporary credentials

**HuggingFace models slow**
- Models download on first use (~250MB each)
- Consider using GPU for faster inference
- Models are cached after first load

### Frontend Issues

**CORS errors**
- Ensure backend CORS settings include frontend URL
- Check `REACT_APP_API_URL`

**API connection failed**
- Verify backend is running
- Check network/firewall
- Confirm API URL is correct

## 🤝 Contributing

This is an internal company tool. For contributions:

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## 📝 License

Internal company tool - not for public distribution

## 👥 Team

Developed by the Data Platform Team

## 📞 Support

For questions or issues:
- Check documentation in `/backend/README.md` and `/frontend/README.md`
- Contact the development team
- File an issue in the repository

## 🎯 Roadmap

### Phase 1 (Current)
- ✅ Metadata generation for 232 tables
- ✅ Geographic and coordinate detection
- ✅ AI-powered alias generation
- ✅ Schema change detection
- ✅ Web UI for exploration

### Phase 2 (Future)
- 🔲 RAG (Retrieval Augmented Generation) integration
- 🔲 LangChain orchestration
- 🔲 Natural language queries
- 🔲 Advanced analytics and insights
- 🔲 Metadata comparison and history
- 🔲 Bulk operations
- 🔲 User authentication and permissions

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- HuggingFace for transformer models
- TanStack Table for the table component
- React community for inspiration

---

**Built with ❤️ by the Data Platform Team**