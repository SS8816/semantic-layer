# Neptune Analytics Vector Index Configuration

## Current Status

**Storage:** ✅ Embeddings are stored as JSON strings in Neptune
- Property: `table_embedding_json` (1536 dimensions)
- Property: `column_embedding_json` (1536 dimensions)

**Vector Index:** ⚠️ Configured with WRONG dimension
- Current Neptune config: **2048 dimensions**
- Our embeddings: **1536 dimensions** (Azure OpenAI text-embedding-3-small)
- **Dimension mismatch causes vector queries to fail**

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

## The Dimension Mismatch Problem

**Discovery:** Running `aws neptune-graph get-graph` revealed:
```json
"vectorSearchConfiguration": {
    "dimension": 2048
}
```

**Issue:** Our embeddings are 1536 dimensions, but Neptune is configured for 2048.

**Impact:** Vector similarity queries fail with 400 errors because dimensions don't match.

**Evidence:**
```
Error: 400 Client Error: Bad Request
Function: vectorSimilarity(t.table_embedding_json, [0.1, 0.1, ...])
Reason: Dimension mismatch (provided: variable, expected: 2048)
```

## What Needs to be Configured

### Configuration Requirements

**Graph:** `cai-semantic-graph` (g-el5ekbpdu0)

**Current Config:** 2048 dimensions ❌
**Required Config:** 1536 dimensions ✅

**Why 1536?**
- Our embedding model: Azure OpenAI `text-embedding-3-small`
- Output dimensions: 1536 (fixed, cannot be changed)
- Already implemented and generating embeddings for all tables/columns
- Changing to a different embedding model would require:
  - Re-generating embeddings for all existing data
  - Higher cost (larger models are more expensive)
  - Slower performance

**Properties using embeddings:**
1. `table_embedding_json` - 1536 dimensions
2. `column_embedding_json` - 1536 dimensions

### How to Fix the Dimension Mismatch

**Option 1: AWS Console (Recommended)**
1. Navigate to Neptune Analytics → Graphs → cai-semantic-graph
2. Go to "Vector search configuration"
3. Update dimension from 2048 to 1536
4. Save changes

**Option 2: AWS CLI**

Update Neptune to use 1536 dimensions:
```bash
aws neptune-graph update-graph \
  --graph-identifier g-el5ekbpdu0 \
  --vector-search-configuration dimension=1536 \
  --region us-east-1
```

**Important Questions to Ask:**
1. Will this require downtime or impact existing queries?
2. Is there existing data that depends on 2048 dimensions?
3. Why was 2048 chosen originally?
4. Do we need to backup before changing this?

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

1. Can you update Neptune vector dimension from 2048 to 1536?
2. Why was 2048 dimensions chosen originally? Is there other data using it?
3. Will updating the dimension require downtime or impact existing queries?
4. What's the timeline for this configuration change?
5. Should we backup before making this change?

## Next Steps After Configuration

1. ✅ Verify vector index using `check_neptune_vector_index.py`
2. ✅ Enable vector similarity methods in `neptune_service.py`
3. ✅ Test semantic search with sample queries
4. ✅ Integrate into RAG pipeline for natural language queries
