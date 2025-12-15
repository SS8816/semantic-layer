"""
Fixed test script that reconstructs the ACTUAL embedded text format
"""

import sys
sys.path.append('/home/user/semantic-layer/backend')

from app.services.embedding_service import embedding_service
from app.services.neptune_service import neptune_service, pad_embedding_to_2048
import json


def test_with_reconstructed_format():
    """
    Reconstruct the actual embedded format and test similarity
    """

    print("=" * 80)
    print("EMBEDDING FORMAT RECONSTRUCTION TEST")
    print("=" * 80)
    print()

    # Get a sample column with ALL its properties
    query = """
    MATCH (c:Column)
    RETURN c.full_name as full_name,
           c.column_name as column_name,
           c.data_type as data_type,
           c.column_type as column_type,
           c.semantic_type as semantic_type,
           c.description as description,
           c.aliases_json as aliases_json,
           c.cardinality as cardinality,
           c.sample_values_json as sample_values_json
    LIMIT 1
    """
    result = neptune_service.execute_query(query, {})

    if not result:
        print("❌ No columns found!")
        return

    col = result[0]
    full_name = col['full_name']
    column_name = col['column_name']
    data_type = col['data_type']
    column_type = col['column_type']
    semantic_type = col.get('semantic_type', '')
    description = col['description']
    aliases = json.loads(col.get('aliases_json', '[]'))
    cardinality = col.get('cardinality')
    sample_values = json.loads(col.get('sample_values_json', '[]'))

    # Extract table name
    parts = full_name.rsplit('.', 1)
    table_name = parts[0] if len(parts) == 2 else ''

    print(f"Testing column: {full_name}")
    print()

    # ========== Reconstruct the EXACT format used in embedding_service.py ==========
    aliases_str = ", ".join(aliases[:3]) if aliases else "none"
    sample_values_list = sample_values[:5] if sample_values else []
    sample_str = ", ".join(str(v) for v in sample_values_list) if sample_values_list else "no samples"

    reconstructed_text = f"""
Column: {column_name} in table {table_name}
Data type: {data_type}
Column type: {column_type}
Semantic type: {semantic_type}
Description: {description}
Aliases: {aliases_str}
Cardinality: {cardinality if cardinality else 'unknown'}
Null percentage: 0.0%
Sample values: {sample_str}

Purpose: A {column_type} column that stores {semantic_type} data, used for {'identification' if column_type == 'identifier' else 'analysis and filtering'}.
    """.strip()

    print("RECONSTRUCTED EMBEDDED TEXT:")
    print("-" * 80)
    print(reconstructed_text)
    print("-" * 80)
    print()

    # Test 1: Exact reconstructed format
    print("TEST 1: Exact reconstructed format")
    exact_embedding = embedding_service.generate_embedding(reconstructed_text)
    exact_embedding_padded = pad_embedding_to_2048(exact_embedding)

    embedding_str = str(exact_embedding_padded)
    search_query = f"""
    MATCH (c:Column)
    WHERE c.full_name = "{full_name}"
    CALL neptune.algo.vectors.distance.byEmbedding(
        c,
        {{
            embedding: {embedding_str},
            metric: "CosineSimilarity"
        }}
    )
    YIELD distance as similarity
    RETURN similarity
    """

    result = neptune_service.execute_query(search_query, {})
    if result:
        exact_score = result[0]['similarity']
        print(f"✓ EXACT FORMAT score: {exact_score:.4f} ({exact_score*100:.2f}%)")
        print()
    else:
        print("❌ Failed")
        exact_score = None

    # Test 2: Just column name
    print("TEST 2: Just column name")
    name_embedding = embedding_service.generate_embedding(column_name)
    name_embedding_padded = pad_embedding_to_2048(name_embedding)

    embedding_str = str(name_embedding_padded)
    search_query = f"""
    MATCH (c:Column)
    WHERE c.full_name = "{full_name}"
    CALL neptune.algo.vectors.distance.byEmbedding(
        c,
        {{
            embedding: {embedding_str},
            metric: "CosineSimilarity"
        }}
    )
    YIELD distance as similarity
    RETURN similarity
    """

    result = neptune_service.execute_query(search_query, {})
    if result:
        name_score = result[0]['similarity']
        print(f"✓ Column name only: {name_score:.4f} ({name_score*100:.2f}%)")
        print()
    else:
        print("❌ Failed")
        name_score = None

    # Test 3: Description only
    print("TEST 3: Description only")
    desc_embedding = embedding_service.generate_embedding(description)
    desc_embedding_padded = pad_embedding_to_2048(desc_embedding)

    embedding_str = str(desc_embedding_padded)
    search_query = f"""
    MATCH (c:Column)
    WHERE c.full_name = "{full_name}"
    CALL neptune.algo.vectors.distance.byEmbedding(
        c,
        {{
            embedding: {embedding_str},
            metric: "CosineSimilarity"
        }}
    )
    YIELD distance as similarity
    RETURN similarity
    """

    result = neptune_service.execute_query(search_query, {})
    if result:
        desc_score = result[0]['similarity']
        print(f"✓ Description only: {desc_score:.4f} ({desc_score*100:.2f}%)")
        print()
    else:
        print("❌ Failed")
        desc_score = None

    # Test 4: Simplified query format (what users actually type)
    print("TEST 4: User-friendly query")
    user_query = f"{column_name} column with {description[:50]}..."
    user_embedding = embedding_service.generate_embedding(user_query)
    user_embedding_padded = pad_embedding_to_2048(user_embedding)

    embedding_str = str(user_embedding_padded)
    search_query = f"""
    MATCH (c:Column)
    WHERE c.full_name = "{full_name}"
    CALL neptune.algo.vectors.distance.byEmbedding(
        c,
        {{
            embedding: {embedding_str},
            metric: "CosineSimilarity"
        }}
    )
    YIELD distance as similarity
    RETURN similarity
    """

    result = neptune_service.execute_query(search_query, {})
    if result:
        user_score = result[0]['similarity']
        print(f"Query: {user_query[:80]}...")
        print(f"✓ User query score: {user_score:.4f} ({user_score*100:.2f}%)")
        print()
    else:
        print("❌ Failed")
        user_score = None

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    if exact_score:
        print(f"EXACT FORMAT (should be ~99%):   {exact_score:.4f} ({exact_score*100:.2f}%)")
    if desc_score:
        print(f"Description only:                {desc_score:.4f} ({desc_score*100:.2f}%)")
    if name_score:
        print(f"Column name only:                {name_score:.4f} ({name_score*100:.2f}%)")
    if user_score:
        print(f"User-friendly query:             {user_score:.4f} ({user_score*100:.2f}%)")
    print()

    if exact_score and exact_score > 0.95:
        print("✅ Storage format is correct!")
        print(f"   Recommended threshold: {exact_score * 0.65:.2f} ({exact_score * 0.65 * 100:.1f}%)")
    else:
        print("⚠️  Exact match is lower than expected.")
        print("   This suggests the stored embedding doesn't match the reconstructed format.")
    print("=" * 80)


if __name__ == "__main__":
    test_with_reconstructed_format()
