# Neptune Analytics Vector Index Configuration

## Current Status

**Storage:** ✅ Embeddings are stored as JSON strings in Neptune
- Property: `table_embedding_json` (1536 dimensions)
- Property: `column_embedding_json` (1536 dimensions)

**Vector Index:** ❌ Not configured yet

## Why We Need Vector Index

Without a vector index, we cannot perform fast semantic similarity search:

```python
# What we want to do:
"Find tables similar to: 'customer revenue data'"
  → Calculate embedding for query
  → Find top 10 most similar tables in Neptune
  → Return results in < 100ms
```

Currently, this would require:
1. Fetching ALL table embeddings from Neptune
2. Parsing JSON strings in Python
3. Calculating similarity for each one
4. Sorting and returning top K

For 600 tables, this is **too slow** for real-time queries.

## What Needs to be Configured

### Configuration Requirements

**Graph:** `cai-semantic-graph` (g-el5ekbpdu0)

**Vector Indexes Needed:**

1. **Table Embeddings:**
   - Property name: `table_embedding_json`
   - Data format: JSON array string (e.g., "[0.123, -0.456, ...]")
   - Dimensions: 1536
   - Similarity metric: cosine
   - Use case: Find similar tables for RAG queries

2. **Column Embeddings:**
   - Property name: `column_embedding_json`
   - Data format: JSON array string
   - Dimensions: 1536
   - Similarity metric: cosine
   - Use case: Find similar columns for query generation

### How to Configure

**Option 1: AWS Console**
1. Navigate to Neptune Analytics → Graphs → cai-semantic-graph
2. Go to "Vector search configuration"
3. Add vector index for `table_embedding_json`
4. Add vector index for `column_embedding_json`

**Option 2: AWS CLI**
```bash
aws neptune-graph update-graph \
  --graph-identifier g-el5ekbpdu0 \
  --vector-search-configuration '{
    "dimension": 1536,
    "properties": ["table_embedding_json", "column_embedding_json"]
  }' \
  --region us-east-1
```

**Option 3: CloudFormation/Terraform**
Add vector search configuration to infrastructure-as-code.

## Verification

After configuration, run this script to verify:

```bash
python check_neptune_vector_index.py
```

This will test if the `vectorSimilarity()` function works in OpenCypher queries.

## Impact on Code

### Before Vector Index:
```python
def search_similar_tables(self, query_embedding):
    # Currently returns empty list
    logger.warning("Vector search not configured")
    return []
```

### After Vector Index:
```python
def search_similar_tables(self, query_embedding, top_k=5):
    query = """
    MATCH (t:Table)
    WHERE vectorSimilarity(t.table_embedding_json, $query_vector) > 0.7
    RETURN t.name,
           t.table_summary,
           vectorSimilarity(t.table_embedding_json, $query_vector) as similarity
    ORDER BY similarity DESC
    LIMIT $top_k
    """

    return self.execute_query(query, {
        'query_vector': query_embedding,
        'top_k': top_k
    })
```

## Storage Format Note

**Important:** Even with vector index configured, embeddings must still be stored as **JSON strings** (not raw arrays). This is because:

1. Neptune Analytics doesn't support large array properties natively
2. The vector index works on top of the string storage format
3. Neptune parses the JSON string into a vector for indexing

The JSON string format is **NOT a limitation** - it's the correct storage format for Neptune Analytics vector indexes.

## Questions for Your Lead

1. Can you configure vector indexes in Neptune Analytics for our graph?
2. What's the timeline for this configuration?
3. Do we need any special permissions or approvals?
4. Should we use AWS Console, CLI, or IaC for this?

## Next Steps After Configuration

1. ✅ Verify vector index using `check_neptune_vector_index.py`
2. ✅ Enable vector similarity methods in `neptune_service.py`
3. ✅ Test semantic search with sample queries
4. ✅ Integrate into RAG pipeline for natural language queries
