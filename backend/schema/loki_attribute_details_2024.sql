  `object_id` string, 
  `mcw_attribute` string, 
  `ws_name` string, 
  `ws_region` string, 
  `version` double, 
  `view_start_date` timestamp, 
  `kernel` string, 
  `operation` string, 
  `attr_id` bigint, 
  `admin_rmob_id` string, 
  `admin_l3_rmob_id` bigint, 
  `admin_l1_display_name` string, 
  `admin_l2_display_name` string, 
  `admin_l3_display_name` string, 
  `admin_l4_display_name` string, 
  `user_id` bigint, 
  `source_id` string, 
  `functional_class` decimal, 
  `link_length_meters` decimal, 
  `feature_type` bigint, 
  `project_task_id` bigint, 
  `country_iso_code` string, 
  `task_code` bigint)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/loki_attribute_details_2024_05_10_2024_02_02_09/'
TBLPROPERTIES (
  'classification'='parquet', 
  'compressionType'='none', 
  'projection.enabled'='false', 
  'typeOfData'='file')
