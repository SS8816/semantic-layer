  `ws_region` string, 
  `version` string, 
  `carto_rmob_id` string, 
  `max_height` bigint, 
  `building_type` string, 
  `longitude` double, 
  `latitude` double, 
  `country_iso_code` string, 
  `admin_l1_display_name` string, 
  `admin_l2_display_name` string, 
  `admin_l3_display_name` string, 
  `admin_l4_display_name` string, 
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
  's3://explorer-datasets-sources-prod/parquet_sources/building_2d_2024_12_16_2024_02_30_02/'
TBLPROPERTIES (
  'classification'='parquet', 
  'compressionType'='none', 
  'projection.enabled'='false', 
  'typeOfData'='file')
