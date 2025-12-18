"""
Test script to find MIN and MAX similarity scores for threshold tuning
Run this to establish proper threshold ranges
"""

import sys
sys.path.append('/home/user/semantic-layer/backend')

from app.services.embedding_service import embedding_service
from app.services.neptune_service import neptune_service, pad_embedding_to_2048
from app.services.dynamodb import dynamodb_service
import numpy as np


def test_similarity_ranges():
    """
    Test similarity scores to find min/max ranges:
    - Min: words completely absent from index
    - Max: exact match with stored embeddings
    """

    print("=" * 80)
    print("EMBEDDING SIMILARITY DIAGNOSTIC TEST")
    print("=" * 80)
    print()

    # ========== TEST 1: Get a sample stored column from Neptune ==========
    print("TEST 1: Getting sample column from Neptune...")
    query = """
    MATCH (c:Column)
    RETURN c.full_name as name, c.description as description
    LIMIT 1
    """
    result = neptune_service.execute_query(query, {})

    if not result:
        print("❌ No columns found in Neptune!")
        return

    sample_column = result[0]
    column_name = sample_column['name']
    stored_description = sample_column.get('description', '')

    print(f"✓ Sample column: {column_name}")
    print(f"  Description: {stored_description[:100]}...")
    print()

    # ========== TEST 2: EXACT MATCH - Query with stored description ==========
    print("TEST 2: EXACT MATCH - Using stored description as query")
    print(f"Query: {stored_description[:100]}...")

    exact_embedding = embedding_service.generate_embedding(stored_description)
    exact_embedding_padded = pad_embedding_to_2048(exact_embedding)

    # Search Neptune
    embedding_str = str(exact_embedding_padded)
    search_query = f"""
    MATCH (c:Column)
    WHERE c.full_name = "{column_name}"
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
        max_score = result[0]['similarity']
        print(f"✓ MAX SCORE (exact match): {max_score:.4f} ({max_score*100:.2f}%)")
    else:
        print("❌ Failed to get exact match score")
        max_score = None
    print()

    # ========== TEST 3: COLUMN NAME ONLY ==========
    print("TEST 3: COLUMN NAME ONLY")
    parts = column_name.rsplit('.', 1)
    if len(parts) == 2:
        col_name_only = parts[1]
    else:
        col_name_only = column_name

    print(f"Query: {col_name_only}")

    name_embedding = embedding_service.generate_embedding(col_name_only)
    name_embedding_padded = pad_embedding_to_2048(name_embedding)

    embedding_str = str(name_embedding_padded)
    search_query = f"""
    MATCH (c:Column)
    WHERE c.full_name = "{column_name}"
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
        print(f"✓ Column name only score: {name_score:.4f} ({name_score*100:.2f}%)")
    else:
        print("❌ Failed to get column name score")
        name_score = None
    print()

    # ========== TEST 4: ENRICHED QUERY ==========
    print("TEST 4: ENRICHED QUERY (mimicking stored format)")
    enriched_query = f"""
Column: {col_name_only}
Description: {stored_description}
Type: database column
    """.strip()

    print(f"Query:\n{enriched_query[:150]}...")

    enriched_embedding = embedding_service.generate_embedding(enriched_query)
    enriched_embedding_padded = pad_embedding_to_2048(enriched_embedding)

    embedding_str = str(enriched_embedding_padded)
    search_query = f"""
    MATCH (c:Column)
    WHERE c.full_name = "{column_name}"
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
        enriched_score = result[0]['similarity']
        print(f"✓ Enriched query score: {enriched_score:.4f} ({enriched_score*100:.2f}%)")
    else:
        print("❌ Failed to get enriched score")
        enriched_score = None
    print()

    # ========== TEST 5: MIN SCORE - Completely unrelated query ==========
    print("TEST 5: MIN SCORE - Completely unrelated query")
    unrelated_query = "quantum physics black hole singularity xyzabc nonsense"
    print(f"Query: {unrelated_query}")

    unrelated_embedding = embedding_service.generate_embedding(unrelated_query)
    unrelated_embedding_padded = pad_embedding_to_2048(unrelated_embedding)

    embedding_str = str(unrelated_embedding_padded)
    search_query = f"""
    MATCH (c:Column)
    WHERE c.full_name = "{column_name}"
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
        min_score = result[0]['similarity']
        print(f"✓ MIN SCORE (unrelated): {min_score:.4f} ({min_score*100:.2f}%)")
    else:
        print("❌ Failed to get min score")
        min_score = None
    print()

    # ========== TEST 6: Check if padding affects similarity ==========
    print("TEST 6: PADDING EFFECT TEST")
    print("Comparing same vector with and without padding...")

    # Create two identical 1536-dim vectors
    test_vec_1536 = exact_embedding[:1536]
    test_vec_padded = pad_embedding_to_2048(test_vec_1536)

    # Calculate cosine similarity manually
    def cosine_similarity(a, b):
        a = np.array(a)
        b = np.array(b)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    # Compare padded vs padded
    sim_both_padded = cosine_similarity(test_vec_padded, test_vec_padded)
    print(f"✓ Padded vs Padded similarity: {sim_both_padded:.6f}")

    # Compare 1536 vs 1536
    sim_original = cosine_similarity(test_vec_1536, test_vec_1536)
    print(f"✓ Original vs Original similarity: {sim_original:.6f}")

    print(f"  Difference: {abs(sim_both_padded - sim_original):.8f}")
    if abs(sim_both_padded - sim_original) < 0.0001:
        print("  ✓ Padding does NOT affect similarity (as expected)")
    else:
        print("  ⚠️  WARNING: Padding might be affecting similarity!")
    print()

    # ========== SUMMARY ==========
    print("=" * 80)
    print("SUMMARY OF RESULTS")
    print("=" * 80)
    if max_score:
        print(f"MAX SCORE (exact match):     {max_score:.4f} ({max_score*100:.2f}%)")
    if enriched_score:
        print(f"ENRICHED QUERY:              {enriched_score:.4f} ({enriched_score*100:.2f}%)")
    if name_score:
        print(f"COLUMN NAME ONLY:            {name_score:.4f} ({name_score*100:.2f}%)")
    if min_score:
        print(f"MIN SCORE (unrelated):       {min_score:.4f} ({min_score*100:.2f}%)")
    print()
    print("RECOMMENDED THRESHOLDS:")
    if max_score and min_score:
        mid_point = (max_score + min_score) / 2
        strict_threshold = max_score * 0.7
        loose_threshold = max_score * 0.5

        print(f"  Strict (high precision):   {strict_threshold:.2f} ({strict_threshold*100:.1f}%)")
        print(f"  Balanced:                  {mid_point:.2f} ({mid_point*100:.1f}%)")
        print(f"  Loose (high recall):       {loose_threshold:.2f} ({loose_threshold*100:.1f}%)")
    print("=" * 80)


if __name__ == "__main__":
    test_similarity_ranges()
