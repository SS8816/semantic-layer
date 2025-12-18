#!/usr/bin/env python3
"""
Quick script to retry Neptune import for a specific table
"""
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.neptune_service import NeptuneService
from app.services.dynamodb import DynamoDBService

def retry_import(table_name: str):
    """Retry Neptune import for a specific table"""
    print(f"🔄 Retrying Neptune import for {table_name}...")

    # Initialize services
    neptune_service = NeptuneService()
    dynamodb_service = DynamoDBService()

    # Attempt import
    success = neptune_service.import_table_to_neptune(table_name)

    if success:
        # Update status to 'imported'
        dynamodb_service.update_neptune_import_status(table_name, 'imported')
        print(f"✅ Successfully imported {table_name} to Neptune")
    else:
        dynamodb_service.update_neptune_import_status(table_name, 'failed')
        print(f"❌ Failed to import {table_name} to Neptune")

    return success

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python retry_neptune_import.py <table_name>")
        print("Example: python retry_neptune_import.py here_explorer.explorer_datasets.core_poi_2025")
        sys.exit(1)

    table_name = sys.argv[1]
    retry_import(table_name)
