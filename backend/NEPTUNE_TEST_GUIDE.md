# Neptune Analytics Integration - Test Guide

## What Changed

### 1. DNS Mapping (You Did This!)
- Added hostname mapping to Windows hosts file
- `10.96.112.27` → `g-el5ekbpdu0.us-east-1.neptune-graph.amazonaws.com`
- Allows code to use proper hostname instead of IP

### 2. Updated Configuration
- **config.py**: Now uses hostname instead of IP
- **neptune_service.py**: Simplified (no manual Host header, SSL verification enabled)
- **.env**: Updated endpoint to hostname

### 3. Enhanced Test Script
- **test_neptune_integration.py**:
  - Updated for 4-5 tables (add your 5th if needed)
  - Added fallback logic for missing relationships
  - Shows relationship detection status
  - Handles cases where detection hasn't run yet

---

## Neptune Relationship Detection - How It Works

**Important:** Neptune does NOT automatically find relationships!

```
┌─────────────────────────────────────────────────────────┐
│  Relationship Detection Flow                            │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. User generates metadata → Stored in DynamoDB        │
│                                                          │
│  2. GPT-5 analyzes tables → Finds relationships         │
│     (This is the AI/intelligence part)                  │
│                                                          │
│  3. Relationships stored in DynamoDB                    │
│                                                          │
│  4. THIS TEST SCRIPT reads from DynamoDB →              │
│     stores in Neptune as graph edges                    │
│                                                          │
│  Neptune = Storage + Query engine (not AI)              │
│  GPT-5 = Intelligence (finds relationships)             │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Your Tables

Currently configured for these 4 tables:
1. `here_explorer.explorer_datasets.carto_active_2022`
2. `here_explorer.explorer_datasets.carto_active_2023`
3. `here_explorer.explorer_datasets.carto_active_2024`
4. `here_explorer.explorer_datasets.carto_active_2025`

**To add your 5th table:**
Edit line 29 in `test_neptune_integration.py`:
```python
test_tables = [
    "here_explorer.explorer_datasets.carto_active_2022",
    "here_explorer.explorer_datasets.carto_active_2023",
    "here_explorer.explorer_datasets.carto_active_2024",
    "here_explorer.explorer_datasets.carto_active_2025",
    "here_explorer.explorer_datasets.YOUR_5TH_TABLE_HERE",  # Uncomment and fill in
]
```

---

## Fallback Logic for Missing Relationships

The script now handles all these cases:

| Status | What It Means | Script Behavior |
|--------|---------------|-----------------|
| `completed` | Detection ran, no relationships found | ℹ️  Informs you, continues with table/column nodes |
| `not_started` | Detection hasn't been triggered | 💡 Suggests running detection, continues |
| `in_progress` | Detection is running now | ⏳ Suggests waiting, continues |
| `failed` | Detection failed | ⚠️  Suggests checking logs, continues |

**Key point:** Even without relationships, the script will:
- ✅ Create table nodes in Neptune
- ✅ Create column nodes in Neptune
- ✅ Store embeddings for RAG
- ⚠️  Skip relationship edges (no connections between tables)

---

## Prerequisites

Before running the test:

1. **AWS Credentials** (run this first!):
   ```bash
   gimme-aws-creds
   # Select: content-analytics-index-portal-p (877525430744)
   ```

2. **Your Real .env File** (not the placeholder one):
   - Copy your actual `.env` with real Azure OpenAI credentials
   - Or update the placeholder `.env` with real values:
   ```env
   AZURE_OPENAI_API_KEY=your-actual-key
   AZURE_OPENAI_ENDPOINT=your-actual-endpoint
   STARBURST_HOST=your-actual-starburst-host
   STARBURST_USER=your-actual-username
   STARBURST_PASSWORD=your-actual-password
   ```

3. **Python Dependencies** (if not installed):
   ```bash
   pip install -r requirements.txt
   ```

---

## How to Run the Test

### Step 1: Verify DNS Mapping Works
```bash
ping g-el5ekbpdu0.us-east-1.neptune-graph.amazonaws.com
```
Should show: `[10.96.112.27]` (ping timeout is OK)

### Step 2: Test Neptune Connection
```bash
cd backend
python test_neptune_connection.py
```

Expected output:
```
================================================================================
NEPTUNE ANALYTICS CONNECTION TEST
================================================================================

Endpoint: g-el5ekbpdu0.us-east-1.neptune-graph.amazonaws.com
Port: 443
Base URL: https://g-el5ekbpdu0.us-east-1.neptune-graph.amazonaws.com

🔌 Testing connection with simple query...
✅ Connection successful!
   Query result: [{'test': 1}]
```

### Step 3: Run Full Integration Test
```bash
python test_neptune_integration.py
```

This will:
1. Fetch metadata from DynamoDB for each table
2. Generate embeddings using Azure OpenAI
3. Store table nodes in Neptune (with embeddings)
4. Store column nodes in Neptune (with embeddings)
5. Store relationship edges (if relationships exist)
6. Query Neptune to verify everything was stored

Expected runtime: **3-5 minutes** (depending on number of columns and relationships)

---

## What You'll See During Test

```
================================================================================
NEPTUNE INTEGRATION TEST
================================================================================

