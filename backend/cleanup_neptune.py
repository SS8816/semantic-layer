"""
Clean up Neptune graph - Remove unwanted tables and their columns
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


def cleanup_neptune():
    """Remove unwanted tables and their relationships"""

    print("="*80)
    print("NEPTUNE GRAPH CLEANUP")
    print("="*80)
    print()

    # Tables to delete (the mystery tables without embeddings)
    tables_to_delete = [
        'core_poi_2024',
        'core_poi_2025',
        'navigable_road_attributes_2025'
    ]

    print("Tables marked for deletion:")
    for table in tables_to_delete:
        print(f"  - {table}")
    print()

    # Step 1: Count what will be deleted
    print("Step 1: Counting nodes to be deleted...")
    print("-" * 80)

    for table_name in tables_to_delete:
        # Count columns
        query = f"""
        MATCH (t:Table {{name: '{table_name}'}})-[:HAS_COLUMN]->(c:Column)
        RETURN count(c) as column_count
        """

        try:
            result = execute_query(query)
            col_count = result[0]['column_count'] if result else 0
            print(f"  {table_name}: 1 table + {col_count} columns")
        except Exception as e:
            print(f"  ❌ Error counting {table_name}: {e}")

    print()
    input("Press ENTER to proceed with deletion (Ctrl+C to cancel)...")
    print()

    # Step 2: Delete tables and their columns
    print("Step 2: Deleting tables and columns...")
    print("-" * 80)

    for table_name in tables_to_delete:
        print(f"\nDeleting {table_name}...")

        # Delete the table and all connected columns (DETACH DELETE removes relationships too)
        query = f"""
        MATCH (t:Table {{name: '{table_name}'}})
        OPTIONAL MATCH (t)-[:HAS_COLUMN]->(c:Column)
        DETACH DELETE t, c
        """

        try:
            execute_query(query)
            print(f"  ✅ Deleted {table_name} and its columns")
        except Exception as e:
            print(f"  ❌ Failed to delete {table_name}: {e}")

    # Step 3: Verify deletion
    print()
    print("Step 3: Verifying deletion...")
    print("-" * 80)

    query = """
    MATCH (t:Table)
    RETURN t.name as name
    ORDER BY t.name
    """

    try:
        result = execute_query(query)
        print(f"\nRemaining tables ({len(result)}):")
        for row in result:
            print(f"  ✅ {row['name']}")

    except Exception as e:
        print(f"❌ Failed to verify: {e}")

    # Step 4: Count remaining nodes
    print()
    print("Step 4: Final node count...")
    print("-" * 80)

    query = """
    MATCH (n)
    RETURN labels(n) as label, count(n) as count
    ORDER BY count DESC
    """

    try:
        result = execute_query(query)
        print("\nNode counts after cleanup:")
        for row in result:
            print(f"  {row['label']}: {row['count']} nodes")

    except Exception as e:
        print(f"❌ Failed to count: {e}")


if __name__ == "__main__":
    print()
    cleanup_neptune()
    print()
    print("="*80)
    print("CLEANUP COMPLETE")
    print("="*80)
    print()
    print("Next steps:")
    print("1. Run inspect_neptune_graph.py to verify cleanup")
    print("2. Check vector index - those 167 columns might still be indexed")
    print("3. May need to recreate graph to clear vector index completely")
