"""
Bulk upsert all table and column embeddings into Neptune vector index
Pads 1536-dim embeddings to 2048 to match Neptune configuration
"""

import json
import requests
import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from app.config import settings
from typing import List


def execute_query(query):
    """Execute an OpenCypher query on Neptune Analytics"""
    endpoint = settings.neptune_endpoint
    base_url = f"https://{endpoint}"
    url = f"{base_url}/opencypher"

    body = {"query": query}
    body_json = json.dumps(body)
    headers = {'Content-Type': 'application/json'}

    session = boto3.Session()
    credentials = session.get_credentials()

    request = AWSRequest(method='POST', url=url, data=body_json, headers=headers)
    SigV4Auth(credentials, 'neptune-graph', 'us-east-1').add_auth(request)

    response = requests.post(url, data=body_json, headers=dict(request.headers), verify=True)

    if response.status_code != 200:
        print(f"HTTP {response.status_code}: {response.reason}")
        print(f"Response body: {response.text}")

    response.raise_for_status()

    return response.json().get('results', [])


def pad_embedding_to_2048(embedding_1536: List[float]) -> List[float]:
    """
    Pad a 1536-dimension embedding to 2048 dimensions with zeros

    Args:
        embedding_1536: List of 1536 floats

    Returns:
        List of 2048 floats (original + 512 zeros)
    """
    if len(embedding_1536) != 1536:
        raise ValueError(f"Expected 1536 dimensions, got {len(embedding_1536)}")

    # Pad with 512 zeros to reach 2048
    padding = [0.0] * (2048 - 1536)
    padded = embedding_1536 + padding

    return padded


def fetch_all_tables():
    """Fetch all tables with embeddings from Neptune"""
    query = """
    MATCH (t:Table)
    WHERE t.table_embedding_json IS NOT NULL
    RETURN t.name as table_name,
           t.table_embedding_json as embedding_json,
           id(t) as node_id
    ORDER BY t.name
    """

    results = execute_query(query)

    tables = []
    for row in results:
        embedding = json.loads(row['embedding_json'])
        tables.append({
            'name': row['table_name'],
            'node_id': row['node_id'],
            'embedding': embedding
        })

    return tables


def fetch_all_columns():
    """Fetch all columns with embeddings from Neptune"""
    query = """
    MATCH (c:Column)
    WHERE c.column_embedding_json IS NOT NULL
    RETURN c.full_name as full_name,
           c.column_name as column_name,
           c.column_embedding_json as embedding_json,
           id(c) as node_id
    ORDER BY c.full_name
    """

    results = execute_query(query)

    columns = []
    for row in results:
        embedding = json.loads(row['embedding_json'])
        columns.append({
            'name': row['full_name'] or row['column_name'],
            'node_id': row['node_id'],
            'embedding': embedding
        })

    return columns


def upsert_table_embedding(table_name: str, embedding_padded: List[float]) -> bool:
    """Upsert a single table embedding into vector index"""

    embedding_str = json.dumps(embedding_padded)

    query = f"""
    MATCH (t:Table {{name: '{table_name}'}})
    CALL neptune.algo.vectors.upsert(t, {embedding_str})
    YIELD node, embedding, success
    RETURN success
    """

    try:
        result = execute_query(query)
        return result[0]['success'] if result else False
    except Exception as e:
        print(f"      Error: {e}")
        return False


def upsert_column_embedding(column_full_name: str, embedding_padded: List[float]) -> bool:
    """Upsert a single column embedding into vector index"""

    embedding_str = json.dumps(embedding_padded)

    query = f"""
    MATCH (c:Column {{full_name: '{column_full_name}'}})
    CALL neptune.algo.vectors.upsert(c, {embedding_str})
    YIELD node, embedding, success
    RETURN success
    """

    try:
        result = execute_query(query)
        return result[0]['success'] if result else False
    except Exception as e:
        print(f"      Error: {e}")
        return False


