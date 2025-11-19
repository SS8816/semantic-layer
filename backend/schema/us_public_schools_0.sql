  `x` double, 
  `y` double, 
  `fid` bigint, 
  `ncesid` bigint, 
  `name` string, 
  `address` string, 
  `address2` string, 
  `city` string, 
  `state` string, 
  `zip` bigint, 
  `zip4` string, 
  `telephone` string, 
  `type` bigint, 
  `status` bigint, 
  `population` bigint, 
  `county` string, 
  `countyfips` string, 
  `country` string, 
  `latitude` double, 
  `longitude` double, 
  `naics_code` bigint, 
  `naics_desc` string, 
  `source` string, 
  `source_dat` timestamp, 
  `val_method` string, 
  `val_date` timestamp, 
  `website` string, 
  `level_` string, 
  `enrollment` bigint, 
  `start_grad` string, 
  `end_grade` string, 
  `district_i` bigint, 
  `full_time_` bigint, 
  `shelter_id` string)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/us_public_schools_0/'
TBLPROPERTIES (
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='explorer_datasets', 
  'averageRecordSize'='319', 
  'classification'='parquet', 
  'compressionType'='none', 
  'objectCount'='1', 
  'recordCount'='103481', 
  'sizeKey'='12364252', 
  'typeOfData'='file')
