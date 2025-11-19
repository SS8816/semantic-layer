  `metadata_version` string, 
  `metadata_change_id` bigint, 
  `domain_name` string, 
  `domain_long_name` string, 
  `domain_short_name` string, 
  `domain_published_name` string, 
  `value_type` string, 
  `published_value_type` string, 
  `domain_type` string, 
  `value_long_name` string, 
  `value_short_name` string, 
  `value` string, 
  `published_value` string, 
  `published` boolean)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/rmob_metadata_mcw_metadata_10_21_2025_20_00_02/'
TBLPROPERTIES (
  'classification'='parquet', 
  'compressionType'='none', 
  'projection.enabled'='false', 
  'typeOfData'='file')
