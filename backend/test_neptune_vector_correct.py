"""
Test Neptune Analytics vector search using correct neptune.algo.vectors functions
"""

import json
import requests
import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from app.config import settings


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


def test_neptune_vectors():
    """Test Neptune's vector algorithms"""

    print("="*80)
    print("NEPTUNE ANALYTICS VECTOR SEARCH - CORRECT SYNTAX")
    print("="*80)
    print()

    # Step 1: Get a real embedding from Neptune
    print("Step 1: Fetching a table with embedding from Neptune...")
    print("-" * 80)

    query = """
    MATCH (t:Table)
    WHERE t.table_embedding_json IS NOT NULL
    RETURN t.name as table_name,
           t.table_embedding_json as embedding_json,
           t.embedding_dimensions as dimensions
    LIMIT 1
    """

    try:
        result = execute_query(query)

        if not result:
            print("❌ No tables with embeddings found")
            return False

        table_name = result[0]['table_name']
        embedding_json = result[0]['embedding_json']
        dimensions = result[0]['dimensions']

        print(f"✅ Found table: {table_name}")
        print(f"   Dimensions: {dimensions}")
        print()

        # Parse the embedding
        embedding = json.loads(embedding_json)
        print(f"✅ Parsed embedding: {len(embedding)} dimensions")
        print()

    except Exception as e:
        print(f"❌ Failed to fetch embedding: {e}")
        return False

    # Step 2: Test if vector index dimension matches
    print("Step 2: Checking vector index configuration...")
    print("-" * 80)
    print(f"Graph has vectorSearchConfiguration.dimension = 2048")
    print(f"Our embeddings are {len(embedding)} dimensions")

    if len(embedding) != 2048:
        print(f"⚠️  DIMENSION MISMATCH!")
        print(f"   Neptune expects: 2048")
        print(f"   We have: {len(embedding)}")
        print(f"   This will cause vector operations to fail")
        print()
    else:
        print(f"✅ Dimensions match!")
        print()

    # Step 3: Test neptune.algo.vectors.upsert to load embedding into vector index
    print("Step 3: Testing neptune.algo.vectors.upsert...")
    print("-" * 80)
    print(f"Attempting to upsert embedding for: {table_name}")
    print()

    # Create embedding list string (Neptune needs the actual array, not JSON string)
    embedding_str = json.dumps(embedding)

    upsert_query = f"""
    MATCH (t:Table {{name: '{table_name}'}})
    CALL neptune.algo.vectors.upsert(t, {embedding_str})
    YIELD node, embedding, success
    RETURN node.name as table_name, success
    """

    try:
        result = execute_query(upsert_query)

        if result and result[0].get('success'):
            print(f"✅ Successfully upserted embedding into vector index!")
            print(f"   Table: {result[0]['table_name']}")
            print()
        else:
            print(f"⚠️  Upsert returned but success status unclear")
            print(f"   Result: {result}")
            print()

    except requests.exceptions.HTTPError as e:
        print(f"❌ neptune.algo.vectors.upsert FAILED")
        print(f"   HTTP Error: {e}")
        print()

        if hasattr(e, 'response') and e.response is not None:
            print("Full Error Response:")
            print(f"  {e.response.text}")
            print()

            # Check for dimension mismatch
            if "dimension" in e.response.text.lower() or "2048" in e.response.text:
                print("Root Cause: DIMENSION MISMATCH")
                print(f"  Neptune is configured for 2048 dimensions")
                print(f"  Our embedding has {len(embedding)} dimensions")
                print(f"  Solution: Recreate graph with dimension={len(embedding)}")
                print()

        return False
    except Exception as e:
        print(f"❌ Upsert failed: {e}")
        return False

    # Step 4: Test semantic search with topK
    print("Step 4: Testing neptune.algo.vectors.topK.byEmbedding...")
    print("-" * 80)
    print(f"Searching for top 5 similar tables using embedding from {table_name}")
    print()

    topk_query = f"""
    CALL neptune.algo.vectors.topK.byEmbedding(
        {{ embedding: {embedding_str}, topK: 5 }}
    )
    YIELD node, score
    RETURN node.`~id` AS id, node.name AS name, score
    ORDER BY score ASC
    LIMIT 5
    """

    try:
        result = execute_query(topk_query)

        print(f"✅ Neptune vector search works!")
        print(f"   Found {len(result)} similar nodes:")
        print()

        for i, row in enumerate(result, 1):
            print(f"   {i}. {row.get('name', 'N/A')}")
            print(f"      Score (distance): {row.get('score', 'N/A')}")
            print()

        return True

    except requests.exceptions.HTTPError as e:
        print(f"❌ topK search FAILED")
        print(f"   HTTP Error: {e}")
        print()

        if hasattr(e, 'response') and e.response is not None:
            print("Full Error Response:")
            print(f"  {e.response.text}")
            print()

        return False
    except Exception as e:
        print(f"❌ Search failed: {e}")
        return False


if __name__ == "__main__":
    print()
    result = test_neptune_vectors()
    print()
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print()

    if result:
        print("✅ Neptune vector search is WORKING with correct syntax!")
        print()
        print("Next steps:")
        print("1. Upsert all table embeddings into vector index")
        print("2. Upsert all column embeddings into vector index")
        print("3. Update neptune_service.py to use neptune.algo.vectors.* functions")
    else:
        print("❌ Neptune vector search failed")
        print()
        print("Issues to fix:")
        print("1. Dimension mismatch: Neptune=2048, Embeddings=1536")
        print("2. Recreate graph with vectorSearchConfiguration.dimension=1536")
        print("3. Or regenerate embeddings with 2048 dimensions (not recommended)")
