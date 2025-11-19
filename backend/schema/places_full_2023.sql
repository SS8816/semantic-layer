  `place_id` string, 
  `place_partition` string, 
  `as_of` timestamp, 
  `last_changed_at` timestamp, 
  `link_pvid` string, 
  `categories` string, 
  `chains` string, 
  `suppliers` string, 
  `latitude` decimal, 
  `longitude` decimal, 
  `names` string, 
  `tqs_isopen` bigint, 
  `tqs_isaddresscorrect` bigint, 
  `tqs_isplace` bigint, 
  `tqs_isnamecorrect` bigint, 
  `tqs_isphonecorrect` bigint, 
  `tqs_overallscore` bigint, 
  `is_core` boolean, 
  `core_poi_count` bigint, 
  `core_poi_ids` string, 
  `has_url` boolean, 
  `has_name` boolean, 
  `has_display_coordinates` boolean, 
  `has_routing_coordinates` boolean, 
  `has_h24x7` boolean, 
  `has_hours` boolean, 
  `has_note` boolean, 
  `admin_l1_pvid` bigint, 
  `admin_l2_pvid` bigint, 
  `admin_l3_pvid` bigint, 
  `admin_level_2` string, 
  `admin_level_3` string, 
  `admin_level_4` string, 
  `country_iso_code` string, 
  `is_encumbered` boolean)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/places_full_2023_01_10_2024_04_10_31/'
TBLPROPERTIES (
  'classification'='parquet', 
  'compressionType'='none', 
  'projection.enabled'='false', 
  'typeOfData'='file')
