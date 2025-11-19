  `region` string, 
  `country` string, 
  `admin_level_2` string, 
  `admin_level_3` string, 
  `admin_level_4` string, 
  `condition_pvid` bigint, 
  `attribute_type` string, 
  `attribute_value` string, 
  `link_pvid` bigint, 
  `functional_class` string, 
  `intersection_category` string, 
  `latitude` decimal(8,5), 
  `longitude` decimal(8,5))
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/navmap_signs_apac_231C0/'
TBLPROPERTIES (
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='explorer_datasets', 
  'averageRecordSize'='20', 
  'classification'='parquet', 
  'compressionType'='none', 
  'objectCount'='1', 
  'recordCount'='789588', 
  'sizeKey'='16553523', 
  'typeOfData'='file')
