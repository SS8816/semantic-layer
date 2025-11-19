  `condition_pvid` bigint, 
  `condition_rmob_id` bigint, 
  `ws_region` string, 
  `link_rmob_id` bigint, 
  `toll_structure_type` string, 
  `toll_method` string, 
  `toll_structure_toll_cost_id` bigint, 
  `longitude` double, 
  `latitude` double, 
  `iso_country_code` string, 
  `country` string, 
  `admin_level2` string, 
  `admin_level3` string, 
  `admin_level4` string)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/condition_tolls_latest_10_21_2025_22_30_02/'
TBLPROPERTIES (
  'classification'='parquet', 
  'compressionType'='none', 
  'projection.enabled'='false', 
  'typeOfData'='file')