Testing with 4 tables:
  - here_explorer.explorer_datasets.carto_active_2022
  - here_explorer.explorer_datasets.carto_active_2023
  - here_explorer.explorer_datasets.carto_active_2024
  - here_explorer.explorer_datasets.carto_active_2025

🔌 Testing Neptune Analytics connection...
   Endpoint: g-el5ekbpdu0.us-east-1.neptune-graph.amazonaws.com
   Base URL: https://g-el5ekbpdu0.us-east-1.neptune-graph.amazonaws.com
   Using AWS SigV4 authentication

================================================================================
Processing Table 1/4: here_explorer.explorer_datasets.carto_active_2022
================================================================================

📥 Step 1: Fetching metadata from DynamoDB...
✅ Found metadata:
   - Row count: 1,234,567
   - Column count: 12
   - Columns: 12

🧠 Step 2: Generating embeddings with Azure OpenAI...
✅ Generated table embedding (1536 dimensions)
   Summary preview: Table: carto_active_2022 with 1,234,567 rows and 12 columns...

💾 Step 3: Storing table node in Neptune...
✅ Stored table node in Neptune

💾 Step 4: Storing ALL 12 column nodes...
   ✅ carto_id (identifier)
   ✅ carto_geometry_type (dimension)
   ... (10 more)
✅ Stored 12/12 column nodes

💾 Step 5: Storing relationships...
   Relationship detection status: completed
   Found 7 relationships
✅ Stored 7/7 relationships

✅ Successfully processed carto_active_2022

... (repeats for other 3 tables)

================================================================================
VERIFICATION: Querying Neptune
================================================================================

📊 Fetching all tables from Neptune...
✅ Found 4 tables in Neptune:
   - here_explorer.explorer_datasets.carto_active_2022
   - here_explorer.explorer_datasets.carto_active_2023
   - here_explorer.explorer_datasets.carto_active_2024
   - here_explorer.explorer_datasets.carto_active_2025

✅ Done!
```

---

## After Successful Test

Show your lead:
1. **Graph structure**: 4 table nodes + 48 column nodes + 21+ relationship edges
2. **Embeddings stored**: 52 embedding vectors (4 tables + 48 columns) for RAG
3. **Sample queries** you can now run:
   ```cypher
   // Find all tables in Neptune
   MATCH (t:Table) RETURN t.name

   // Find all columns in a table
   MATCH (t:Table {name: 'here_explorer.explorer_datasets.carto_active_2022'})-[:HAS_COLUMN]->(c:Column)
   RETURN c.column_name, c.column_type

   // Find all relationships from a table
   MATCH (source:Table {name: 'here_explorer.explorer_datasets.carto_active_2025'})-[r:RELATED_TO]->(target:Table)
   RETURN source.name, r.relationship_type, r.confidence, target.name

   // Vector similarity search (RAG!)
   MATCH (t:Table)
   WITH t, gds.similarity.cosine(t.table_embedding, $query_embedding) as similarity
   WHERE similarity >= 0.7
   RETURN t.name, t.table_summary, similarity
   ORDER BY similarity DESC
   LIMIT 5
   ```

---

## Troubleshooting

### Error: "NoCredentialsError"
**Fix:** Run `gimme-aws-creds` and select the correct AWS account

### Error: "Unable to locate credentials"
**Fix:** Make sure you're in the correct AWS account:
```bash
aws sts get-caller-identity
# Should show Account: 877525430744
```

### Error: "Connection refused" or "Name resolution failed"
**Fix:** Verify DNS mapping in hosts file:
```bash
ping g-el5ekbpdu0.us-east-1.neptune-graph.amazonaws.com
# Should show [10.96.112.27]
```

### Error: "Missing Authorization header"
**Fix:** AWS SigV4 auth failed. Check:
1. AWS credentials are valid
2. You have access to Neptune Analytics

### Warning: "No relationships found"
**Not an error!** The script will continue and create table/column nodes without relationship edges. You can:
1. Run relationship detection from the UI
2. Re-run the test script after detection completes

---

## Next Steps (After Test)

1. **Review graph data** with your lead
2. **Test RAG queries** (vector similarity search)
3. **Integrate into main pipeline** (if approved):
   - Update `metadata_generator.py` to also store in Neptune
   - Update relationship detection to also store in Neptune
4. **Build graph visualization** in frontend (optional)

---

## Notes

- **Neptune = Storage, GPT-5 = Intelligence**: Neptune doesn't find relationships, it stores what GPT-5 finds
- **Fallback logic**: Script continues even if relationships are missing
- **SSL enabled**: Using proper hostname allows certificate validation
- **Embeddings for RAG**: All tables and columns have embedding vectors for semantic search
