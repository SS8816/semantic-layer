"""
Vector Store Comparison Experiment

Compare similarity scores and performance between different vector stores and chunking strategies.
Tests: FAISS, Chroma, and Neptune against various text formatting approaches.

Usage:
    python vector_store_comparison.py --stores faiss,chroma --strategy baseline
    python vector_store_comparison.py --stores all --strategy all --queries "poi data" "location columns"
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.services.dynamodb import dynamodb_service
from app.services.embedding_service import embedding_service
from experiments.chunking_strategies import get_strategy, STRATEGIES


# ============= Vector Store Implementations =============

class VectorStore:
    """Base class for vector stores"""

    def __init__(self, name: str):
        self.name = name
        self.dimension = 1536  # text-embedding-3-small or text-embedding-ada-002

    def index_documents(self, documents: List[Dict[str, Any]]):
        """
        Index documents with embeddings

        Args:
            documents: List of dicts with 'id', 'text', 'embedding', 'metadata'
        """
        raise NotImplementedError

    def search(self, query_embedding: List[float], k: int = 10) -> List[Dict[str, Any]]:
        """
        Search for similar documents

        Args:
            query_embedding: Query vector
            k: Number of results to return

        Returns:
            List of dicts with 'id', 'score', 'metadata'
        """
        raise NotImplementedError

    def clear(self):
        """Clear all indexed documents"""
        raise NotImplementedError


class FAISSVectorStore(VectorStore):
    """FAISS vector store implementation"""

    def __init__(self):
        super().__init__("FAISS")
        try:
            import faiss
            self.faiss = faiss
            self.index = None
            self.id_map = {}  # Map index position to document ID
            self.metadata_map = {}  # Map document ID to metadata
        except ImportError:
            raise ImportError("FAISS not installed. Run: pip install faiss-cpu")

    def index_documents(self, documents: List[Dict[str, Any]]):
        """Index documents into FAISS"""
        if not documents:
            return

        # Create index (using L2 distance, will convert to cosine similarity)
        # For cosine similarity with FAISS, we normalize vectors
        self.index = self.faiss.IndexFlatIP(self.dimension)  # Inner Product (for normalized vectors = cosine)

        # Prepare embeddings and mappings
        embeddings = []
        for idx, doc in enumerate(documents):
            embedding = np.array(doc['embedding'], dtype='float32')
            # Normalize for cosine similarity
            embedding = embedding / np.linalg.norm(embedding)
            embeddings.append(embedding)

            self.id_map[idx] = doc['id']
            self.metadata_map[doc['id']] = doc.get('metadata', {})

        # Add to index
        embeddings_array = np.vstack(embeddings)
        self.index.add(embeddings_array)

        print(f"✅ FAISS: Indexed {len(documents)} documents")

    def search(self, query_embedding: List[float], k: int = 10) -> List[Dict[str, Any]]:
        """Search FAISS index"""
        if self.index is None or self.index.ntotal == 0:
            return []

        # Normalize query for cosine similarity
        query = np.array([query_embedding], dtype='float32')
        query = query / np.linalg.norm(query)

        # Search
        scores, indices = self.index.search(query, min(k, self.index.ntotal))

        # Format results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for empty slots
                continue

            doc_id = self.id_map[idx]
            results.append({
                'id': doc_id,
                'score': float(score),  # Already cosine similarity (0-1)
                'metadata': self.metadata_map.get(doc_id, {})
            })

        return results

    def clear(self):
        """Clear FAISS index"""
        self.index = None
        self.id_map = {}
        self.metadata_map = {}


class ChromaVectorStore(VectorStore):
    """Chroma vector store implementation"""

    def __init__(self):
        super().__init__("Chroma")
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            # Create client with ephemeral in-memory storage
            self.client = chromadb.Client(ChromaSettings(
                is_persistent=False,
                anonymized_telemetry=False
            ))
            self.collection = None
            self.collection_name = f"comparison_{int(time.time())}"
        except ImportError:
            raise ImportError("ChromaDB not installed. Run: pip install chromadb")

    def index_documents(self, documents: List[Dict[str, Any]]):
        """Index documents into Chroma"""
        if not documents:
            return

        # Create or get collection
        if self.collection is not None:
            self.client.delete_collection(self.collection_name)

        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "Vector store comparison experiment"}
        )

        # Prepare data for Chroma
        ids = [doc['id'] for doc in documents]
        embeddings = [doc['embedding'] for doc in documents]
        documents_text = [doc['text'] for doc in documents]
        metadatas = [doc.get('metadata', {}) for doc in documents]

        # Add to collection
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents_text,
            metadatas=metadatas
        )

        print(f"✅ Chroma: Indexed {len(documents)} documents")

    def search(self, query_embedding: List[float], k: int = 10) -> List[Dict[str, Any]]:
        """Search Chroma collection"""
        if self.collection is None:
            return []

        # Query collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k
        )

        # Format results (Chroma returns distances, we convert to similarity)
        formatted_results = []
        if results['ids'] and len(results['ids']) > 0:
            for idx, doc_id in enumerate(results['ids'][0]):
                # Chroma uses L2 distance by default, convert to similarity
                distance = results['distances'][0][idx] if 'distances' in results else 0
                similarity = 1 / (1 + distance)  # Convert distance to similarity score

                formatted_results.append({
                    'id': doc_id,
                    'score': float(similarity),
                    'metadata': results['metadatas'][0][idx] if 'metadatas' in results else {}
                })

        return formatted_results

    def clear(self):
        """Clear Chroma collection"""
        if self.collection is not None:
            self.client.delete_collection(self.collection_name)
            self.collection = None


# ============= Data Loading =============

def load_tables_from_dynamodb(limit: int = None) -> List[Dict[str, Any]]:
    """
    Load table and column metadata from DynamoDB

    Args:
        limit: Optional limit on number of tables to load

    Returns:
        List of dicts with 'table_metadata' and 'columns'
    """
    print("📥 Loading data from DynamoDB...")

    # Get all tables (returns TableSummary objects)
    table_summaries = dynamodb_service.get_all_tables()

    if limit:
        table_summaries = table_summaries[:limit]

    print(f"   Found {len(table_summaries)} tables")

    # Load full metadata and columns for each table
    tables_data = []
    for table_summary in table_summaries:
        catalog_schema_table = table_summary.catalog_schema_table

        # Get full table metadata
        table_metadata = dynamodb_service.get_table_metadata(catalog_schema_table)
        if not table_metadata:
            print(f"   ⚠️  Skipping {catalog_schema_table} - no metadata found")
            continue

        # Convert to dict
        if hasattr(table_metadata, 'dict'):
            table_dict = table_metadata.dict()
        else:
            table_dict = table_metadata

        # Get columns
        columns = dynamodb_service.get_all_columns_for_table(catalog_schema_table)
        if not columns:
            print(f"   ⚠️  Skipping {catalog_schema_table} - no columns found")
            continue

        columns_dicts = []
        for col in columns:
            if hasattr(col, 'dict'):
                columns_dicts.append(col.dict())
            else:
                columns_dicts.append(col)

        tables_data.append({
            'table_metadata': table_dict,
            'columns': columns_dicts
        })

    print(f"✅ Loaded {len(tables_data)} tables with columns")
    return tables_data


def generate_chunks_and_embeddings(
    tables_data: List[Dict[str, Any]],
    strategy_name: str
) -> List[Dict[str, Any]]:
    """
    Generate chunks and embeddings for all tables using a specific strategy

    Args:
        tables_data: List of table data from DynamoDB
        strategy_name: Name of chunking strategy to use

    Returns:
        List of documents with embeddings ready for indexing
    """
    print(f"\n📝 Generating chunks using '{strategy_name}' strategy...")

    strategy = get_strategy(strategy_name)
    all_documents = []

    for table_data in tables_data:
        table_metadata = table_data['table_metadata']
        columns = table_data['columns']

        # Generate chunks using strategy
        chunks = strategy.get_chunks(table_metadata, columns)

        # Generate embeddings for each chunk
        for chunk in chunks:
            try:
                # Generate embedding
                embedding = embedding_service.generate_embedding(chunk['text'])

                all_documents.append({
                    'id': chunk['id'],
                    'text': chunk['text'],
                    'embedding': embedding,
                    'type': chunk['type'],
                    'metadata': chunk['metadata']
                })

            except Exception as e:
                print(f"   ⚠️  Failed to generate embedding for {chunk['id']}: {e}")
                continue

    print(f"✅ Generated {len(all_documents)} documents with embeddings")
    return all_documents


# ============= Query Testing =============

def run_query_test(
    query: str,
    vector_stores: List[VectorStore],
    k: int = 10
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Run a query against all vector stores

    Args:
        query: Natural language query
        vector_stores: List of vector stores to query
        k: Number of results to return

    Returns:
        Dict mapping store name to results
    """
    # Generate query embedding
    query_embedding = embedding_service.generate_embedding(query)

    results = {}
    for store in vector_stores:
        start_time = time.time()
        store_results = store.search(query_embedding, k=k)
        latency_ms = (time.time() - start_time) * 1000

        # Add latency to results
        for result in store_results:
            result['latency_ms'] = latency_ms

        results[store.name] = store_results

    return results


