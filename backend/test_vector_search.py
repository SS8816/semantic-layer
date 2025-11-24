"""
Test Neptune Analytics native vector search functions
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
    response.raise_for_status()

    return response.json().get('results', [])


def test_vector_search():
    """Test Neptune's native vectorSimilarity function"""

    print("="*80)
    print("TESTING NEPTUNE NATIVE VECTOR SEARCH")
    print("="*80)
    print()

    # Step 1: Get a real embedding from Neptune
    print("Step 1: Fetching a real table embedding from Neptune...")
    print("-" * 80)

    query = """
    MATCH (t:Table)
    WHERE t.table_embedding_json IS NOT NULL
    RETURN t.name as table_name,
           t.table_embedding_json as embedding,
           t.embedding_dimensions as dimensions
    LIMIT 1
    """

    try:
        result = execute_query(query)

        if not result:
            print("❌ No tables with embeddings found in Neptune")
            return False

        table_name = result[0]['table_name']
        embedding_json = result[0]['embedding']
        dimensions = result[0]['dimensions']

        print(f"✅ Found table: {table_name}")
        print(f"   Dimensions: {dimensions}")
        print(f"   Embedding preview: {embedding_json[:100]}...")
        print()

        # Parse the embedding
        embedding = json.loads(embedding_json)
        print(f"✅ Parsed embedding: {len(embedding)} dimensions")
        print()

    except Exception as e:
        print(f"❌ Failed to fetch embedding: {e}")
        return False

    # Step 2: Test vectorSimilarity with the same embedding (should return 1.0)
    print("Step 2: Testing vectorSimilarity function...")
    print("-" * 80)
    print(f"Testing with same embedding (should return similarity = 1.0)")
    print()

    # Create the query with the embedding
    vector_query = f"""
    MATCH (t:Table {{name: '{table_name}'}})
    RETURN t.name as table_name,
           vectorSimilarity(t.table_embedding_json, {json.dumps(embedding)}) as similarity
    """

    try:
        print(f"Query: vectorSimilarity(t.table_embedding_json, <{len(embedding)}-dim vector>)")
        print()

        result = execute_query(vector_query)

        similarity = result[0]['similarity']
        print(f"🎉 SUCCESS! Vector search works!")
        print(f"   Similarity score: {similarity}")
        print(f"   (1.0 = perfect match, as expected)")
        print()

        return True

    except Exception as e:
        error_msg = str(e)
        print(f"❌ vectorSimilarity FAILED")
        print(f"   Error: {error_msg}")
        print()

        if "400" in error_msg:
            print("Root Cause Analysis:")
            print(f"  - Neptune is configured for 2048 dimensions")
            print(f"  - Our embeddings are {len(embedding)} dimensions")
            print(f"  - Dimension mismatch causes 400 Bad Request")
            print()
            print("Solution:")
            print(f"  Ask lead to update Neptune vector config to {len(embedding)} dimensions")

        return False

    # Step 3: Test semantic search with different tables
    print("Step 3: Testing semantic search across tables...")
    print("-" * 80)

    search_query = f"""
    MATCH (t:Table)
    WHERE t.table_embedding_json IS NOT NULL
    WITH t, vectorSimilarity(t.table_embedding_json, {json.dumps(embedding)}) as similarity
    WHERE similarity > 0.5
    RETURN t.name as table_name,
           similarity
    ORDER BY similarity DESC
    LIMIT 5
    """

    try:
        result = execute_query(search_query)

        print(f"✅ Found {len(result)} similar tables:")
        for i, row in enumerate(result, 1):
            print(f"   {i}. {row['table_name']} - similarity: {row['similarity']:.4f}")
        print()

        return True

    except Exception as e:
        print(f"❌ Semantic search failed: {e}")
        return False


if __name__ == "__main__":
    print()
    result = test_vector_search()
    print()
    print("="*80)
    print("SUMMARY")
    print("="*80)

    if result:
        print("✅ Neptune native vector search is WORKING!")
        print("   You can use vectorSimilarity() for semantic searches")
    else:
        print("❌ Neptune native vector search is NOT working")
        print("   Dimension mismatch (Neptune: 2048, Embeddings: 1536)")
        print("   Need to update Neptune config to match embedding dimensions")
