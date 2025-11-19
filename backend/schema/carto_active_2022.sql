  `region` string, 
  `carto_id` bigint, 
  `carto_version` double, 
  `carto_pvid` bigint, 
  `carto_geometry_type` string, 
  `feature_type` string, 
  `last_modified_on` timestamp, 
  `country` string, 
  `latitude` double, 
  `longitude` double, 
  `carto_length_meters` double, 
  `extended_attribute_expanded_inclusion` string)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/carto_active_2022/'
TBLPROPERTIES (
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='explorer_datasets', 
  'averageRecordSize'='34', 
  'classification'='parquet', 
  'compressionType'='none', 
  'objectCount'='6', 
  'recordCount'='68355056', 
  'sizeKey'='2436194140', 
  'typeOfData'='file')
