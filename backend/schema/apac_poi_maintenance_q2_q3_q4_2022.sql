  `year` bigint, 
  `quarter` string, 
  `category` string, 
  `poi_name` string, 
  `latitude` double, 
  `longitude` double, 
  `region` string, 
  `country` string, 
  `action` string, 
  `scope` string, 
  `poi_pvid_place_id` string)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/apac_poi_maintenance_q2_q3_q4_2022/'
TBLPROPERTIES (
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='explorer_datasets', 
  'averageRecordSize'='51', 
  'classification'='parquet', 
  'compressionType'='none', 
  'objectCount'='1', 
  'recordCount'='71392', 
  'sizeKey'='2741470', 
  'typeOfData'='file')