# ============= Results Analysis =============

def print_comparison_table(query: str, results_by_store: Dict[str, List[Dict[str, Any]]], strategy_name: str):
    """Print comparison table for query results"""
    print(f"\n{'=' * 120}")
    print(f"Query: \"{query}\" | Strategy: {strategy_name}")
    print(f"{'=' * 120}")
    print(f"{'Vector Store':<15} {'Top Match ID':<50} {'Score':<8} {'Latency':<10}")
    print(f"{'-' * 120}")

    for store_name, results in results_by_store.items():
        if results:
            top_result = results[0]
            print(f"{store_name:<15} {top_result['id']:<50} {top_result['score']:<8.4f} {top_result.get('latency_ms', 0):<10.1f}ms")

            # Show top 5 results
            for result in results[1:5]:
                print(f"{'':15} {result['id']:<50} {result['score']:<8.4f}")
        else:
            print(f"{store_name:<15} {'No results':<50} {'N/A':<8} {'N/A':<10}")

    print(f"{'=' * 120}\n")


def save_results(results: Dict[str, Any], output_dir: str = "experiments/results"):
    """Save comparison results to JSON file"""
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"comparison_{timestamp}.json")

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Results saved to: {output_file}")


# ============= Main =============

def main():
    parser = argparse.ArgumentParser(description="Compare vector stores and chunking strategies")
    parser.add_argument(
        '--stores',
        type=str,
        default='faiss,chroma',
        help='Comma-separated list of stores to test (faiss,chroma,all)'
    )
    parser.add_argument(
        '--strategy',
        type=str,
        default='baseline',
        help=f'Chunking strategy to use: {", ".join(STRATEGIES.keys())}, or "all"'
    )
    parser.add_argument(
        '--queries',
        type=str,
        nargs='+',
        default=['tables with poi data', 'location columns', 'country code'],
        help='List of test queries to run'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of tables to load from DynamoDB'
    )
    parser.add_argument(
        '--top-k',
        type=int,
        default=10,
        help='Number of results to return per query'
    )

    args = parser.parse_args()

    # Parse stores
    if args.stores.lower() == 'all':
        store_names = ['faiss', 'chroma']
    else:
        store_names = [s.strip().lower() for s in args.stores.split(',')]

    # Parse strategies
    if args.strategy.lower() == 'all':
        strategy_names = list(STRATEGIES.keys())
    else:
        strategy_names = [args.strategy.lower()]

    print("🚀 Vector Store Comparison Experiment")
    print(f"   Stores: {', '.join(store_names)}")
    print(f"   Strategies: {', '.join(strategy_names)}")
    print(f"   Queries: {len(args.queries)}")
    print()

    # Load data from DynamoDB (once)
    tables_data = load_tables_from_dynamodb(limit=args.limit)

    if not tables_data:
        print("❌ No tables found in DynamoDB")
        return

    # Run comparison for each strategy
    all_results = {}

    for strategy_name in strategy_names:
        print(f"\n{'#' * 120}")
        print(f"# Testing Strategy: {strategy_name}")
        print(f"# {STRATEGIES[strategy_name].description}")
        print(f"{'#' * 120}")

        # Generate chunks and embeddings
        documents = generate_chunks_and_embeddings(tables_data, strategy_name)

        if not documents:
            print(f"❌ No documents generated for strategy '{strategy_name}'")
            continue

        # Initialize vector stores
        vector_stores = []
        for store_name in store_names:
            if store_name == 'faiss':
                store = FAISSVectorStore()
            elif store_name == 'chroma':
                store = ChromaVectorStore()
            else:
                print(f"⚠️  Unknown store: {store_name}")
                continue

            # Index documents
            print(f"\n📊 Indexing into {store.name}...")
            store.index_documents(documents)
            vector_stores.append(store)

        # Run test queries
        strategy_results = {
            'strategy': strategy_name,
            'description': STRATEGIES[strategy_name].description,
            'num_documents': len(documents),
            'queries': {}
        }

        for query in args.queries:
            print(f"\n🔍 Query: \"{query}\"")

            results_by_store = run_query_test(query, vector_stores, k=args.top_k)
            print_comparison_table(query, results_by_store, strategy_name)

            strategy_results['queries'][query] = results_by_store

        all_results[strategy_name] = strategy_results

        # Cleanup stores
        for store in vector_stores:
            store.clear()

    # Save results
    save_results(all_results)

    print("\n✅ Comparison complete!")


if __name__ == '__main__':
    main()
