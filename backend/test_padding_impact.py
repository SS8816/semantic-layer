"""
Comprehensive test to verify zero-padding doesn't affect cosine similarity
Tests both self-similarity and cross-vector similarity
"""

import sys
sys.path.append('/home/user/semantic-layer/backend')

from app.services.embedding_service import embedding_service
from app.services.neptune_service import pad_embedding_to_2048
import numpy as np


def cosine_similarity(a, b):
    """Manual cosine similarity calculation"""
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def test_padding_impact():
    """
    Test if padding affects cosine similarity between different vectors
    """
    print("=" * 80)
    print("COMPREHENSIVE PADDING IMPACT TEST")
    print("=" * 80)
    print()

    # Generate embeddings for two different texts
    print("Generating embeddings for different texts...")
    text1 = "Country name or ISO country code identifying the nation"
    text2 = "Classification or category for feature type"

    emb1 = embedding_service.generate_embedding(text1)
    emb2 = embedding_service.generate_embedding(text2)

    print(f"✓ Embedding 1 dimensions: {len(emb1)}")
    print(f"✓ Embedding 2 dimensions: {len(emb2)}")
    print()

    # Test 1: Original vectors (1536 dimensions)
    print("TEST 1: Cosine similarity of ORIGINAL vectors (1536-dim)")
    sim_original = cosine_similarity(emb1, emb2)
    print(f"✓ Similarity: {sim_original:.6f} ({sim_original*100:.4f}%)")
    print()

    # Test 2: Padded vectors (2048 dimensions)
    print("TEST 2: Cosine similarity of PADDED vectors (2048-dim)")
    emb1_padded = pad_embedding_to_2048(emb1)
    emb2_padded = pad_embedding_to_2048(emb2)

    print(f"  Padded 1 dimensions: {len(emb1_padded)}")
    print(f"  Padded 2 dimensions: {len(emb2_padded)}")

    sim_padded = cosine_similarity(emb1_padded, emb2_padded)
    print(f"✓ Similarity: {sim_padded:.6f} ({sim_padded*100:.4f}%)")
    print()

    # Test 3: Compare the difference
    print("TEST 3: Difference analysis")
    diff = abs(sim_original - sim_padded)
    print(f"  Original:  {sim_original:.10f}")
    print(f"  Padded:    {sim_padded:.10f}")
    print(f"  Difference: {diff:.10f}")
    print()

    if diff < 1e-6:
        print("✅ PADDING HAS NO EFFECT (difference < 0.000001)")
    elif diff < 1e-4:
        print("⚠️  PADDING HAS MINIMAL EFFECT (difference < 0.0001)")
    else:
        print("❌ PADDING SIGNIFICANTLY AFFECTS SIMILARITY!")
    print()

    # Test 4: Verify padding structure
    print("TEST 4: Padding structure verification")
    padding_1 = emb1_padded[1536:]
    padding_2 = emb2_padded[1536:]

    all_zeros_1 = all(x == 0.0 for x in padding_1)
    all_zeros_2 = all(x == 0.0 for x in padding_2)

    print(f"  Padding 1 all zeros: {all_zeros_1}")
    print(f"  Padding 2 all zeros: {all_zeros_2}")
    print(f"  Padding length 1: {len(padding_1)}")
    print(f"  Padding length 2: {len(padding_2)}")
    print()

    if all_zeros_1 and all_zeros_2:
        print("✅ Padding is correct (all zeros)")
    else:
        print("❌ Padding contains non-zero values!")
    print()

    # Test 5: Mathematical verification
    print("TEST 5: Mathematical verification")

    # Manual calculation for original vectors
    dot_product_orig = np.dot(emb1, emb2)
    norm1_orig = np.linalg.norm(emb1)
    norm2_orig = np.linalg.norm(emb2)
    manual_sim_orig = dot_product_orig / (norm1_orig * norm2_orig)

    # Manual calculation for padded vectors
    dot_product_pad = np.dot(emb1_padded, emb2_padded)
    norm1_pad = np.linalg.norm(emb1_padded)
    norm2_pad = np.linalg.norm(emb2_padded)
    manual_sim_pad = dot_product_pad / (norm1_pad * norm2_pad)

    print(f"  Original vectors:")
    print(f"    Dot product: {dot_product_orig:.6f}")
    print(f"    Norm 1:      {norm1_orig:.6f}")
    print(f"    Norm 2:      {norm2_orig:.6f}")
    print(f"    Similarity:  {manual_sim_orig:.10f}")
    print()

    print(f"  Padded vectors:")
    print(f"    Dot product: {dot_product_pad:.6f}")
    print(f"    Norm 1:      {norm1_pad:.6f}")
    print(f"    Norm 2:      {norm2_pad:.6f}")
    print(f"    Similarity:  {manual_sim_pad:.10f}")
    print()

    # Check if dot products are equal
    dot_diff = abs(dot_product_orig - dot_product_pad)
    norm1_diff = abs(norm1_orig - norm1_pad)
    norm2_diff = abs(norm2_orig - norm2_pad)

    print(f"  Differences:")
    print(f"    Dot product: {dot_diff:.10f}")
    print(f"    Norm 1:      {norm1_diff:.10f}")
    print(f"    Norm 2:      {norm2_diff:.10f}")
    print()

    if dot_diff < 1e-6 and norm1_diff < 1e-6 and norm2_diff < 1e-6:
        print("✅ Mathematical properties preserved (dot product and norms unchanged)")
    else:
        print("❌ Mathematical properties changed by padding!")
    print()

    # Test 6: Azure OpenAI embedding normalization check
    print("TEST 6: Check if Azure OpenAI embeddings are normalized")
    norm_emb1 = np.linalg.norm(emb1)
    norm_emb2 = np.linalg.norm(emb2)

    print(f"  Embedding 1 norm: {norm_emb1:.10f}")
    print(f"  Embedding 2 norm: {norm_emb2:.10f}")

    if abs(norm_emb1 - 1.0) < 0.01 and abs(norm_emb2 - 1.0) < 0.01:
        print("✅ Embeddings are L2-normalized (norm ≈ 1.0)")
        print("   This means dot product ≈ cosine similarity for original vectors")
    else:
        print("⚠️  Embeddings are NOT normalized")
    print()

    # Final summary
    print("=" * 80)
    print("FINAL VERDICT")
    print("=" * 80)

    if diff < 1e-6:
        print("✅ Zero-padding does NOT affect cosine similarity")
        print("   The 87% vs 99% discrepancy is NOT caused by padding.")
        print()
        print("   Root cause is likely:")
        print("   - Query format mismatch (short query vs verbose storage)")
        print("   - Sample values changed since embedding was created")
        print("   - Minor metadata differences")
    else:
        print("❌ Zero-padding DOES affect cosine similarity")
        print("   This could explain lower than expected scores.")
        print()
        print("   Solution: Store and query with same dimensions (1536 or 2048)")

    print("=" * 80)


if __name__ == "__main__":
    test_padding_impact()
