"""
Starburst/Trino connection and query service
"""

from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from trino.auth import BasicAuthentication
from trino.dbapi import connect

from app.config import settings
from app.utils.logger import app_logger as logger


class StarburstService:
    """Service for connecting to and querying Starburst/Trino"""

    def __init__(self):
        """Initialize Starburst connection parameters"""
        self.host = settings.starburst_host
        self.port = settings.starburst_port
        self.catalog = settings.starburst_catalog
        self.schema = settings.starburst_schema
        self.user = settings.starburst_user
        self.password = settings.starburst_password
        self.http_scheme = settings.starburst_http_scheme
        self._connection = None

    def get_connection(
        self, username: Optional[str] = None, password: Optional[str] = None
    ):
        """
        Get or create a Trino connection

        Args:
            username: Optional username (uses logged-in user if provided, otherwise uses config)
            password: Optional password (uses logged-in user if provided, otherwise uses config)

        Returns:
            Trino connection object
        """
        try:
            # Use provided credentials or fall back to config
            user = username if username else self.user
            pwd = password if password else self.password

            auth = BasicAuthentication(user, pwd)

            conn = connect(
                host=self.host,
                port=self.port,
                user=user,
                catalog=self.catalog,
                schema=self.schema,
                http_scheme=self.http_scheme,
                auth=auth,
            )

            logger.info(
                f"Connected to Starburst at {self.host}:{self.port} as user: {user}"
            )
            return conn

        except Exception as e:
            logger.error(f"Failed to connect to Starburst: {e}")
            raise

    def execute_query(
        self, query: str, username: Optional[str] = None, password: Optional[str] = None
    ) -> List[Tuple]:
        """
        Execute a query and return results

        Args:
            query: SQL query string
            username: Optional username for connection
            password: Optional password for connection

        Returns:
            List of tuples containing query results
        """
        conn = None
        cursor = None
        try:
            conn = self.get_connection(username, password)
            cursor = conn.cursor()

            logger.debug(f"Executing query: {query[:100]}...")
            cursor.execute(query)

            results = cursor.fetchall()
            logger.info(f"Query returned {len(results)} rows")

            return results

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def execute_query_to_df(
        self, query: str, username: Optional[str] = None, password: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Execute a query and return results as pandas DataFrame

        Args:
            query: SQL query string
            username: Optional username for connection
            password: Optional password for connection

        Returns:
            DataFrame containing query results
        """
        conn = None
        cursor = None
        try:
            conn = self.get_connection(username, password)
            cursor = conn.cursor()

            logger.debug(f"Executing query to DataFrame: {query[:100]}...")
            cursor.execute(query)

            # Get column names
            columns = [desc[0] for desc in cursor.description]

            # Fetch all rows
            rows = cursor.fetchall()

            # Create DataFrame
            df = pd.DataFrame(rows, columns=columns)
            logger.info(f"Query returned DataFrame with shape {df.shape}")

            return df

        except Exception as e:
            logger.error(f"Query execution to DataFrame failed: {e}")
            raise

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_table_schema(
        self,
        table_name: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Get table schema using DESCRIBE

        Args:
            table_name: Name of the table
            username: Optional username for connection
            password: Optional password for connection

        Returns:
            Dictionary mapping column names to data types
        """
        try:
            query = f"DESCRIBE {self.catalog}.{self.schema}.{table_name}"
            results = self.execute_query(query, username, password)

            # Results format: [(column_name, data_type, extra_info, comment), ...]
            schema = {}
            for row in results:
                column_name = row[0]
                data_type = row[1]
                schema[column_name] = data_type

            logger.info(
                f"Retrieved schema for table {table_name}: {len(schema)} columns"
            )
            return schema

        except Exception as e:
            logger.error(f"Failed to get schema for table {table_name}: {e}")
            raise

    def get_row_count(
        self,
        table_name: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> int:
        """
        Get total row count for a table

        Args:
            table_name: Name of the table
            username: Optional username for connection
            password: Optional password for connection

        Returns:
            Total number of rows
        """
        try:
            query = f"SELECT COUNT(*) FROM {self.catalog}.{self.schema}.{table_name}"
            results = self.execute_query(query, username, password)

            row_count = results[0][0] if results else 0
            logger.info(f"Table {table_name} has {row_count} rows")

            return row_count

        except Exception as e:
            logger.error(f"Failed to get row count for {table_name}: {e}")
            raise

    def get_sample_data(
        self,
        table_name: str,
        limit: int = 1000,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Get random sample of data from a table

        Args:
            table_name: Name of the table
            limit: Number of rows to sample
            username: Optional username for connection
            password: Optional password for connection

        Returns:
            DataFrame with sample data
        """
        try:
            # Use ORDER BY RANDOM() for random sampling
            query = f"""
                SELECT *
                FROM {self.catalog}.{self.schema}.{table_name}
                ORDER BY RANDOM()
                LIMIT {limit}
            """

            df = self.execute_query_to_df(query, username, password)
            logger.info(f"Retrieved {len(df)} sample rows from {table_name}")

            return df

        except Exception as e:
            logger.error(f"Failed to get sample data from {table_name}: {e}")
            raise

    def get_column_statistics(
        self,
        table_name: str,
        columns: List[str],
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for all columns in a table (min, max, avg, cardinality, null count)

        Args:
            table_name: Name of the table
            columns: List of column names with their data types as dict
            username: Optional username for connection
            password: Optional password for connection

        Returns:
            Dictionary with statistics for each column
        """
        try:
            # Build SELECT clause for all columns
            select_clauses = []
            column_names = list(columns.keys())

            # Numeric types that support AVG
            numeric_types = [
                "INTEGER",
                "BIGINT",
                "SMALLINT",
                "TINYINT",
                "REAL",
                "DOUBLE",
                "DECIMAL",
                "NUMERIC",
            ]

            for col_name in column_names:
                col_type = columns.get(col_name, "").upper()

                # MIN and MAX work for most types
                select_clauses.extend(
                    [
                        f"MIN({col_name}) as {col_name}_min",
                        f"MAX({col_name}) as {col_name}_max",
                    ]
                )

                # AVG only for numeric columns
                if any(nt in col_type for nt in numeric_types):
                    select_clauses.append(
                        f"AVG(CAST({col_name} AS DOUBLE)) as {col_name}_avg"
                    )
                else:
                    select_clauses.append(f"NULL as {col_name}_avg")

                # Cardinality and null count for all columns
                select_clauses.extend(
                    [
                        f"APPROX_DISTINCT({col_name}) as {col_name}_cardinality",
                        f"SUM(CASE WHEN {col_name} IS NULL THEN 1 ELSE 0 END) as {col_name}_null_count",
                    ]
                )

            # Add total row count
            select_clauses.append("COUNT(*) as total_rows")

            # Build complete query
            query = f"""
                SELECT {", ".join(select_clauses)}
                FROM {self.catalog}.{self.schema}.{table_name}
            """

            logger.info(f"Executing statistics query for {table_name}...")
            results = self.execute_query(query, username, password)

            if not results:
                return {}

            # Parse results into dictionary
            row = results[0]
            total_rows = row[-1]  # Last column is total_rows

            stats = {}
            for i, col_name in enumerate(columns):
                base_idx = i * 5

                min_val = row[base_idx]
                max_val = row[base_idx + 1]
                avg_val = row[base_idx + 2]
                cardinality = row[base_idx + 3]
                null_count = row[base_idx + 4]

                null_percentage = (
                    (null_count / total_rows * 100) if total_rows > 0 else 0
                )

                stats[col_name] = {
                    "min_value": min_val,
                    "max_value": max_val,
                    "avg_value": avg_val,
                    "cardinality": cardinality,
                    "null_count": null_count,
                    "null_percentage": round(null_percentage, 2),
                }

            logger.info(
                f"Retrieved statistics for {len(stats)} columns from {table_name}"
            )
            return stats

        except Exception as e:
            logger.error(f"Failed to get column statistics for {table_name}: {e}")
            raise

    def get_distinct_values(
        self,
        table_name: str,
        column_name: str,
        limit: int = 1000,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> List[Any]:
        """
        Get distinct values from a column

        Args:
            table_name: Name of the table
            column_name: Name of the column
            limit: Maximum number of distinct values to return
            username: Optional username for connection
            password: Optional password for connection

        Returns:
            List of distinct values
        """
        try:
            query = f"""
                SELECT DISTINCT {column_name}
                FROM {self.catalog}.{self.schema}.{table_name}
                WHERE {column_name} IS NOT NULL
                LIMIT {limit}
            """

            results = self.execute_query(query, username, password)
            values = [row[0] for row in results]

            logger.info(
                f"Retrieved {len(values)} distinct values from {table_name}.{column_name}"
            )
            return values

        except Exception as e:
            logger.error(
                f"Failed to get distinct values from {table_name}.{column_name}: {e}"
            )
            return []

    def table_exists(
        self,
        table_name: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> bool:
        """
        Check if a table exists

        Args:
            table_name: Name of the table
            username: Optional username for connection
            password: Optional password for connection

        Returns:
            True if table exists, False otherwise
        """
        try:
            query = f"""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_catalog = '{self.catalog}'
                AND table_schema = '{self.schema}'
                AND table_name = '{table_name}'
            """

            results = self.execute_query(query, username, password)
            exists = results[0][0] > 0 if results else False

            return exists

        except Exception as e:
            logger.error(f"Failed to check if table {table_name} exists: {e}")
            return False

    def get_catalogs(
        self, username: Optional[str] = None, password: Optional[str] = None
    ) -> List[str]:
        """
        Get list of all available catalogs

        Args:
            username: Optional username for connection
            password: Optional password for connection

        Returns:
            List of catalog names
        """
        try:
            query = "SHOW CATALOGS"
            results = self.execute_query(query, username, password)

            catalogs = [row[0] for row in results]
            logger.info(f"Found {len(catalogs)} catalogs")

            return catalogs

        except Exception as e:
            logger.error(f"Failed to get catalogs: {e}")
            raise

    def get_schemas_in_catalog(
        self,
        catalog: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> List[str]:
        """
        Get list of schemas in a catalog

        Args:
            catalog: Catalog name
            username: Optional username for connection
            password: Optional password for connection

        Returns:
            List of schema names
        """
        try:
            query = f"SHOW SCHEMAS FROM {catalog}"
            logger.info(f"Fetching schemas from catalog: {catalog}")

            # Use DataFrame-returning helper so we can check .empty and column names
            df = self.execute_query_to_df(query, username, password)

            if df is None or df.empty:
                logger.warning(f"No schemas found in catalog {catalog}")
                return []

            # Many Trino setups return column named 'Schema' or 'schema'
            col_name = None
            for candidate in ("Schema", "schema", "SCHEMA"):
                if candidate in df.columns:
                    col_name = candidate
                    break

            if col_name is None:
                # Fallback: first column
                col_name = df.columns[0]

            schemas = df[col_name].astype(str).tolist()

            logger.info(f"Found {len(schemas)} schemas in {catalog}")
            return schemas

        except Exception as e:
            logger.error(f"Failed to get schemas from {catalog}: {e}")
            return []

    def get_schemas(
        self,
        catalog: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> List[str]:
        """
        Get list of schemas in a catalog

        Args:
            catalog: Name of the catalog
            username: Optional username for connection
            password: Optional password for connection

        Returns:
            List of schema names
        """
        try:
            query = f"SHOW SCHEMAS FROM {catalog}"
            results = self.execute_query(query, username, password)

            schemas = [row[0] for row in results]
            logger.info(f"Found {len(schemas)} schemas in catalog '{catalog}'")

            return schemas

        except Exception as e:
            logger.error(f"Failed to get schemas from catalog '{catalog}': {e}")
            raise

    def get_tables_in_catalog(
        self,
        catalog: str,
        schema: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get list of tables in a specific catalog.schema

        Args:
            catalog: Name of the catalog
            schema: Name of the schema
            username: Optional username for connection
            password: Optional password for connection

        Returns:
            List of dictionaries with table info: [{'name': 'table1', 'type': 'BASE TABLE'}, ...]
        """
        try:
            query = f"SHOW TABLES FROM {catalog}.{schema}"
            results = self.execute_query(query, username, password)

            tables = [
                {"name": row[0], "type": row[1] if len(row) > 1 else "TABLE"}
                for row in results
            ]

            logger.info(f"Found {len(tables)} tables in {catalog}.{schema}")

            return tables

        except Exception as e:
            logger.error(f"Failed to get tables from {catalog}.{schema}: {e}")
            raise

    def get_table_schema_with_catalog(
        self,
        catalog: str,
        schema: str,
        table_name: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Get table schema using DESCRIBE with specific catalog and schema

        Args:
            catalog: Name of the catalog
            schema: Name of the schema
            table_name: Name of the table
            username: Optional username for connection
            password: Optional password for connection

        Returns:
            Dictionary mapping column names to data types
        """
        try:
            query = f"DESCRIBE {catalog}.{schema}.{table_name}"
            results = self.execute_query(query, username, password)

            schema_dict = {}
            for row in results:
                column_name = row[0]
                data_type = row[1]
                schema_dict[column_name] = data_type

            logger.info(
                f"Retrieved schema for {catalog}.{schema}.{table_name}: {len(schema_dict)} columns"
            )
            return schema_dict

        except Exception as e:
            logger.error(
                f"Failed to get schema for {catalog}.{schema}.{table_name}: {e}"
            )
            raise

    def get_row_count_with_catalog(
        self,
        catalog: str,
        schema: str,
        table_name: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> int:
        """
        Get total row count for a table with specific catalog and schema

        Args:
            catalog: Name of the catalog
            schema: Name of the schema
            table_name: Name of the table
            username: Optional username for connection
            password: Optional password for connection

        Returns:
            Total number of rows
        """
        try:
            query = f"SELECT COUNT(*) FROM {catalog}.{schema}.{table_name}"
            results = self.execute_query(query, username, password)

            row_count = results[0][0] if results else 0
            logger.info(f"Table {catalog}.{schema}.{table_name} has {row_count} rows")

            return row_count

        except Exception as e:
            logger.error(
                f"Failed to get row count for {catalog}.{schema}.{table_name}: {e}"
            )
            raise

    def get_sample_data_with_catalog(
        self,
        catalog: str,
        schema: str,
        table_name: str,
        limit: int = 1000,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Get random sample of data from a table with specific catalog and schema

        Args:
            catalog: Name of the catalog
            schema: Name of the schema
            table_name: Name of the table
            limit: Number of rows to sample
            username: Optional username for connection
            password: Optional password for connection

        Returns:
            DataFrame with sample data
        """

        """
        Get random sample of data from a table with specific catalog and schema

        Args:
            catalog: Name of the catalog
            schema: Name of the schema
            table_name: Name of the table
            limit: Number of rows to sample
            username: Optional username for connection
            password: Optional password for connection

        Returns:
            DataFrame with sample data (complex types converted to strings)
        """
        try:
            query = f"""
                SELECT *
                FROM {catalog}.{schema}.{table_name}
                ORDER BY RANDOM()
                LIMIT {limit}
            """

            df = self.execute_query_to_df(query, username, password)

            if df is None or df.empty:
                logger.warning(f"No data returned from {catalog}.{schema}.{table_name}")
                return pd.DataFrame()

            # Convert complex types (arrays, maps, rows) to strings
            for col in df.columns:
                try:
                    # Check if column contains complex types
                    if df[col].dtype == "object":
                        # Sample a non-null value to check type
                        non_null_values = df[col].dropna()
                        if not non_null_values.empty:
                            sample_val = non_null_values.iloc[0]
                            if isinstance(sample_val, (list, dict, tuple)):
                                # Convert all values to strings
                                df[col] = df[col].apply(
                                    lambda x: str(x) if pd.notna(x) else None
                                )
                except Exception as e:
                    logger.warning(f"Could not process column {col}: {e}")
                    # Convert entire column to string as fallback
                    df[col] = df[col].astype(str)

            logger.info(
                f"Retrieved {len(df)} sample rows from {catalog}.{schema}.{table_name}"
            )

            return df

        except Exception as e:
            logger.error(
                f"Failed to get sample data from {catalog}.{schema}.{table_name}: {e}"
            )
            # Return empty DataFrame instead of raising
            return pd.DataFrame()

    def get_column_statistics_with_catalog(
        self,
        catalog: str,
        schema: str,
        table_name: str,
        columns: Dict[str, str],
        username: Optional[str] = None,
        password: Optional[str] = None,
        batch_size: int = 15,  # ADD THIS PARAMETER
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for all columns in a table with specific catalog and schema
        Processes columns in batches to avoid memory issues
        """
        try:
            column_names = list(columns.keys())
            all_stats = {}

            # Process columns in batches
            for i in range(0, len(column_names), batch_size):
                batch_columns = column_names[i : i + batch_size]
                batch_dict = {col: columns[col] for col in batch_columns}

                logger.info(
                    f"Processing statistics batch {i // batch_size + 1}/{(len(column_names) + batch_size - 1) // batch_size} ({len(batch_columns)} columns)"
                )

                # Build query for this batch
                batch_stats = self._get_batch_statistics(
                    catalog, schema, table_name, batch_dict, username, password
                )

                all_stats.update(batch_stats)

            logger.info(
                f"Retrieved statistics for {len(all_stats)} columns from {catalog}.{schema}.{table_name}"
            )
            return all_stats

        except Exception as e:
            logger.error(
                f"Failed to get column statistics for {catalog}.{schema}.{table_name}: {e}"
            )
            raise

    def _get_batch_statistics(
        self,
        catalog: str,
        schema: str,
        table_name: str,
        columns: Dict[str, str],
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for a batch of columns
        """
        try:
            select_clauses = []
            column_names = list(columns.keys())

            numeric_types = [
                "INTEGER",
                "BIGINT",
                "SMALLINT",
                "TINYINT",
                "REAL",
                "DOUBLE",
                "DECIMAL",
                "NUMERIC",
            ]

            for col_name in column_names:
                col_type = columns.get(col_name, "").upper()

                # SKIP COMPLEX TYPES
                if any(
                    complex_type in col_type
                    for complex_type in ["ARRAY", "MAP", "ROW", "JSON"]
                ):
                    select_clauses.extend(
                        [
                            f"NULL as {col_name}_min",
                            f"NULL as {col_name}_max",
                            f"NULL as {col_name}_avg",
                            f"APPROX_DISTINCT({col_name}) as {col_name}_cardinality",  # CHANGED
                            f"SUM(CASE WHEN {col_name} IS NULL THEN 1 ELSE 0 END) as {col_name}_null_count",
                        ]
                    )
                    continue

                # MIN and MAX for simple types
                select_clauses.extend(
                    [
                        f"MIN({col_name}) as {col_name}_min",
                        f"MAX({col_name}) as {col_name}_max",
                    ]
                )

                # AVG only for numeric columns
                if any(nt in col_type for nt in numeric_types):
                    select_clauses.append(
                        f"AVG(CAST({col_name} AS DOUBLE)) as {col_name}_avg"
                    )
                else:
                    select_clauses.append(f"NULL as {col_name}_avg")

                select_clauses.extend(
                    [
                        f"APPROX_DISTINCT({col_name}) as {col_name}_cardinality",  # CHANGED
                        f"SUM(CASE WHEN {col_name} IS NULL THEN 1 ELSE 0 END) as {col_name}_null_count",
                    ]
                )

            select_clauses.append("COUNT(*) as total_rows")

            query = f"""
                SELECT {", ".join(select_clauses)}
                FROM {catalog}.{schema}.{table_name}
            """

            results = self.execute_query(query, username, password)

            if not results:
                return {}

            row = results[0]
            total_rows = row[-1]

            stats = {}
            for i, col_name in enumerate(columns):
                base_idx = i * 5

                min_val = row[base_idx]
                max_val = row[base_idx + 1]
                avg_val = row[base_idx + 2]
                cardinality = row[base_idx + 3]
                null_count = row[base_idx + 4]

                null_percentage = (
                    (null_count / total_rows * 100) if total_rows > 0 else 0
                )

                stats[col_name] = {
                    "min_value": min_val,
                    "max_value": max_val,
                    "avg_value": avg_val,
                    "cardinality": cardinality,
                    "null_count": null_count,
                    "null_percentage": round(null_percentage, 2),
                }

            return stats

        except Exception as e:
            logger.error(f"Failed to get batch statistics: {e}")
            raise


# Global Starburst service instance
starburst_service = StarburstService()
