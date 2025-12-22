# Vector Store Comparison Experiments

This directory contains experiments to compare different vector stores and chunking strategies for semantic search.

## Goal

Compare similarity scores between Neptune Analytics and other vector stores (FAISS, Chroma) to determine if lower similarity scores are due to:
- The vector store implementation
- The embedding model
- The text formatting/chunking strategy

## Vector Stores Tested

1. **FAISS** - Facebook's fast similarity search library
   - Local, in-memory
   - Industry standard for vector similarity
   - Uses cosine similarity (normalized inner product)

2. **Chroma** - Modern vector database
   - Popular for RAG applications
   - Easy metadata filtering
   - Uses L2 distance (converted to similarity)

3. **Neptune Analytics** (baseline comparison)
   - AWS graph database with vector index
   - Current production system

## Chunking Strategies

### 1. Baseline (Same as Neptune)
- Separate vectors for each table and each column
- Uses exact same text formatting as current Neptune implementation
- **Purpose:** Fair comparison to isolate if it's a vector store issue

### 2. Rich Column
- Enhanced column representation with more metadata
- Includes: semantic tags, more sample values, distinctness metrics, value ranges
- **Purpose:** Test if more context improves matching

### 3. Table + Columns Combined
- Single vector per table with all column information
- Captures full table context in one chunk
- **Purpose:** Test if combined context yields better results

### 4. Semantic Grouping
- Group columns by semantic type (location, business, identifiers, etc.)
- Creates thematic chunks per group
- **Purpose:** Test if semantic grouping improves relevance

## Files

- **`chunking_strategies.py`** - Implements 4 different chunking strategies
- **`vector_store_comparison.py`** - Main comparison script
- **`results/`** - Output directory for comparison results

## Usage

### Basic Comparison

```bash
cd backend
python experiments/vector_store_comparison.py \
  --stores faiss,chroma \
  --strategy baseline \
  --queries "tables with poi data" "location columns" "country code"
```

### Test All Strategies

```bash
python experiments/vector_store_comparison.py \
  --stores all \
  --strategy all \
  --queries "poi data" "location" "country"
```

### Limit Tables (for faster testing)

```bash
python experiments/vector_store_comparison.py \
  --stores faiss,chroma \
  --strategy baseline \
  --limit 5 \
  --queries "poi data"
```

### Custom Queries

```bash
python experiments/vector_store_comparison.py \
  --stores faiss \
  --strategy rich_column \
  --queries "tables with geographic data" "columns about addresses" "timestamp fields"
```

## Command Line Arguments

- `--stores` - Comma-separated list: `faiss`, `chroma`, `all` (default: `faiss,chroma`)
- `--strategy` - Strategy name or `all` (default: `baseline`)
  - Options: `baseline`, `rich_column`, `table_with_columns`, `semantic_grouping`, `all`
- `--queries` - List of test queries (default: `["tables with poi data", "location columns", "country code"]`)
- `--limit` - Limit number of tables from DynamoDB (default: None = all tables)
- `--top-k` - Number of results per query (default: 10)

## Output

### Console Output

The script prints a comparison table for each query:

```
Query: "tables with poi data" | Strategy: baseline
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Vector Store    Top Match ID                                       Score    Latency
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FAISS           here_explorer.explorer_datasets.core_poi_2025      0.6821   12.3ms
                here_explorer.explorer_datasets.poi_categories     0.6234
                here_explorer.explorer_datasets.poi_attributes     0.5892

Chroma          here_explorer.explorer_datasets.core_poi_2025      0.6543   18.7ms
                here_explorer.explorer_datasets.poi_categories     0.6102
                here_explorer.explorer_datasets.poi_attributes     0.5745
```

### JSON Results

Results are saved to `experiments/results/comparison_YYYYMMDD_HHMMSS.json`:

```json
{
  "baseline": {
    "strategy": "baseline",
    "description": "Exact match to current Neptune formatting",
    "num_documents": 150,
    "queries": {
      "tables with poi data": {
        "FAISS": [
          {
            "id": "here_explorer.explorer_datasets.core_poi_2025",
            "score": 0.6821,
            "metadata": {...},
            "latency_ms": 12.3
          }
        ],
        "Chroma": [...]
      }
    }
  }
}
```

## Installation

Install required dependencies:

```bash
pip install -r requirements.txt
```

This includes:
- `faiss-cpu==1.7.4` - FAISS library (CPU version)
- `chromadb==0.4.22` - Chroma vector database

## Interpreting Results

### Similarity Scores

- **Higher is better** (0-1 scale, closer to 1 = more similar)
- Compare scores across vector stores for the same query
- If FAISS/Chroma have significantly higher scores than Neptune, it suggests Neptune may have lower sensitivity

### Latency

- FAISS is typically fastest (in-memory, optimized)
- Chroma is slightly slower (additional overhead)
- Neptune (not in this test) has network latency

### Top-K Accuracy

- Check if the same documents appear in top results
- Order matters: is the most relevant document ranked #1?
- If different stores return different top results, it may indicate:
  - Different distance metrics
  - Index configuration differences
  - Quality issues with the data

## Next Steps

Based on comparison results:

1. **If FAISS/Chroma have higher scores:**
   - Neptune may need index tuning
   - Consider switching vector store
   - Investigate Neptune vector index configuration

2. **If all stores have low scores:**
   - Issue is with embeddings or text formatting
   - Try different chunking strategies
   - Consider different embedding model

3. **If a different strategy performs better:**
   - Update Neptune import to use that strategy
   - Re-import all data with new format
   - Test in production

## Troubleshooting

### "FAISS not installed"
```bash
pip install faiss-cpu
```

### "ChromaDB not installed"
```bash
pip install chromadb
```

### "No tables found in DynamoDB"
- Check `.env` file has correct DynamoDB table names
- Ensure tables have been onboarded
- Try `--limit 1` to test with subset

### Azure OpenAI errors
- Check `.env` has Azure OpenAI credentials
- Ensure API key is valid
- Check rate limits

## Contact

For questions or issues with these experiments, contact the team.
