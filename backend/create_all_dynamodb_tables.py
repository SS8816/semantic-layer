"""
Create all DynamoDB tables for the Semantic Layer project
Run this after switching to the new AWS account: content-analytics-index-portal-p (877525430744)

Usage:
    python create_all_dynamodb_tables.py
"""

import boto3
from botocore.exceptions import ClientError
from app.config import settings

def create_table_metadata():
    """
    Create table_metadata_rag_t1 table

    Schema:
    - Partition Key: catalog_schema_table (String) - format: "catalog.schema.table"
    - Attributes: last_updated, row_count, column_count, schema_status, relationship_detection_status
    """
    dynamodb = boto3.client('dynamodb', region_name=settings.aws_region)
    table_name = "table_metadata_rag_t1"

    try:
        # Check if table exists
        existing_tables = dynamodb.list_tables()['TableNames']
        if table_name in existing_tables:
            print(f"✅ Table '{table_name}' already exists")
            return

        print(f"Creating table '{table_name}'...")

        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'catalog_schema_table',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'catalog_schema_table',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST'  # On-demand capacity mode
        )

        # Wait for table to be created
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=table_name)

        print(f"✅ Table '{table_name}' created successfully!")

    except ClientError as e:
        print(f"❌ Error creating table '{table_name}': {e}")
        raise


def create_column_metadata():
    """
    Create column_metadata_rag_t2 table

    Schema:
    - Partition Key: catalog_schema_table (String)
    - Sort Key: column_name (String)
    - Attributes: data_type, aliases, description, column_type, semantic_type, statistics, etc.
    """
    dynamodb = boto3.client('dynamodb', region_name=settings.aws_region)
    table_name = "column_metadata_rag_t2"

    try:
        # Check if table exists
        existing_tables = dynamodb.list_tables()['TableNames']
        if table_name in existing_tables:
            print(f"✅ Table '{table_name}' already exists")
            return

        print(f"Creating table '{table_name}'...")

        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'catalog_schema_table',
                    'KeyType': 'HASH'  # Partition key
                },
                {
                    'AttributeName': 'column_name',
                    'KeyType': 'RANGE'  # Sort key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'catalog_schema_table',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'column_name',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST'  # On-demand capacity mode
        )

        # Wait for table to be created
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=table_name)

        print(f"✅ Table '{table_name}' created successfully!")

    except ClientError as e:
        print(f"❌ Error creating table '{table_name}': {e}")
        raise


def create_table_relationships():
    """
    Create table_relationships table

    Schema:
    - Partition Key: relationship_id (String - UUID)
    - GSI1: source_table (for querying all relationships from a table)
    - GSI2: target_table (for querying all relationships to a table)
    - Attributes: source_column, target_column, relationship_type, confidence, reasoning, detected_by
    """
    dynamodb = boto3.client('dynamodb', region_name=settings.aws_region)
    table_name = "table_relationships"

    try:
        # Check if table exists
        existing_tables = dynamodb.list_tables()['TableNames']
        if table_name in existing_tables:
            print(f"✅ Table '{table_name}' already exists")
            return

        print(f"Creating table '{table_name}'...")

        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'relationship_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'relationship_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'source_table',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'target_table',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'source_table_index',
                    'KeySchema': [
                        {
                            'AttributeName': 'source_table',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                },
                {
                    'IndexName': 'target_table_index',
                    'KeySchema': [
                        {
                            'AttributeName': 'target_table',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                }
            ],
            BillingMode='PAY_PER_REQUEST'  # On-demand capacity mode
        )

        # Wait for table to be created
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=table_name)

        print(f"✅ Table '{table_name}' created successfully!")

    except ClientError as e:
        print(f"❌ Error creating table '{table_name}': {e}")
        raise


def main():
    """Create all DynamoDB tables"""
    print("=" * 60)
    print("Creating DynamoDB Tables for Semantic Layer")
    print("=" * 60)
    print(f"AWS Region: {settings.aws_region}")
    print()

    # Create all three tables
    create_table_metadata()
    print()

    create_column_metadata()
    print()

    create_table_relationships()
    print()

    print("=" * 60)
    print("✅ All tables created successfully!")
    print("=" * 60)
    print()
    print("Tables created:")
    print(f"  1. table_metadata_rag_t1")
    print(f"  2. column_metadata_rag_t2")
    print(f"  3. table_relationships")
    print()
    print("IMPORTANT: Update your .env file with these table names:")
    print("  DYNAMODB_TABLE_METADATA_TABLE=table_metadata_rag_t1")
    print("  DYNAMODB_COLUMN_METADATA_TABLE=column_metadata_rag_t2")
    print()
    print("You can now run the backend API server!")


if __name__ == "__main__":
    main()
