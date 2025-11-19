  `ws_region` string, 
  `environmental_zone_id` bigint, 
  `environmental_zone_name` string, 
  `condition_rmob_id` bigint, 
  `condition_pvid` bigint, 
  `link_rmob_id` bigint, 
  `link_pvid` bigint, 
  `shape_vector` string, 
  `longitude` double, 
  `latitude` double, 
  `functional_class` decimal, 
  `coverage_indicator` string, 
  `admin_l1_display_name` string, 
  `admin_l2_display_name` string, 
  `admin_l3_display_name` string)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/condition_environmental_zones_2025_10_15_2025_22_30_01/'
TBLPROPERTIES (
  'classification'='parquet', 
  'compressionType'='none', 
  'projection.enabled'='false', 
  'typeOfData'='file')
