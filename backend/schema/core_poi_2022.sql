  `poi_id` bigint, 
  `longitude` double, 
  `latitude` double, 
  `country_code` string, 
  `admin_level_2` string, 
  `admin_level_3` string, 
  `admin_level_4` string, 
  `feature_type` string, 
  `chains` string, 
  `has_phone_number` boolean, 
  `timestamp_of_last_update` timestamp, 
  `has_h24x7` boolean, 
  `has_note` boolean, 
  `has_url` boolean, 
  `names` string, 
  `has_name` boolean, 
  `carto_feature` string, 
  `data_source` bigint, 
  `has_display_coordinates` boolean, 
  `has_routing_coordinates` boolean)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/core_poi_2022/'
TBLPROPERTIES (
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='explorer_datasets', 
  'averageRecordSize'='48', 
  'classification'='parquet', 
  'compressionType'='none', 
  'objectCount'='6', 
  'recordCount'='49484857', 
  'sizeKey'='2469623099', 
  'typeOfData'='file')
