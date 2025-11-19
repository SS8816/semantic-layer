# """
# Column type detection service
# Detects whether a column is: dimension, measure, identifier, timestamp, or detail
# """
# from typing import Any
# from app.utils.logger import app_logger as logger


# class ColumnTypeDetector:
#     """Detect column types (dimension, measure, identifier, timestamp, detail)"""

#     DIMENSION_THRESHOLD = 20
#     IDENTIFIER_PATTERNS = ['id', 'pvid', 'key', 'uuid', 'guid', 'code']
#     NUMERIC_TYPES = ['bigint', 'integer', 'smallint', 'tinyint', 'double',
#                      'float', 'real', 'decimal', 'numeric']
#     TIMESTAMP_TYPES = ['timestamp', 'date', 'datetime', 'time']

#     def detect_column_type(
#         self,
#         column_name: str,
#         data_type: str,
#         cardinality: int,
#         row_count: int = 0
#     ) -> str:
#         """
#         Detect column type

#         Returns: 'dimension', 'measure', 'identifier', 'timestamp', or 'detail'
#         """
#         col_lower = column_name.lower()
#         type_lower = data_type.lower()

#         # 1. TIMESTAMP
#         if any(ts in type_lower for ts in self.TIMESTAMP_TYPES):
#             return 'timestamp'

#         # 2. IDENTIFIER
#         if self._is_identifier(col_lower, cardinality, row_count):
#             return 'identifier'

#         # 3. MEASURE (numeric, high cardinality)
#         if self._is_measure(type_lower, cardinality):
#             return 'measure'

#         # 4. DIMENSION (low cardinality, categorical)
#         if cardinality <= self.DIMENSION_THRESHOLD:
#             return 'dimension'

#         # 5. DETAIL (high cardinality text)
#         if self._is_detail(type_lower, cardinality):
#             return 'detail'

#         # Default
#         if self._is_numeric_type(type_lower):
#             return 'measure'
#         return 'dimension'

#     def _is_identifier(self, col_name: str, cardinality: int, row_count: int) -> bool:
#         """Check if column is an identifier"""
#         has_pattern = any(p in col_name for p in self.IDENTIFIER_PATTERNS)
#         if not has_pattern:
#             return False

#         if row_count > 0:
#             uniqueness = cardinality / row_count
#             if uniqueness > 0.8:
#                 return True

#         return cardinality > 1000

#     def _is_measure(self, data_type: str, cardinality: int) -> bool:
#         """Check if column is a measure"""
#         if not self._is_numeric_type(data_type):
#             return False
#         return cardinality > self.DIMENSION_THRESHOLD

#     def _is_detail(self, data_type: str, cardinality: int) -> bool:
#         """Check if column is detail"""
#         if self._is_numeric_type(data_type):
#             return False
#         return cardinality > 100

#     def _is_numeric_type(self, data_type: str) -> bool:
#         """Check if numeric"""
#         return any(t in data_type for t in self.NUMERIC_TYPES)


# # Global instance
# column_type_detector = ColumnTypeDetector()


"""
Column type detection service
Detects whether a column is: dimension, measure, identifier, timestamp, or detail
"""

from typing import Any

from app.utils.logger import app_logger as logger


