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
  `functional_class` bigint, 
  `link_length_meters` decimal, 
  `feature_type` bigint, 
  `project_task_id` bigint, 
  `country_iso_code` string, 
  `task_code` bigint, 
  `year` double, 
  `month` double, 
  `username` string, 
  `user_group` string, 
  `edit_method` string, 
  `golden_region` string, 
  `golden_sub_region` string, 
  `golden_iso3_code` string, 
  `attribute_display_name` string, 
  `attribute_group` string, 
  `attribute_sub_group` string, 
  `proposed_business_value` decimal, 
  `workstream` string, 
  `work_order_descr` string, 
  `effort_type` string, 
  `wo_code` string, 
  `source_type` string, 
  `hl_dept` string, 
  `exec_dtl` string, 
  `instrumented_source_type` string, 
  `calculated_source_type` string, 
  `automated_vs_manual` string)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/rmob_map_change_stats_attribute_level_2023_08_07_2024_18_55_27/'
TBLPROPERTIES (
  'classification'='parquet', 
  'compressionType'='none', 
  'projection.enabled'='false', 
  'typeOfData'='file')
