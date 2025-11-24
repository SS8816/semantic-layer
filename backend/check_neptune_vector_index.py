"""
Check if Neptune Analytics has vector indexes configured
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


def check_vector_index():
    """
    Check if vector indexes are configured in Neptune Analytics

    Note: Neptune Analytics vector index configuration is done at the AWS level,
    not visible through OpenCypher queries. This script tries common approaches.
    """

    print("="*80)
    print("NEPTUNE ANALYTICS - VECTOR INDEX CHECK")
    print("="*80)
    print()

    # Method 1: Try to use vector similarity function
    print("Method 1: Testing vector similarity function...")
    print("-" * 80)

    try:
        # Create a test vector (small one)
        test_vector = [0.1] * 10  # 10-dimensional test vector

        query = """
        MATCH (t:Table)
        RETURN t.name
        LIMIT 1
        """

        result = execute_query(query)

        if result:
            table_name = result[0]['t.name']
            print(f"✅ Found test table: {table_name}")

            # Try vector similarity query
            vector_query = f"""
            MATCH (t:Table {{name: '{table_name}'}})
            RETURN vectorSimilarity(t.table_embedding_json, {test_vector}) as similarity
            """

            print(f"\nTrying vector similarity query:")
            print(f"  {vector_query}")

            try:
                vec_result = execute_query(vector_query)
                print(f"✅ Vector similarity function WORKS!")
                print(f"   Result: {vec_result}")
                print(f"\n🎉 VECTOR INDEX IS CONFIGURED!")
                return True

            except Exception as e:
                error_msg = str(e)
                print(f"❌ Vector similarity function failed")
                print(f"   Error: {error_msg}")

                if "vectorSimilarity" in error_msg or "not found" in error_msg.lower():
                    print(f"\n⚠️  VECTOR INDEX IS NOT CONFIGURED")
                    print(f"   Neptune Analytics doesn't recognize vectorSimilarity function")
                    return False
        else:
            print("⚠️  No tables found to test with")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print()
    print("="*80)
    print("ALTERNATIVE CHECK: AWS CLI")
    print("="*80)
    print()
    print("You can also check using AWS CLI:")
    print()
    print("  aws neptune-graph describe-graph \\")
    print("    --graph-identifier g-el5ekbpdu0 \\")
    print("    --region us-east-1")
    print()
    print("Look for 'vectorSearchConfiguration' in the output.")
    print()
    print("="*80)
    print("ALTERNATIVE CHECK: AWS Console")
    print("="*80)
    print()
    print("1. Go to Neptune Analytics in AWS Console")
    print("2. Select your graph: cai-semantic-graph")
    print("3. Look for 'Vector search' or 'Vector index' configuration")
    print("4. Check if any properties are configured as vector indexes")
    print()

    return None


if __name__ == "__main__":
    result = check_vector_index()

    print()
    print("="*80)
    print("SUMMARY")
    print("="*80)

    if result is True:
        print("✅ Vector index IS configured")
        print("   You can use vector similarity search!")
    elif result is False:
        print("❌ Vector index IS NOT configured")
        print("   Ask your lead to configure Neptune Analytics vector index")
        print()
        print("   Configuration needed:")
        print("   - Property: table_embedding_json and column_embedding_json")
        print("   - Dimensions: 1536")
        print("   - Similarity metric: cosine")
    else:
        print("⚠️  Unable to determine - check manually using AWS CLI or Console")
