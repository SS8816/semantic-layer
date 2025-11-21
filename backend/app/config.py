"""
Configuration management using Pydantic Settings
"""

import os
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Starburst/Trino Configuration
    starburst_host: str
    starburst_port: int = 443
    starburst_catalog: str
    starburst_schema: str
    starburst_user: str
    starburst_password: str
    starburst_http_scheme: str = "https"

    # DynamoDB Configuration
    aws_region: str = "us-east-1"
    dynamodb_table_metadata_table: str = "table_metadata"
    dynamodb_column_metadata_table: str = "column_metadata"

    # AWS Credentials (optional - will use boto3 default chain if not provided)
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None

    # Application Configuration
    schema_files_path: str = "./schema"
    log_level: str = "INFO"

    # HuggingFace Model Configuration
    alias_model: str = "google/flan-t5-base"
    description_model: str = "google/flan-t5-base"
    ner_model: str = "dslim/bert-base-NER"
    sentence_transformer_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Azure OpenAI Configuration
    azure_openai_api_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_deployment: str = "gpt-5"
    azure_openai_api_version: str = "2024-12-01-preview"

    # OpenAI Configuration (for embeddings)
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"

    # Neptune Configuration
    neptune_endpoint: str = "localhost"  # Use localhost when SSH tunneling
    neptune_port: int = 8182
    neptune_use_iam: bool = False  # Set to True for production IAM auth

    # Session Configuration
    session_secret_key: str

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: List[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


# Global settings instance
settings = Settings()


def get_schema_file_path(table_name: str) -> str:
    """Get the full path to a schema DDL file"""
    return os.path.join(settings.schema_files_path, f"{table_name}.sql")


def get_all_table_names() -> List[str]:
    """Get all table names from schema directory"""
    if not os.path.exists(settings.schema_files_path):
        return []

    files = os.listdir(settings.schema_files_path)
    table_names = [os.path.splitext(f)[0] for f in files if f.endswith(".sql")]
    return sorted(table_names)
