  `ws_region` string, 
  `admin_l1_display_name` string, 
  `admin_l2_display_name` string, 
  `admin_l3_display_name` string, 
  `feature_point_pvid` bigint, 
  `link_pvid` bigint, 
  `fpt_type` string, 
  `latitude` decimal(25,7), 
  `longitude` decimal(25,7))
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/natural_guidance/'
TBLPROPERTIES (
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='explorer_datasets', 
  'averageRecordSize'='30', 
  'classification'='parquet', 
  'compressionType'='none', 
  'objectCount'='24', 
  'recordCount'='775083', 
  'sizeKey'='24056566', 
  'typeOfData'='file')
