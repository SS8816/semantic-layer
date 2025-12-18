"""
Enhanced geographic detection service - Returns semantic_type
"""

import json
import re
import time
from typing import Any, Dict, List, Optional

import pycountry
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from geopy.geocoders import Nominatim

from app.utils.logger import app_logger as logger


class GeographicDetector:
    """
    Detect semantic type of geographic columns
    Returns: country, state, city, locality, latitude, longitude, wkt_geometry, geojson_geometry, geometry_type, or None
    """

    # Valid geometry types
    GEOMETRY_TYPES = {
        "point",
        "linestring",
        "polygon",
        "multipoint",
        "multilinestring",
        "multipolygon",
        "geometrycollection",
    }

    def __init__(self):
        """Initialize geographic detector with databases"""
        self.countries = {c.name.lower() for c in pycountry.countries}
        self.country_codes_alpha2 = {c.alpha_2.lower() for c in pycountry.countries}
        self.country_codes_alpha3 = {c.alpha_3.lower() for c in pycountry.countries}
        self.geolocator = Nominatim(user_agent="metadata_explorer", timeout=3)
        self.geocode_cache = {}

        logger.info(f"Geographic detector initialized: {len(self.countries)} countries")

    def detect_semantic_type(
        self,
        column_name: str,
        data_type: str,
        sample_values: List[Any],
        min_value: Any = None,
        max_value: Any = None,
        cardinality: int = 0,
    ) -> Optional[str]:
        """
        Detect semantic type for a column

        Returns:
            'country', 'state', 'city', 'locality', 'latitude', 'longitude',
            'wkt_geometry', 'geojson_geometry', 'geometry_type', or None
        """
        col_lower = column_name.lower()

        # EXCLUDE temporal columns (day, month, year, date)
        temporal_keywords = ["day", "month", "year", "date", "time", "timestamp"]
        if any(kw in col_lower for kw in temporal_keywords):
            return None

        # EXCLUDE distance/measurement columns
        if self._is_distance_column(col_lower, data_type):
            return None

        # EXCLUDE address range columns
        if "address" in col_lower and "range" in col_lower:
            return None

        # EXCLUDE code-like columns (e.g., "APAC_MAP_231C0")
        if self._is_code_column(col_lower, sample_values, cardinality):
            return None

        # GEOMETRY TYPE COLUMN (just type names: "Point", "Polygon", etc.)
        if self._is_geometry_type_column(col_lower, sample_values):
            return "geometry_type"

        # GEOJSON DETECTION (must check before WKT because GeoJSON is more specific)
        if self._is_geojson_column(col_lower, data_type, sample_values):
            return "geojson_geometry"

        # WKT / MODIFIED GEOMETRY DETECTION
        if self._is_wkt_geometry_column(col_lower, data_type, sample_values):
            return "wkt_geometry"

        # LATITUDE DETECTION
        if self._is_latitude_column(
            col_lower, data_type, sample_values, min_value, max_value
        ):
            return "latitude"

        # LONGITUDE DETECTION
        if self._is_longitude_column(
            col_lower, data_type, sample_values, min_value, max_value
        ):
            return "longitude"

        # COUNTRY DETECTION
        if self._is_country_column(col_lower, data_type, sample_values):
            return "country"

        # ADMINISTRATIVE REGION DETECTION (state/city only for text columns)
        if data_type in ["varchar", "string", "text"]:
            admin_type = self._detect_administrative_type(
                col_lower, sample_values, cardinality
            )
            if admin_type:
                return admin_type  # 'state' or 'city'

        return None

    def _is_geometry_type_column(self, col_name: str, sample_values: List[Any]) -> bool:
        """
        Detect if column contains only geometry type names
        Examples: "Point", "Polygon", "MultiPolygon"
        """
        type_keywords = [
            "geo_type",
            "geotype",
            "geometry_type",
            "geom_type",
            "shape_type",
        ]
        if not any(kw in col_name for kw in type_keywords):
            return False

        if not sample_values:
            return False

        # Check if most values are geometry types
        match_count = 0
        for val in sample_values[:20]:
            if not val:
                continue
            val_str = str(val).strip().lower()
            if val_str in self.GEOMETRY_TYPES:
                match_count += 1

        # 70%+ must be valid geometry types
        sample_count = len(sample_values[:20])
        threshold = sample_count * 0.3

        return match_count >= threshold

    def _is_geojson_column(
        self, col_name: str, data_type: str, sample_values: List[Any]
    ) -> bool:
        """
        Detect GeoJSON format columns
        Valid GeoJSON: {"type":"Point","coordinates":[lon, lat]}
        """
        # Column name hints
        geojson_keywords = ["geojson", "geo_json", "json_geometry"]
        has_name_hint = any(kw in col_name for kw in geojson_keywords)

        # Check generic geometry column names too
        geometry_keywords = ["geometry", "geom", "shape", "location"]
        has_geometry_hint = any(kw in col_name for kw in geometry_keywords)

        if not (has_name_hint or has_geometry_hint):
            return False

        # Data type must be text-based or JSON
        data_type_upper = data_type.upper()
        is_valid_type = any(
            t in data_type_upper for t in ["VARCHAR", "STRING", "TEXT", "JSON"]
        )

        if not is_valid_type:
            return False

        logger.info(f"Checking GeoJSON for column: {col_name}, data_type: {data_type}")
        if not sample_values:
            logger.info(f"No sample values for {col_name}")
            return False

        # Check sample values
        valid_count = 0
        for val in sample_values[:10]:
            if not val:
                continue
            try:
                val_str = str(val).strip()
                # Try parsing as JSON
                obj = json.loads(val_str)
                # Must be a dict with 'type' and 'coordinates'
                if isinstance(obj, dict) and "type" in obj and "coordinates" in obj:
                    geom_type = obj["type"].lower()
                    if geom_type in self.GEOMETRY_TYPES:
                        valid_count += 1
                        logger.debug(f"Found valid GeoJSON: {geom_type}")
            except (json.JSONDecodeError, ValueError, AttributeError) as e:
                logger.debug(f"Failed to parse GeoJSON: {e}")
                continue

        logger.info(
            f"GeoJSON check for {col_name}: {valid_count}/{len(sample_values[:10])} valid"
        )
        # 30%+ must be valid GeoJSON
        return valid_count >= max(3, len(sample_values[:10]) * 0.3)

    def _is_wkt_geometry_column(
        self, col_name: str, data_type: str, sample_values: List[Any]
    ) -> bool:
        """
        Detect WKT or modified geometry format columns

        Valid formats:
        - Standard WKT: POINT(lon lat), POLYGON((lon lat, ...))
        - Modified: {type=Point, coordinates=[lon, lat]}
        """
        # Column name hints
        geometry_keywords = ["geometry", "geom", "shape", "wkt", "location"]
        if not any(kw in col_name for kw in geometry_keywords):
            return False

        # Data type must be text-based OR struct (for nested geometry)
        data_type_upper = data_type.upper()
        is_valid_type = any(
            t in data_type_upper for t in ["VARCHAR", "STRING", "TEXT", "STRUCT", "ROW"]
        )

        if not is_valid_type:
            return False

        # If it's a struct with 'type' and 'coordinates', it's geometry
        if "STRUCT" in data_type_upper or "ROW" in data_type_upper:
            if "type" in data_type.lower() and "coordinates" in data_type.lower():
                return True

        if not sample_values:
            return False

        # Check sample values
        valid_count = 0
        for val in sample_values[:10]:
            if not val:
                continue

            val_str = str(val).strip()

            # Check for standard WKT format: POINT(...), POLYGON(...), etc.
            wkt_pattern = r"^(POINT|LINESTRING|POLYGON|MULTIPOINT|MULTILINESTRING|MULTIPOLYGON|GEOMETRYCOLLECTION)\s*\("
            if re.match(wkt_pattern, val_str, re.IGNORECASE):
                valid_count += 1
                continue

            # Check for modified format: {type=..., coordinates=...}
            if (
                val_str.startswith("{")
                and "type=" in val_str
                and "coordinates=" in val_str
            ):
                # Extract type value
                type_match = re.search(r"type=(\w+)", val_str, re.IGNORECASE)
                if type_match:
                    geom_type = type_match.group(1).lower()
                    if geom_type in self.GEOMETRY_TYPES:
                        valid_count += 1
                        continue

        # 30%+ must be valid geometry format
        return valid_count >= max(3, len(sample_values[:10]) * 0.3)

    def _is_distance_column(self, col_name: str, data_type: str) -> bool:
        """Check if column represents distance/measurement"""
        distance_keywords = [
            "km",
            "kilometer",
            "mile",
            "meter",
            "distance",
            "length",
            "total_km",
            "total",
        ]
        return any(kw in col_name for kw in distance_keywords)

    def _is_code_column(
        self, col_name: str, sample_values: List[Any], cardinality: int
    ) -> bool:
        """Check if column contains code-like values (not place names)"""
        if cardinality > 5 or not sample_values:
            return False

        code_pattern_count = 0
        for val in sample_values[:5]:
            if not val:
                continue
            val_str = str(val).upper()
            # Check for code patterns: underscores, numbers, all caps
            if "_" in val_str or any(char.isdigit() for char in val_str):
                if val_str == val_str.upper():
                    code_pattern_count += 1

        # If 60%+ look like codes, it's a code column
        return code_pattern_count >= len(sample_values[:5]) * 0.6

    def _has_lat_lon_pattern(self, col_name: str) -> bool:
        """Check if column name suggests latitude/longitude"""
        lat_patterns = ["lat", "latitude", "_lat", "lat_"]
        lon_patterns = ["lon", "lng", "longitude", "_lon", "_lng", "lon_", "lng_"]
        return any(p in col_name for p in lat_patterns + lon_patterns)

    def _is_latitude_column(
        self,
        col_name: str,
        data_type: str,
        sample_values: List[Any],
        min_value: Any,
        max_value: Any,
    ) -> bool:
        """Detect latitude column"""
        lat_patterns = ["lat", "latitude", "_lat", "lat_"]
        has_lat_pattern = any(p in col_name for p in lat_patterns)

        is_numeric = data_type in ["double", "float", "decimal", "real"]

        if not is_numeric or not has_lat_pattern:
            return False

        # Verify value range [-90, 90]
        try:
            if min_value is not None and max_value is not None:
                if -90 <= float(min_value) <= 90 and -90 <= float(max_value) <= 90:
                    return True
        except (ValueError, TypeError):
            pass

        # Check sample values
        valid_count = sum(
            1
            for val in sample_values[:10]
            if val is not None and -90 <= float(val) <= 90
        )

        return valid_count >= 5

    def _is_longitude_column(
        self,
        col_name: str,
        data_type: str,
        sample_values: List[Any],
        min_value: Any,
        max_value: Any,
    ) -> bool:
        """Detect longitude column"""
        lon_patterns = ["lon", "lng", "longitude", "_lon", "_lng", "lon_", "lng_"]
        has_lon_pattern = any(p in col_name for p in lon_patterns)

        is_numeric = data_type in ["double", "float", "decimal", "real"]

        if not is_numeric or not has_lon_pattern:
            return False

        # Verify value range [-180, 180]
        try:
            if min_value is not None and max_value is not None:
                if -180 <= float(min_value) <= 180 and -180 <= float(max_value) <= 180:
                    return True
        except (ValueError, TypeError):
            pass

        # Check sample values
        valid_count = sum(
            1
            for val in sample_values[:10]
            if val is not None and -180 <= float(val) <= 180
        )

        return valid_count >= 5

    def _is_country_column(
        self, col_name: str, data_type: str, sample_values: List[Any]
    ) -> bool:
        """Detect country column"""
        if "country" not in col_name:
            return False

        if data_type not in ["varchar", "string", "text"]:
            return False

        match_count = sum(
            1 for val in sample_values[:20] if val and self._is_country_value(str(val))
        )

        return match_count >= min(10, len(sample_values) * 0.5)

    def _is_country_value(self, value: str) -> bool:
        """Check if value is a country name or code"""
        val_lower = value.lower().strip()

        if val_lower in self.countries:
            return True
        if val_lower in self.country_codes_alpha2:
            return True
        if val_lower in self.country_codes_alpha3:
            return True

        # Fuzzy match
        for country in self.countries:
            if val_lower in country or country in val_lower:
                return True

        return False

    def _detect_administrative_type(
        self, col_name: str, sample_values: List[Any], cardinality: int
    ) -> Optional[str]:
        """
        Detect administrative type: 'state', 'city', or 'locality'

        Returns:
            'state' for provinces/states, 'city' for cities, 'locality' for districts, None otherwise
        """
        # Pattern-based detection (with underscore support)
        # Level 2: State/Province
        if any(
            x in col_name
            for x in ["province", "state", "admin_level_2", "admin_level2", "admin_l2", "level_2", "level2"]
        ):
            return "state"

        # Level 3: City/Town
        if any(
            x in col_name
            for x in [
                "city",
                "town",
                "municipality",
                "admin_level_3",
                "admin_level3",
                "admin_l3",
                "level_3",
                "level3",
            ]
        ):
            return "city"

        # Level 4: District/Locality/Neighborhood
        if any(
            x in col_name
            for x in [
                "district",
                "locality",
                "neighborhood",
                "neighbourhood",
                "admin_level_4",
                "admin_level4",
                "admin_l4",
                "level_4",
                "level4",
            ]
        ):
            return "locality"

        # Content-based detection (extended cardinality range for POI datasets)
        # Only use for columns that might be administrative (avoid false positives)
        if 10 <= cardinality <= 200000 and self._looks_like_admin_column(col_name):
            place_match_count = self._count_place_matches(sample_values[:20])

            if place_match_count >= 5:
                # Infer level based on cardinality
                if cardinality < 500:
                    return "state"
                elif cardinality < 50000:
                    return "city"
                else:
                    return "locality"

        return None

    def _looks_like_admin_column(self, col_name: str) -> bool:
        """Check if column name suggests administrative/geographic data"""
        admin_keywords = [
            "admin", "region", "area", "zone", "location", "place",
            "province", "state", "city", "town", "district", "county"
        ]
        # Exclude non-geographic columns
        exclude_keywords = [
            "type", "category", "feature", "class", "kind", "code",
            "id", "name", "description", "address", "street"
        ]

        has_admin_keyword = any(kw in col_name for kw in admin_keywords)
        has_exclude_keyword = any(kw in col_name for kw in exclude_keywords)

        return has_admin_keyword and not has_exclude_keyword

    def _count_place_matches(self, sample_values: List[Any]) -> int:
        """Count how many values match known places (with rate limiting)"""
        match_count = 0

        for val in sample_values[:10]:
            if not val:
                continue

            val_str = str(val).strip()

            if val_str in self.geocode_cache:
                if self.geocode_cache[val_str]:
                    match_count += 1
                continue

            try:
                time.sleep(0.1)
                location = self.geolocator.geocode(
                    val_str, exactly_one=True, addressdetails=True
                )

                if location:
                    self.geocode_cache[val_str] = True
                    match_count += 1
                else:
                    self.geocode_cache[val_str] = False

            except (GeocoderTimedOut, GeocoderUnavailable):
                self.geocode_cache[val_str] = True
                match_count += 0.5
            except Exception:
                self.geocode_cache[val_str] = False

        return int(match_count)


geographic_detector = GeographicDetector()
