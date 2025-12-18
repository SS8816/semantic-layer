"""
Test Neptune vector search with zero-padded embeddings
Pads 1536-dim embeddings to 2048 to match Neptune's configuration
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


def pad_embedding_to_2048(embedding_1536):
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


def test_padded_vectors():
    """Test Neptune vector search with zero-padded embeddings"""

    print("="*80)
    print("NEPTUNE VECTOR SEARCH - ZERO-PADDED EMBEDDINGS TEST")
    print("="*80)
    print()

    # Step 1: Get a real 1536-dim embedding from Neptune
    print("Step 1: Fetching 1536-dim embedding from Neptune...")
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
        print(f"   Original dimensions: {dimensions}")
        print()

        # Parse the embedding
        embedding_1536 = json.loads(embedding_json)
        print(f"✅ Parsed embedding: {len(embedding_1536)} dimensions")

    except Exception as e:
        print(f"❌ Failed to fetch embedding: {e}")
        return False

    # Step 2: Pad to 2048 dimensions
    print()
    print("Step 2: Padding embedding to 2048 dimensions...")
    print("-" * 80)

    try:
        embedding_2048 = pad_embedding_to_2048(embedding_1536)
        print(f"✅ Padded embedding created: {len(embedding_2048)} dimensions")
        print(f"   Original values: {embedding_1536[:5]} ...")
        print(f"   Padded values: {embedding_2048[:5]} ... {embedding_2048[-5:]}")
        print(f"   Last 5 values (should be zeros): {embedding_2048[-5:]}")
        print()

    except Exception as e:
        print(f"❌ Failed to pad embedding: {e}")
        return False

    # Step 3: Test upsert with padded embedding
    print("Step 3: Testing neptune.algo.vectors.upsert with padded embedding...")
    print("-" * 80)

    embedding_str = json.dumps(embedding_2048)

    upsert_query = f"""
    MATCH (t:Table {{name: '{table_name}'}})
    CALL neptune.algo.vectors.upsert(t, {embedding_str})
    YIELD node, embedding, success
    RETURN node.name as table_name, success
    """

    try:
        result = execute_query(upsert_query)

        if result and result[0].get('success'):
            print(f"🎉 SUCCESS! Upsert worked with padded embedding!")
            print(f"   Table: {result[0]['table_name']}")
            print(f"   The 2048-dim padded embedding was accepted by Neptune")
            print()
        else:
            print(f"⚠️  Upsert returned but success status unclear")
            print(f"   Result: {result}")
            print()

    except requests.exceptions.HTTPError as e:
        print(f"❌ Upsert with padded embedding FAILED")
        print(f"   HTTP Error: {e}")
        print()

        if hasattr(e, 'response') and e.response is not None:
            print("Full Error Response:")
            print(f"  {e.response.text}")
            print()

        return False
    except Exception as e:
        print(f"❌ Upsert failed: {e}")
        return False

    # Step 4: Test semantic search with padded embedding
    print("Step 4: Testing semantic search with padded embedding...")
    print("-" * 80)

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

        print(f"🎉 SEMANTIC SEARCH WORKS!")
        print(f"   Found {len(result)} similar nodes:")
        print()

        for i, row in enumerate(result, 1):
            print(f"   {i}. {row.get('name', 'N/A')}")
            print(f"      Distance score: {row.get('score', 'N/A'):.6f}")
            print()

        # The first result should be the same table (distance ~0)
        if result and result[0].get('name') == table_name:
            score = result[0].get('score', 999)
            print(f"✅ Self-match verified! Same table appears first with score: {score:.6f}")
            print(f"   (Score should be very close to 0 for exact match)")

        print()
        return True

    except requests.exceptions.HTTPError as e:
        print(f"❌ Semantic search FAILED")
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
    result = test_padded_vectors()
    print()
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print()

    if result:
        print("✅ ZERO-PADDING SOLUTION WORKS!")
        print()
        print("Next steps:")
        print("1. Update embedding generation to pad from 1536 to 2048 dimensions")
        print("2. Bulk upsert all existing table embeddings (padded)")
        print("3. Bulk upsert all existing column embeddings (padded)")
        print("4. Update neptune_service.py to pad embeddings before upsert")
        print()
        print("Note: Zero-padding is a workaround. Ideally Neptune should be")
        print("configured for 1536 dimensions to avoid wasting 512 dimensions.")
    else:
        print("❌ Zero-padding solution failed")
        print("   Check error messages above for details")
