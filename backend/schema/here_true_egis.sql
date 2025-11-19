  `covered_by_id` string, 
  `additional_info` string, 
  `coverages_core_map_link_id` bigint, 
  `ht_timestamp` timestamp, 
  `segment_id` bigint, 
  `partition_id` string, 
  `asset_id` bigint, 
  `asset_state` string, 
  `country_iso_code` string, 
  `egis_drive_date` timestamp)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/here_true_egis_10_27_2025_18_00_02/'
TBLPROPERTIES (
  'classification'='parquet', 
  'compressionType'='none', 
  'projection.enabled'='false', 
  'typeOfData'='file')
