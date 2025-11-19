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
  's3://explorer-datasets-sources-prod/parquet_sources/vexcel_aerial_imagery_fdwa_06_15_2023_21_33_43/'
TBLPROPERTIES (
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='explorer_datasets', 
  'averageRecordSize'='1748', 
  'classification'='parquet', 
  'compressionType'='none', 
  'objectCount'='1', 
  'recordCount'='670', 
  'sizeKey'='641220', 
  'typeOfData'='file')
