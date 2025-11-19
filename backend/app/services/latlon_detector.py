"""
Latitude and Longitude detection service
"""
from typing import List, Any
import pandas as pd
from app.utils.logger import app_logger as logger


class LatLonDetector:
    """Service for detecting latitude and longitude columns"""
    
    @staticmethod
    def is_latitude(values: List[Any]) -> bool:
        """
        Detect if values represent latitude coordinates
        
        Latitude range: -90 to 90
        
        Args:
            values: List of values to check
            
        Returns:
            True if values appear to be latitude, False otherwise
        """
        if not values:
            return False
        
        try:
            # Filter out None/null values
            numeric_values = [v for v in values if v is not None]
            
            if not numeric_values:
                return False
            
            # Convert to float
            numeric_values = [float(v) for v in numeric_values]
            
            # Check if all values are within latitude range
            min_val = min(numeric_values)
            max_val = max(numeric_values)
            
            # Valid latitude range: -90 to 90
            if min_val < -90 or max_val > 90:
                return False
            
            # Check if at least some values are non-zero (to avoid false positives)
            non_zero_count = sum(1 for v in numeric_values if abs(v) > 0.0001)
            if non_zero_count == 0:
                return False
            
            # Additional heuristic: check if values have reasonable distribution
            # Real latitude data typically has some variance
            if len(numeric_values) > 10:
                std_dev = pd.Series(numeric_values).std()
                if std_dev < 0.001:  # Too uniform, probably not lat
                    return False
            
            # Check percentage of values in valid range
            valid_count = sum(1 for v in numeric_values if -90 <= v <= 90)
            valid_percentage = valid_count / len(numeric_values)
            
            # At least 95% of values should be in valid range
            if valid_percentage >= 0.95:
                logger.debug(f"Detected latitude: min={min_val:.2f}, max={max_val:.2f}, valid%={valid_percentage:.2%}")
                return True
            
            return False
        
        except (ValueError, TypeError) as e:
            logger.debug(f"Not a latitude column: {e}")
            return False
    
    @staticmethod
    def is_longitude(values: List[Any]) -> bool:
        """
        Detect if values represent longitude coordinates
        
        Longitude range: -180 to 180
        
        Args:
            values: List of values to check
            
        Returns:
            True if values appear to be longitude, False otherwise
        """
        if not values:
            return False
        
        try:
            # Filter out None/null values
            numeric_values = [v for v in values if v is not None]
            
            if not numeric_values:
                return False
            
            # Convert to float
            numeric_values = [float(v) for v in numeric_values]
            
            # Check if all values are within longitude range
            min_val = min(numeric_values)
            max_val = max(numeric_values)
            
            # Valid longitude range: -180 to 180
            if min_val < -180 or max_val > 180:
                return False
            
            # Check if at least some values are non-zero (to avoid false positives)
            non_zero_count = sum(1 for v in numeric_values if abs(v) > 0.0001)
            if non_zero_count == 0:
                return False
            
            # Additional heuristic: check if values have reasonable distribution
            # Real longitude data typically has some variance
            if len(numeric_values) > 10:
                std_dev = pd.Series(numeric_values).std()
                if std_dev < 0.001:  # Too uniform, probably not lon
                    return False
            
            # Check percentage of values in valid range
            valid_count = sum(1 for v in numeric_values if -180 <= v <= 180)
            valid_percentage = valid_count / len(numeric_values)
            
            # At least 95% of values should be in valid range
            if valid_percentage >= 0.95:
                logger.debug(f"Detected longitude: min={min_val:.2f}, max={max_val:.2f}, valid%={valid_percentage:.2%}")
                return True
            
            return False
        
        except (ValueError, TypeError) as e:
            logger.debug(f"Not a longitude column: {e}")
            return False
    
    @staticmethod
    def is_numeric_type(data_type: str) -> bool:
        """
        Check if a data type is numeric (suitable for lat/lon)
        
        Args:
            data_type: Data type string
            
        Returns:
            True if numeric, False otherwise
        """
        numeric_types = [
            'INTEGER', 'BIGINT', 'SMALLINT', 'TINYINT',
            'REAL', 'DOUBLE', 'FLOAT', 'DECIMAL', 'NUMERIC'
        ]
        
        data_type_upper = data_type.upper()
        
        # Check if base type (before parentheses) is numeric
        base_type = data_type_upper.split('(')[0].strip()
        
        return base_type in numeric_types
    
    @staticmethod
    def detect_from_column_name(column_name: str) -> str | None:
        """
        Detect lat/lon from column name patterns
        
        Args:
            column_name: Name of the column
            
        Returns:
            'latitude' or 'longitude' or None
        """
        column_lower = column_name.lower()
        
        # Latitude patterns
        lat_patterns = ['lat', 'latitude', '_lat_', 'lat_', '_lat']
        if any(pattern in column_lower for pattern in lat_patterns):
            # Exclude longitude patterns that might contain 'lat'
            if 'lon' not in column_lower and 'lng' not in column_lower:
                return 'latitude'
        
        # Longitude patterns
        lon_patterns = ['lon', 'lng', 'longitude', '_lon_', 'lon_', '_lon', '_lng_', 'lng_', '_lng']
        if any(pattern in column_lower for pattern in lon_patterns):
            return 'longitude'
        
        return None


# Global detector instance
latlon_detector = LatLonDetector()