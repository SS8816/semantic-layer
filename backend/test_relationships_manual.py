# backend/test_relationships_manual.py

import asyncio

from app.services.relationship_tasks import detect_and_store_relationships

# Choose a table that already has metadata
catalog = "here_explorer"
schema = "explorer_datasets"
table_name = "carto_active_2024"  # Change this to any table you want

table_identifier = f"{catalog}#{schema}#{table_name}"

print(f" Manually triggering relationship detection for {table_name}")
print(f"This will compare against all other tables with metadata...")
print()

# Run the detection
result = asyncio.run(
    detect_and_store_relationships(
        table_identifier=table_identifier,
        catalog=catalog,
        schema=schema,
        table_name=table_name,
    )
)

print("\n" + "=" * 60)
print("RESULT:")
print("=" * 60)
print(f"Status: {result['status']}")
print(f"Table: {result.get('table', 'N/A')}")
print(f"Relationships found: {result['relationships_found']}")

if result.get("error"):
    print(f"Error: {result['error']}")

if result.get("relationships"):
    print(f"\nTop relationships:")
    for rel in result["relationships"][:5]:
        print(
            f"  • {rel['source_column']} → {rel['target_table']}.{rel['target_column']}"
        )
        print(
            f"    Type: {rel['relationship_type']}, Confidence: {rel['confidence']:.2f}"
        )

print("=" * 60)
