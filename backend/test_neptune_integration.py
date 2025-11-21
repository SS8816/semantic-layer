"""
Test script to populate Neptune with existing DynamoDB metadata

This script:
1. Reads metadata for existing tables from DynamoDB
2. Generates embeddings using Azure OpenAI
3. Stores in Neptune graph database
4. Queries Neptune to verify the data

Run this BEFORE integrating into the main pipeline to test Neptune functionality.
"""

import sys
from app.services import dynamodb_service, neptune_service, embedding_service
from app.services.dynamodb_relationships import relationships_service
from app.utils.logger import app_logger as logger


def test_neptune_with_existing_tables():
    """Test Neptune integration with existing 3 tables"""

    # The 3 tables you already have metadata for
    test_tables = [
        "here_explorer.explorer_datasets.carto_active_2022",
        "here_explorer.explorer_datasets.carto_active_2023",
        "here_explorer.explorer_datasets.carto_active_2024",
    ]

    print("=" * 80)
    print("NEPTUNE INTEGRATION TEST")
    print("=" * 80)
    print()
    print(f"Testing with {len(test_tables)} tables:")
    for table in test_tables:
        print(f"  - {table}")
    print()

    # Connect to Neptune
    try:
        print("🔌 Connecting to Neptune...")
        neptune_service.connect()
        print("✅ Connected to Neptune successfully!")
        print()
    except Exception as e:
        print(f"❌ Failed to connect to Neptune: {e}")
        print("\nMake sure:")
        print("  1. SSH tunnel is running")
        print("  2. Neptune endpoint is correct in .env")
        return

    # Process each table
    for i, table_name in enumerate(test_tables, 1):
        print(f"{'='*80}")
        print(f"Processing Table {i}/{len(test_tables)}: {table_name}")
        print(f"{'='*80}")

        try:
            # Step 1: Fetch metadata from DynamoDB
            print(f"\n📥 Step 1: Fetching metadata from DynamoDB...")
            table_with_columns = dynamodb_service.get_table_with_columns(table_name)

            if not table_with_columns:
                print(f"❌ No metadata found in DynamoDB for {table_name}")
                continue

            table_metadata = dynamodb_service.get_table_metadata(table_name)
            columns = table_with_columns.columns

            print(f"✅ Found metadata:")
            print(f"   - Row count: {table_metadata.row_count:,}")
            print(f"   - Column count: {table_metadata.column_count}")
            print(f"   - Columns: {len(columns)}")

            # Step 2: Generate embeddings
            print(f"\n🧠 Step 2: Generating embeddings with Azure OpenAI...")

            # Generate table embedding
            table_embedding, table_summary = embedding_service.generate_table_embedding(
                table_metadata, columns
            )
            print(f"✅ Generated table embedding ({len(table_embedding)} dimensions)")
            print(f"   Summary preview: {table_summary[:150]}...")

            # Step 3: Store table node in Neptune
            print(f"\n💾 Step 3: Storing table node in Neptune...")
            success = neptune_service.create_table_node(
                table_name=table_name,
                row_count=table_metadata.row_count,
                column_count=table_metadata.column_count,
                schema_status=table_metadata.schema_status.value,
                table_embedding=table_embedding,
                table_summary=table_summary
            )

            if success:
                print(f"✅ Stored table node in Neptune")
            else:
                print(f"❌ Failed to store table node")
                continue

            # Step 4: Store ALL column nodes
            print(f"\n💾 Step 4: Storing ALL {len(columns)} column nodes...")
            columns_stored = 0

            for col_name, col_metadata in columns.items():  # Process ALL columns
                try:
                    # Generate column embedding
                    col_embedding, col_description = embedding_service.generate_column_embedding(
                        table_name, col_metadata
                    )

                    # Store column node
                    success = neptune_service.create_column_node(
                        table_name=table_name,
                        column_name=col_name,
                        data_type=col_metadata.data_type,
                        column_type=col_metadata.column_type,
                        semantic_type=col_metadata.semantic_type,
                        description=col_metadata.description,
                        column_embedding=col_embedding,
                        aliases=col_metadata.aliases,
                        cardinality=col_metadata.cardinality,
                        sample_values=col_metadata.sample_values
                    )

                    if success:
                        columns_stored += 1
                        print(f"   ✅ {col_name} ({col_metadata.column_type})")

                except Exception as e:
                    print(f"   ❌ Failed to store column {col_name}: {e}")

            print(f"✅ Stored {columns_stored}/{len(columns)} column nodes")

            # Step 5: Store ALL relationships
            print(f"\n💾 Step 5: Storing ALL relationships...")
            relationships = relationships_service.get_relationships_by_source_table(table_name)

            if relationships:
                print(f"   Found {len(relationships)} relationships")
                rels_stored = 0

                for rel in relationships:  # Process ALL relationships
                    try:
                        success = neptune_service.create_relationship_edge(
                            source_table=rel['source_table'],
                            source_column=rel['source_column'],
                            target_table=rel['target_table'],
                            target_column=rel['target_column'],
                            relationship_type=rel['relationship_type'],
                            relationship_subtype=rel.get('relationship_subtype'),
                            confidence=float(rel['confidence']),
                            reasoning=rel.get('reasoning', ''),
                            detected_by=rel.get('detected_by', 'gpt-5')
                        )

                        if success:
                            rels_stored += 1

                    except Exception as e:
                        print(f"   ❌ Failed to store relationship: {e}")

                print(f"✅ Stored {rels_stored}/{len(relationships)} relationships")
            else:
                print(f"   No relationships found for this table")

            print(f"\n✅ Successfully processed {table_name}")

        except Exception as e:
            print(f"\n❌ Error processing {table_name}: {e}")
            import traceback
            traceback.print_exc()

        print()

    # Query Neptune to verify
    print(f"{'='*80}")
    print("VERIFICATION: Querying Neptune")
    print(f"{'='*80}")
    print()

    try:
        print("📊 Fetching all tables from Neptune...")
        all_tables = neptune_service.get_all_tables()
        print(f"✅ Found {len(all_tables)} tables in Neptune:")
        for table in all_tables:
            print(f"   - {table}")
        print()

        # Get details for first table
        if all_tables:
            first_table = all_tables[0]
            print(f"📊 Fetching details for {first_table}...")

            table_data = neptune_service.get_table_with_columns(first_table)
            if table_data:
                print(f"✅ Table data retrieved:")
                print(f"   Properties: {list(table_data.get('table', {}).keys())}")
                print(f"   Columns: {len(table_data.get('columns', []))}")

            relationships = neptune_service.get_table_relationships(first_table)
            print(f"✅ Relationships: {len(relationships)}")

            if relationships:
                print(f"\n   Sample relationship:")
                rel = relationships[0]
                print(f"   {rel.get('source')} → {rel.get('target')}")
                print(f"   Type: {rel.get('relationship', {}).get('relationship_type', [''])[0]}")
                print(f"   Confidence: {rel.get('relationship', {}).get('confidence', [0])[0]}")

    except Exception as e:
        print(f"❌ Error querying Neptune: {e}")
        import traceback
        traceback.print_exc()

    # Close connection
    print()
    print("🔌 Closing Neptune connection...")
    neptune_service.close()
    print("✅ Done!")
    print()
    print("=" * 80)
    print("Next steps:")
    print("  1. Review the data stored in Neptune")
    print("  2. Show to your lead for approval")
    print("  3. If approved, we'll integrate into metadata generation pipeline")
    print("=" * 80)


if __name__ == "__main__":
    test_neptune_with_existing_tables()
