  `partition_id` string, 
  `region` string, 
  `sub_region` string, 
  `country` string, 
  `country_iso_code` string, 
  `county` string, 
  `state` string, 
  `city` string, 
  `agency_id` string, 
  `agency_name` string, 
  `route_type_name` string, 
  `route_id` string, 
  `stop_id` string, 
  `stop_name` string, 
  `stop_lat` double, 
  `stop_lon` double, 
  `stop_code` string)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/gtfs_12_10_2024_22_37_57/'
TBLPROPERTIES (
  'classification'='parquet', 
  'compressionType'='none', 
  'projection.enabled'='false', 
  'typeOfData'='file')
