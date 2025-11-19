  `building_id` string, 
  `iso_country_code` string, 
  `type` string, 
  `type_description` string, 
  `latitude` double, 
  `longitude` double, 
  `max_building_height` double)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/building_footprints_2d_2022_old/'
TBLPROPERTIES (
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='explorer_datasets', 
  'averageRecordSize'='30', 
  'classification'='parquet', 
  'compressionType'='none', 
  'objectCount'='256', 
  'recordCount'='394474217', 
  'sizeKey'='11881778703', 
  'typeOfData'='file')