def bulk_upsert_embeddings():
    """Main function to bulk upsert all embeddings"""

    print("="*80)
    print("BULK UPSERT EMBEDDINGS TO NEPTUNE VECTOR INDEX")
    print("="*80)
    print()

    # Step 1: Fetch all tables
    print("Step 1: Fetching tables with embeddings...")
    print("-" * 80)

    tables = fetch_all_tables()
    print(f"✅ Found {len(tables)} tables with embeddings")
    for table in tables:
        print(f"   - {table['name']}")
    print()

    # Step 2: Fetch all columns
    print("Step 2: Fetching columns with embeddings...")
    print("-" * 80)

    columns = fetch_all_columns()
    print(f"✅ Found {len(columns)} columns with embeddings")
    print(f"   (Showing first 5)")
    for col in columns[:5]:
        print(f"   - {col['name']}")
    print(f"   ... and {len(columns) - 5} more")
    print()

    total_to_upsert = len(tables) + len(columns)
    print(f"📊 Total embeddings to upsert: {total_to_upsert}")
    print()

    input("Press ENTER to start bulk upsert (Ctrl+C to cancel)...")
    print()

    # Step 3: Upsert table embeddings
    print("Step 3: Upserting table embeddings...")
    print("-" * 80)

    table_success = 0
    table_failed = 0

    for i, table in enumerate(tables, 1):
        print(f"   [{i}/{len(tables)}] {table['name'][:60]}...")

        # Pad embedding
        padded = pad_embedding_to_2048(table['embedding'])

        # Upsert
        success = upsert_table_embedding(table['name'], padded)

        if success:
            table_success += 1
            print(f"      ✅ Success")
        else:
            table_failed += 1
            print(f"      ❌ Failed")

    print()
    print(f"Table results: {table_success} success, {table_failed} failed")
    print()

    # Step 4: Upsert column embeddings
    print("Step 4: Upserting column embeddings...")
    print("-" * 80)

    column_success = 0
    column_failed = 0

    for i, column in enumerate(columns, 1):
        print(f"   [{i}/{len(columns)}] {column['name'][:60]}...")

        # Pad embedding
        padded = pad_embedding_to_2048(column['embedding'])

        # Upsert
        success = upsert_column_embedding(column['name'], padded)

        if success:
            column_success += 1
            print(f"      ✅ Success")
        else:
            column_failed += 1
            print(f"      ❌ Failed")

    print()
    print(f"Column results: {column_success} success, {column_failed} failed")
    print()

    # Step 5: Verify
    print("Step 5: Verifying vector index...")
    print("-" * 80)

    # Use a test vector to count indexed nodes
    test_embedding = [0.1] * 1536 + [0.0] * 512

    query = f"""
    CALL neptune.algo.vectors.topK.byEmbedding(
        {{ embedding: {json.dumps(test_embedding)}, topK: 100 }}
    )
    YIELD node, score
    RETURN count(node) as total_indexed
    """

    try:
        result = execute_query(query)
        total_indexed = result[0]['total_indexed'] if result else 0

        print(f"Nodes in vector index: {total_indexed}")
        print(f"Expected: {total_to_upsert}")
        print()

        if total_indexed == total_to_upsert:
            print(f"🎉 Perfect! All {total_to_upsert} embeddings are indexed!")
        elif total_indexed > total_to_upsert:
            print(f"⚠️  More nodes in index than expected (orphaned vectors?)")
        else:
            missing = total_to_upsert - total_indexed
            print(f"⚠️  {missing} embeddings missing from index")

    except Exception as e:
        print(f"❌ Failed to verify: {e}")

    print()
    print("="*80)
    print("BULK UPSERT COMPLETE")
    print("="*80)
    print()
    print(f"Summary:")
    print(f"  Tables upserted: {table_success}/{len(tables)}")
    print(f"  Columns upserted: {column_success}/{len(columns)}")
    print(f"  Total success: {table_success + column_success}/{total_to_upsert}")
    print()
    print("Next steps:")
    print("1. Run inspect_neptune_graph.py to verify")
    print("2. Test semantic search with a sample query")
    print("3. Update neptune_service.py to enable search methods")


if __name__ == "__main__":
    bulk_upsert_embeddings()
