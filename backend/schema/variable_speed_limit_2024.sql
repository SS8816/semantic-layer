  `condition_rmob_id` bigint, 
  `ws_region` string, 
  `country` string, 
  `admin_l2_display_name` string, 
  `admin_l3_display_name` string, 
  `vsl_direction_of_travel` string, 
  `link_rmob_id` bigint, 
  `functional_class` decimal, 
  `total_kms` double, 
  `shape_vector` string, 
  `latitude` double, 
  `longitude` double, 
  `admin_l1_pvid` bigint, 
  `admin_l2_pvid` bigint, 
  `admin_l3_pvid` bigint)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/variable_speed_limit_2024_12_17_2024_07_30_02/'
TBLPROPERTIES (
  'classification'='parquet', 
  'compressionType'='none', 
  'projection.enabled'='false', 
  'typeOfData'='file')
