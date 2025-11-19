# backend/create_relationships_table.py
from app.services.dynamodb_relationships import relationships_service

print("Creating table_relationships table in DynamoDB...")
relationships_service.ensure_table_exists()
print("✅ Table created successfully!")
