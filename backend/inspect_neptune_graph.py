"""
Inspect Neptune graph structure and vector index contents
Shows what nodes exist, their relationships, and what's in the vector index
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


def inspect_neptune_graph():
    """Inspect what's actually in Neptune"""

    print("="*80)
    print("NEPTUNE GRAPH INSPECTION")
    print("="*80)
    print()

    # Query 1: Count all nodes by label
    print("Query 1: Count all nodes by label")
    print("-" * 80)

    query = """
    MATCH (n)
    RETURN labels(n) as label, count(n) as count
    ORDER BY count DESC
    """

    try:
        result = execute_query(query)
        print(f"Total node types found: {len(result)}")
        print()
        for row in result:
            print(f"  {row['label']}: {row['count']} nodes")
        print()
    except Exception as e:
        print(f"❌ Failed: {e}\n")

    # Query 2: List all Table nodes
    print("Query 2: All Table nodes")
    print("-" * 80)

    query = """
    MATCH (t:Table)
    RETURN t.name as name,
           t.row_count as rows,
           t.column_count as columns,
           t.table_embedding_json IS NOT NULL as has_embedding_property
    ORDER BY t.name
    """

    try:
        result = execute_query(query)
        print(f"Found {len(result)} Table nodes:")
        print()
        for row in result:
            embed_status = "✅" if row['has_embedding_property'] else "❌"
            print(f"  {embed_status} {row['name']}")
            print(f"     Rows: {row['rows']}, Columns: {row['columns']}")
        print()
    except Exception as e:
        print(f"❌ Failed: {e}\n")

    # Query 3: List all Column nodes
    print("Query 3: All Column nodes (first 20)")
    print("-" * 80)

    query = """
    MATCH (c:Column)
    RETURN c.full_name as full_name,
           c.column_name as name,
           c.column_type as type,
           c.column_embedding_json IS NOT NULL as has_embedding_property
    ORDER BY c.full_name
    LIMIT 20
    """

    try:
        result = execute_query(query)
        print(f"Found Column nodes (showing first 20):")
        print()
        for row in result:
            embed_status = "✅" if row['has_embedding_property'] else "❌"
            print(f"  {embed_status} {row['full_name']} ({row['type']})")
        print()
    except Exception as e:
        print(f"❌ Failed: {e}\n")

    # Query 4: Count relationships
    print("Query 4: Count relationships by type")
    print("-" * 80)

    query = """
    MATCH ()-[r]->()
    RETURN type(r) as relationship_type, count(r) as count
    ORDER BY count DESC
    """

    try:
        result = execute_query(query)
        print(f"Total relationship types: {len(result)}")
        print()
        for row in result:
            print(f"  {row['relationship_type']}: {row['count']} edges")
        print()
    except Exception as e:
        print(f"❌ Failed: {e}\n")

    # Query 5: Check what's ACTUALLY in the vector index by trying topK
    print("Query 5: Check what's in Neptune's VECTOR INDEX")
    print("-" * 80)
    print("Testing with a random embedding to see what nodes are indexed...")
    print()

    # Use a simple test vector (2048 dims with padding)
    test_embedding = [0.1] * 1536 + [0.0] * 512  # 1536 + 512 = 2048

    query = f"""
    CALL neptune.algo.vectors.topK.byEmbedding(
        {{ embedding: {json.dumps(test_embedding)}, topK: 20 }}
    )
    YIELD node, score
    RETURN node.`~id` AS id,
           labels(node) AS labels,
           node.name AS name,
           node.column_name AS column_name,
           node.full_name AS full_name,
           score
    ORDER BY score ASC
    LIMIT 20
    """

    try:
        result = execute_query(query)
        print(f"✅ Found {len(result)} nodes IN THE VECTOR INDEX:")
        print()
        print("These nodes have been upserted into Neptune's vector index:")
        print()

        for i, row in enumerate(result, 1):
            labels = row.get('labels', ['Unknown'])
            name = row.get('name') or row.get('column_name') or row.get('full_name') or 'Unknown'
            score = row.get('score', 'N/A')

            print(f"  {i}. [{labels[0]}] {name}")
            print(f"     Distance: {score}")
        print()

    except Exception as e:
        print(f"❌ Failed: {e}\n")

    # Query 6: Find those mysterious "carto_feature" and "country_code" nodes
    print("Query 6: Find 'carto_feature' and 'country_code' nodes")
    print("-" * 80)

    query = """
    MATCH (n)
    WHERE n.name = 'carto_feature' OR n.column_name = 'carto_feature' OR
          n.name = 'country_code' OR n.column_name = 'country_code'
    RETURN labels(n) as labels,
           n.name as name,
           n.column_name as column_name,
           n.full_name as full_name,
           n.column_type as column_type,
           n.column_embedding_json IS NOT NULL as has_embedding_property
    """

    try:
        result = execute_query(query)
        print(f"Found {len(result)} nodes with these names:")
        print()

        for row in result:
            labels = row.get('labels', ['Unknown'])
            name = row.get('name') or row.get('column_name') or row.get('full_name') or 'Unknown'
            col_type = row.get('column_type', 'N/A')
            has_embed = "✅" if row.get('has_embedding_property') else "❌"

            print(f"  Label: {labels[0]}")
            print(f"  Name: {name}")
            print(f"  Column Type: {col_type}")
            print(f"  Has embedding property: {has_embed}")
            print()

    except Exception as e:
        print(f"❌ Failed: {e}\n")

    # Query 7: Show sample relationships
    print("Query 7: Sample relationships (first 10)")
    print("-" * 80)

    query = """
    MATCH (source)-[r]->(target)
    RETURN labels(source) as source_label,
           COALESCE(source.name, source.column_name, source.full_name) as source_name,
           type(r) as rel_type,
           labels(target) as target_label,
           COALESCE(target.name, target.column_name, target.full_name) as target_name
    LIMIT 10
    """

    try:
        result = execute_query(query)
        print(f"Sample relationships:")
        print()

        for i, row in enumerate(result, 1):
            src_label = row.get('source_label', ['Unknown'])[0]
            src_name = row.get('source_name', 'Unknown')
            rel = row.get('rel_type', 'Unknown')
            tgt_label = row.get('target_label', ['Unknown'])[0]
            tgt_name = row.get('target_name', 'Unknown')

            print(f"  {i}. [{src_label}]{src_name} --{rel}--> [{tgt_label}]{tgt_name}")
        print()

    except Exception as e:
        print(f"❌ Failed: {e}\n")

    # Query 8: Check for orphaned vectors in index
    print("Query 8: Check for orphaned vectors (in index but not in graph)")
    print("-" * 80)
    print("Checking if vector index has more nodes than graph...")
    print()

    # Use a test vector to search the index
    test_embedding = [0.1] * 1536 + [0.0] * 512  # 2048 dims

    query = f"""
    CALL neptune.algo.vectors.topK.byEmbedding(
        {{ embedding: {json.dumps(test_embedding)}, topK: 50 }}
    )
    YIELD node, score
    RETURN count(node) as total_in_index
    """

    try:
        result = execute_query(query)
        total_in_index = result[0]['total_in_index'] if result else 0

        # Compare with total nodes in graph
        graph_nodes_query = "MATCH (n) RETURN count(n) as total_in_graph"
        graph_result = execute_query(graph_nodes_query)
        total_in_graph = graph_result[0]['total_in_graph'] if graph_result else 0

        print(f"Nodes in vector index: {total_in_index}")
        print(f"Nodes in graph: {total_in_graph}")
        print()

        if total_in_index > total_in_graph:
            orphaned = total_in_index - total_in_graph
            print(f"⚠️  WARNING: {orphaned} orphaned vectors detected!")
            print(f"   These are in the vector index but not in the graph")
            print(f"   Likely from deleted nodes (mystery tables)")
            print()
            print(f"   To clean up: Recreate Neptune graph or manually remove vectors")
        elif total_in_index < total_in_graph:
            not_upserted = total_in_graph - total_in_index
            print(f"ℹ️  {not_upserted} nodes have embeddings stored but NOT in vector index")
            print(f"   Need to bulk upsert these embeddings")
        else:
            print(f"✅ Vector index and graph are in sync!")

    except Exception as e:
        print(f"❌ Failed to check: {e}\n")


if __name__ == "__main__":
    print()
    inspect_neptune_graph()
    print()
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print()
    print("Key Insights:")
    print("1. Nodes with ✅ have embedding PROPERTY stored (table_embedding_json)")
    print("2. Nodes appearing in Query 5 are in the VECTOR INDEX (upserted)")
    print("3. These are two separate things!")
    print()
    print("If nodes appear in vector search but weren't upserted by our test,")
    print("they were either:")
    print("  - Upserted by someone else manually")
    print("  - Left over from previous experiments")
    print("  - Imported with vector data from a bulk load")
