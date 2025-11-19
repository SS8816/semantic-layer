  `child_area_of_interest_code` string, 
  `child_area_of_interest_name` string, 
  `collection_year` string, 
  `state` string, 
  `country` string, 
  `area_square_km` double, 
  `here_prior` string, 
  `delivery_state` string, 
  `delivery_date` string, 
  `gsd` string, 
  `geometry` string, 
  `shape_file_name` string, 
  `longitude` double, 
  `latitude` double)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/vexcel_aerial_imagery/vexcel_aerial_imagery'
TBLPROPERTIES (
  'auto.purge'='false', 
  'has_encrypted_data'='false', 
  'numFiles'='-1', 
  'parquet.compression'='SNAPPY', 
  'presto_query_id'='20230605_183017_00074_nywuq', 
  'presto_version'='0.215-18065-ge2f002b', 
  'totalSize'='-1', 
  'transactional'='false')
