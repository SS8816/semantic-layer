  `asset_id` bigint, 
  `asset_name` string, 
  `asset_state` string, 
  `iso_country_code` string, 
  `run_id` string, 
  `drive_distance_ft` double, 
  `redrive_candidate_reason` string, 
  `vehicle_type` string, 
  `multicamera_count` bigint, 
  `create_date_utc` timestamp, 
  `drive_available_date_utc` timestamp, 
  `asset_state_date_utc` timestamp, 
  `hardware_setup` string, 
  `for_rwt` boolean, 
  `is_deleted` boolean, 
  `drive_bbox_centroid_latitude` double, 
  `drive_bbox_centroid_longitude` double)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/egis_drives_latest_08_02_2023_01_25_01/'
TBLPROPERTIES (
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='explorer_datasets', 
  'averageRecordSize'='84', 
  'classification'='parquet', 
  'compressionType'='none', 
  'objectCount'='1', 
  'recordCount'='2089266', 
  'sizeKey'='177177595', 
  'typeOfData'='file')
