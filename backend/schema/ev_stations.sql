  `pool_id` string, 
  `station_id` string, 
  `number_of_evses` bigint, 
  `is_open24_hours` boolean, 
  `charging_when_closed` boolean, 
  `accessibility_type` string, 
  `country_iso_code` string, 
  `admin_level1` string, 
  `admin_level2` string, 
  `admin_level3` string, 
  `admin_level4` string, 
  `admin_level5` string, 
  `latitude` double, 
  `longitude` double, 
  `link_pvid` string, 
  `map_version` string, 
  `station_label` string, 
  `manufacturer` string, 
  `station_type` string, 
  `station_name` string)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/ev_stations/'
TBLPROPERTIES (
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='explorer_datasets', 
  'averageRecordSize'='159', 
  'classification'='parquet', 
  'compressionType'='none', 
  'objectCount'='30', 
  'recordCount'='319456', 
  'sizeKey'='34124812', 
  'typeOfData'='file')