class ColumnTypeDetector:
    """Detect column types (dimension, measure, identifier, timestamp, detail)"""

    DIMENSION_THRESHOLD = 20
    PRIMARY_ID_PATTERNS = ["link_id", "road_id", "uuid", "guid", "pk", "primary"]
    FOREIGN_KEY_PATTERNS = ["pvid", "fk", "ref_id", "parent_id"]
    IDENTIFIER_PATTERNS = ["id", "key", "code"]

    # Measurement keywords (strongly indicate numeric measure, not ID)
    MEASURE_KEYWORDS = [
        "kms",
        "kilometers",
        "distance",
        "length",
        "count",
        "total",
        "sum",
        "avg",
        "amount",
        "value",
        "price",
        "cost",
        "rate",
        "latitude",
        "longitude",
        "lat",
        "lon",
        "coord",
    ]

    NUMERIC_TYPES = [
        "bigint",
        "integer",
        "smallint",
        "tinyint",
        "double",
        "float",
        "real",
        "decimal",
        "numeric",
    ]
    TIMESTAMP_TYPES = ["timestamp", "date", "datetime", "time"]

    def detect_column_type(
        self, column_name: str, data_type: str, cardinality: int, row_count: int = 0
    ) -> str:
        """
        Detect column type

        Returns: 'dimension', 'measure', 'identifier', 'timestamp', or 'detail'
        """
        col_lower = column_name.lower()
        type_lower = data_type.lower()

        # 1. TIMESTAMP
        if any(ts in type_lower for ts in self.TIMESTAMP_TYPES):
            return "timestamp"

        # 2. IDENTIFIER (Primary Keys - highly unique)
        if self._is_primary_identifier(col_lower, cardinality, row_count):
            return "identifier"

        # 3. DIMENSION (Foreign Keys or low cardinality)
        # Foreign keys with ID patterns but low uniqueness are dimensions
        if self._is_foreign_key_dimension(col_lower, cardinality, row_count):
            return "dimension"

        # 4. MEASURE (numeric, high cardinality, NOT an ID)
        if self._is_measure(col_lower, type_lower, cardinality):
            return "measure"

        # 5. DIMENSION (low cardinality, categorical)
        if cardinality <= self.DIMENSION_THRESHOLD:
            return "dimension"

        # 6. DETAIL (high cardinality text)
        if self._is_detail(type_lower, cardinality):
            return "detail"

        # Default
        if self._is_numeric_type(type_lower):
            return "measure"
        return "dimension"

    def _is_primary_identifier(
        self, col_name: str, cardinality: int, row_count: int
    ) -> bool:
        """
        Check if column is a PRIMARY identifier (unique ID)
        Must be highly unique (>80%) or have very high cardinality
        """
        # Check for primary ID patterns first
        has_primary_pattern = any(p in col_name for p in self.PRIMARY_ID_PATTERNS)
        has_id_pattern = any(p in col_name for p in self.IDENTIFIER_PATTERNS)

        if not (has_primary_pattern or has_id_pattern):
            return False

        # Calculate uniqueness
        if row_count > 0:
            uniqueness = cardinality / row_count
            # Primary IDs should be highly unique
            if uniqueness > 0.8:
                return True

        # Or have very high cardinality (likely unique even without row count)
        return cardinality > 1000

    def _is_foreign_key_dimension(
        self, col_name: str, cardinality: int, row_count: int
    ) -> bool:
        """
        Check if column is a FOREIGN KEY (repeating ID used for grouping)
        These are numeric IDs but act as dimensions (categories)
        """
        # Check for foreign key patterns
        has_fk_pattern = any(p in col_name for p in self.FOREIGN_KEY_PATTERNS)
        has_id_pattern = any(p in col_name for p in self.IDENTIFIER_PATTERNS)

        if not (has_fk_pattern or has_id_pattern):
            return False

        # Foreign keys have LOW uniqueness (they repeat for grouping)
        if row_count > 0:
            uniqueness = cardinality / row_count
            # Less than 80% unique = likely a foreign key dimension
            if uniqueness < 0.8 and cardinality < 1000:
                return True

        # Low cardinality IDs are dimensions
        return cardinality <= 100

    def _is_measure(self, col_name: str, data_type: str, cardinality: int) -> bool:
        """
        Check if column is a measure (numeric value for calculations)
        """
        if not self._is_numeric_type(data_type):
            return False

        # Strong indicators this is a measure, not an ID
        if any(keyword in col_name for keyword in self.MEASURE_KEYWORDS):
            return True

        # Numeric with high cardinality (and not detected as ID earlier)
        return cardinality > self.DIMENSION_THRESHOLD

    def _is_detail(self, data_type: str, cardinality: int) -> bool:
        """Check if column is detail (high cardinality text)"""
        if self._is_numeric_type(data_type):
            return False
        return cardinality > 100

    def _is_numeric_type(self, data_type: str) -> bool:
        """Check if numeric"""
        return any(t in data_type for t in self.NUMERIC_TYPES)


# Global instance
column_type_detector = ColumnTypeDetector()
