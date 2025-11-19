  `region` string, 
  `condition_id` bigint, 
  `country` string, 
  `admin_level2_name` string, 
  `admin_level3_name` string, 
  `admin_level4_name` string, 
  `condition_type` string, 
  `rdm_type` string, 
  `condition_wkt` string, 
  `longitude` double, 
  `latitude` double)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/all_rdms_2023_01_10_2024_13_10_15/'
TBLPROPERTIES (
  'classification'='parquet', 
  'compressionType'='none', 
  'projection.enabled'='false', 
  'typeOfData'='file')
