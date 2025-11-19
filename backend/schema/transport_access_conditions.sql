  `ws_region` string, 
  `condition_rmob_id` bigint, 
  `applies_to_trucks` boolean, 
  `applies_to_through_traffic` boolean, 
  `applies_to_deliveries` boolean, 
  `link_rmob_id` bigint, 
  `functional_class` decimal, 
  `tunnel` boolean, 
  `bridge` boolean, 
  `long_haul` boolean, 
  `travel_direction` string, 
  `access_autos` boolean, 
  `access_deliveries` boolean, 
  `access_trucks` boolean, 
  `access_through_traffic` boolean, 
  `display_delivery_road` boolean, 
  `display_motorway` boolean, 
  `display_limited_access_road` boolean, 
  `special_attr_transport_verified` boolean, 
  `shape_vector` string, 
  `longitude` double, 
  `latitude` double, 
  `link_length_meters` decimal, 
  `country` string, 
  `admin_level2` string, 
  `admin_level3` string, 
  `admin_level4` string, 
  `date_time_modifier` string, 
  `transport_ar_time_override` string, 
  `transport_ar_direction_closure` string, 
  `transport_ar_hazmat_type` string, 
  `transport_ar_trailer_type` string, 
  `transport_ar_physical_structure_type` string, 
  `transport_ar_weather_type` string, 
  `transport_ar_restriction_type` string, 
  `transport_ar_number_of_axles` bigint, 
  `transport_ar_hazmat_permit_required` bigint, 
  `transport_ar_restriction_value` bigint)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/transport_access_conditions_01_09_2024_17_01_05/'
TBLPROPERTIES (
  'classification'='parquet', 
  'compressionType'='none', 
  'projection.enabled'='false', 
  'typeOfData'='file')
