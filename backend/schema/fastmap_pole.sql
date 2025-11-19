  `pole_id` string, 
  `tile_id` bigint, 
  `version` bigint, 
  `iso_country_code` string, 
  `pole_type` string, 
  `latitude` double, 
  `longitude` double, 
  `last_updated_at` timestamp)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/fastmap_pole/'
TBLPROPERTIES (
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='explorer_datasets', 
  'averageRecordSize'='70', 
  'classification'='parquet', 
  'compressionType'='none', 
  'objectCount'='30', 
  'recordCount'='5767321', 
  'sizeKey'='216512780', 
  'typeOfData'='file')
