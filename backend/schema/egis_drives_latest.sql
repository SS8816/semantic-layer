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
  `project_size` bigint, 
  `min_timestamp_utc` timestamp, 
  `storage_key` string, 
  `for_rwt` boolean, 
  `is_deleted` boolean, 
  `drive_bbox_centroid_latitude` double, 
  `drive_bbox_centroid_longitude` double, 
  `egis_drive_date` timestamp, 
  `project_type` string, 
  `dfp_drive_status` string, 
  `dfp_drive_status_date_utc` timestamp, 
  `last_update_date_utc` timestamp)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/egis_drives_latest_10_27_2025_17_00_02/'
TBLPROPERTIES (
  'classification'='parquet', 
  'compressionType'='none', 
  'projection.enabled'='false', 
  'typeOfData'='file')
