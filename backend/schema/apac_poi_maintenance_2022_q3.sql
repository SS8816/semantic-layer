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
  's3://explorer-datasets-sources-prod/parquet_sources/apac_poi_maintenance_2022_q3/'
TBLPROPERTIES (
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='explorer_datasets', 
  'averageRecordSize'='52', 
  'classification'='parquet', 
  'compressionType'='none', 
  'objectCount'='2', 
  'recordCount'='103008', 
  'sizeKey'='2030202', 
  'typeOfData'='file')
