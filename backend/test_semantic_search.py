"""
Test semantic search with natural language queries
Demonstrates Neptune vector search working end-to-end
"""

import json
import requests
import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from app.config import settings
from app.services.embedding_service import EmbeddingService
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
    """Pad 1536-dim embedding to 2048 dimensions with zeros"""
    if len(embedding_1536) != 1536:
        raise ValueError(f"Expected 1536 dimensions, got {len(embedding_1536)}")

    padding = [0.0] * (2048 - 1536)
    return embedding_1536 + padding


def search_tables(nl_query: str, top_k: int = 5):
    """
    Search for similar tables using natural language query

    Args:
        nl_query: Natural language query (e.g., "tables with geographic data")
        top_k: Number of results to return
    """
    print(f"\n🔍 Searching for: \"{nl_query}\"")
    print("-" * 80)

    # Step 1: Generate embedding for the query
    print(f"Step 1: Generating embedding...")
    embedding_service = EmbeddingService()

    try:
        # Generate embedding using Azure OpenAI
        query_embedding = embedding_service.generate_embedding(nl_query)
        print(f"✅ Generated {len(query_embedding)}-dimensional embedding")

    except Exception as e:
        print(f"❌ Failed to generate embedding: {e}")
        return []

    # Step 2: Pad to 2048 dimensions
    print(f"Step 2: Padding to 2048 dimensions...")
    query_padded = pad_embedding_to_2048(query_embedding)
    print(f"✅ Padded to {len(query_padded)} dimensions")

    # Step 3: Search Neptune vector index
    print(f"Step 3: Searching Neptune vector index...")

    embedding_str = json.dumps(query_padded)

    search_query = f"""
    CALL neptune.algo.vectors.topK.byEmbedding(
        {{ embedding: {embedding_str}, topK: {top_k} }}
    )
    YIELD node, score
    RETURN labels(node)[0] as node_type,
           node.name as name,
           node.column_name as column_name,
           node.full_name as full_name,
           node.table_summary as summary,
           node.description as description,
           node.column_type as column_type,
           score
    ORDER BY score ASC
    LIMIT {top_k}
    """

    try:
        results = execute_query(search_query)

        if not results:
            print(f"⚠️  No results found")
            return []

        print(f"✅ Found {len(results)} result(s)")
        print()

        return results

    except Exception as e:
        print(f"❌ Search failed: {e}")
        import traceback
        traceback.print_exc()
        return []


def display_results(results):
    """Display search results in a nice format"""

    if not results:
        print("No results to display")
        return

    print("="*80)
    print("SEARCH RESULTS")
    print("="*80)
    print()

    for i, result in enumerate(results, 1):
        node_type = result.get('node_type', 'Unknown')
        score = result.get('score', 'N/A')

        # Get the display name
        name = result.get('name') or result.get('full_name') or result.get('column_name') or 'Unknown'

        print(f"{i}. [{node_type}] {name}")
        print(f"   Distance Score: {score:.6f} (lower = more similar)")

        # Show additional info based on type
        if node_type == 'Table':
            summary = result.get('summary', '')
            if summary:
                # Truncate long summaries
                if len(summary) > 150:
                    summary = summary[:147] + "..."
                print(f"   Summary: {summary}")

        elif node_type == 'Column':
            col_type = result.get('column_type', 'N/A')
            description = result.get('description', '')
            print(f"   Type: {col_type}")
            if description and len(description) < 100:
                print(f"   Description: {description}")

        print()


def run_sample_queries():
    """Run a set of sample queries to demonstrate semantic search"""

    print("="*80)
    print("SEMANTIC SEARCH DEMO - NATURAL LANGUAGE QUERIES")
    print("="*80)
    print()
    print("Testing Neptune vector search with natural language queries...")
    print()

    # Sample queries to test
    sample_queries = [
        ("geographic location data", 5),
        ("tables with coordinate information", 5),
        ("cartography and mapping features", 5),
        ("identifier columns", 5),
    ]

    all_results = []

    for query_text, top_k in sample_queries:
        results = search_tables(query_text, top_k)

        if results:
            display_results(results)
            all_results.append((query_text, results))

        print()
        print("="*80)
        print()

    # Summary
    print("SUMMARY")
    print("="*80)
    print(f"Tested {len(sample_queries)} natural language queries")
    print(f"Total results found: {sum(len(r[1]) for r in all_results)}")
    print()

    if len(all_results) == len(sample_queries):
        print("✅ All queries returned results!")
        print("✅ Semantic search is working correctly!")
    else:
        print(f"⚠️  {len(sample_queries) - len(all_results)} queries returned no results")


def interactive_search():
    """Interactive mode - user can type their own queries"""

    print("="*80)
    print("INTERACTIVE SEMANTIC SEARCH")
    print("="*80)
    print()
    print("Type natural language queries to search Neptune.")
    print("Examples:")
    print("  - 'tables with customer data'")
    print("  - 'geographic coordinates'")
    print("  - 'timestamp columns'")
    print()
    print("Type 'quit' or 'exit' to stop.")
    print()

    while True:
        try:
            query = input("Enter your query: ").strip()

            if query.lower() in ['quit', 'exit', 'q']:
                print("Exiting...")
                break

            if not query:
                print("Please enter a query")
                continue

            # Search
            results = search_tables(query, top_k=5)
            display_results(results)
            print()

        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main function"""

    print()
    print("Choose mode:")
    print("1. Run sample queries (demo)")
    print("2. Interactive search (type your own queries)")
    print()

    try:
        choice = input("Enter choice (1 or 2): ").strip()

        if choice == '1':
            run_sample_queries()
        elif choice == '2':
            interactive_search()
        else:
            print("Invalid choice. Running sample queries...")
            run_sample_queries()

    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
