"""
Simple Neptune Analytics Query Tool
Queries Neptune without loading unnecessary services
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
    port = settings.neptune_port

    # Neptune Analytics endpoint configuration
    base_url = f"https://{endpoint}"
    if port and port != 443:
        base_url = f"https://{endpoint}:{port}"

    url = f"{base_url}/opencypher"

    # Prepare request body
    body = {"query": query}
    body_json = json.dumps(body)

    # Prepare headers
    headers = {'Content-Type': 'application/json'}

    # AWS credentials for SigV4 signing
    session = boto3.Session()
    credentials = session.get_credentials()

    # Create AWS request for signing
    request = AWSRequest(
        method='POST',
        url=url,
        data=body_json,
        headers=headers
    )

    # Sign the request with SigV4
    SigV4Auth(credentials, 'neptune-graph', 'us-east-1').add_auth(request)

    # Execute the request
    response = requests.post(
        url,
        data=body_json,
        headers=dict(request.headers),
        verify=True
    )

    response.raise_for_status()
    result = response.json()

    return result.get('results', [])


def run_query(query, description):
    """Run a query and display results"""
    print("\n" + "="*80)
    print(f"Query: {description}")
    print("="*80)
    print(f"\nOpenCypher:\n{query}\n")

    try:
        results = execute_query(query)

        if not results:
            print("✅ Query executed successfully (no results)")
            return

        print(f"✅ Found {len(results)} result(s):\n")

        # Pretty print results
        for i, result in enumerate(results, 1):
            print(f"Result {i}:")
            for key, value in result.items():
                # Handle long JSON strings
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "... (truncated)"
                print(f"  {key}: {value}")
            print()

    except Exception as e:
        print(f"❌ Query failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run a series of test queries"""

    print("="*80)
    print("NEPTUNE ANALYTICS QUERY TOOL")
    print("="*80)
    print(f"Endpoint: {settings.neptune_endpoint}")
    print(f"Port: {settings.neptune_port}")
    print()

    # Query 1: Count all nodes
    run_query(
        """
        MATCH (t:Table)
        RETURN count(t) as table_count
        """,
        "Count all tables in Neptune"
    )

    # Query 2: List your tables only
    run_query(
        """
        MATCH (t:Table)
        WHERE t.name STARTS WITH 'here_explorer.explorer_datasets.carto_active'
        RETURN t.name as table_name,
               t.row_count as rows,
               t.column_count as columns
        ORDER BY t.name
        """,
        "List your carto_active tables"
    )

    # Query 3: Count relationships
    run_query(
        """
        MATCH ()-[r:RELATED_TO]->()
        RETURN count(r) as relationship_count
        """,
        "Count all relationships in the graph"
    )

    # Query 4: Show relationships for carto_active_2025
    run_query(
        """
        MATCH (source:Table {name: 'here_explorer.explorer_datasets.carto_active_2025'})-[r:RELATED_TO]->(target:Table)
        RETURN source.name as from_table,
               r.source_column as from_column,
               target.name as to_table,
               r.target_column as to_column,
               r.relationship_type as type,
               r.confidence as confidence
        ORDER BY r.confidence DESC
        LIMIT 10
        """,
        "Top 10 relationships FROM carto_active_2025 (highest confidence)"
    )

    # Query 5: Show columns for one table
    run_query(
        """
        MATCH (t:Table {name: 'here_explorer.explorer_datasets.carto_active_2025'})-[:HAS_COLUMN]->(c:Column)
        RETURN c.column_name as column_name,
               c.column_type as column_type,
               c.data_type as data_type,
               c.cardinality as cardinality
        ORDER BY c.column_name
        """,
        "Columns in carto_active_2025"
    )

    # Query 6: Find highly confident relationships (0.90+)
    run_query(
        """
        MATCH (source:Table)-[r:RELATED_TO]->(target:Table)
        WHERE r.confidence >= 0.90
        RETURN source.name as from_table,
               r.source_column as column,
               target.name as to_table,
               r.confidence as confidence,
               r.relationship_type as type
        ORDER BY r.confidence DESC
        """,
        "High confidence relationships (0.90+)"
    )

    # Query 7: Count nodes and edges
    run_query(
        """
        MATCH (t:Table)
        WITH count(t) as tables
        MATCH (c:Column)
        WITH tables, count(c) as columns
        MATCH ()-[has:HAS_COLUMN]->()
        WITH tables, columns, count(has) as has_column_edges
        MATCH ()-[rel:RELATED_TO]->()
        RETURN tables, columns, has_column_edges, count(rel) as relationships
        """,
        "Summary: Total nodes and edges"
    )

    print("\n" + "="*80)
    print("CUSTOM QUERY")
    print("="*80)
    print("\nYou can run custom queries by modifying this script.")
    print("Add your own queries in the main() function above.")
    print("\nExample custom query:")
    print("""
    run_query(
        \"\"\"
        MATCH (t:Table {name: 'here_explorer.explorer_datasets.carto_active_2022'})
        RETURN t.name, t.row_count, t.table_summary
        \"\"\",
        "Get details for carto_active_2022"
    )
    """)


if __name__ == "__main__":
    main()
