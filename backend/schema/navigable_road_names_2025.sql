  `ws_region` string, 
  `road_link_rmob_id` bigint, 
  `road_link_pvid` bigint, 
  `link_pvid` bigint, 
  `functional_class` string, 
  `country` string, 
  `admin_l2_display_name` string, 
  `admin_l3_display_name` string, 
  `admin_l4_display_name` string, 
  `link_geometry` string, 
  `latitude` double, 
  `longitude` double, 
  `link_length_kms` double, 
  `road_name` string, 
  `name_type` string, 
  `is_valid_unnamed` boolean, 
  `is_exit_name` boolean, 
  `is_explicatable` boolean, 
  `is_postal_name` boolean, 
  `is_stale_name` boolean, 
  `is_vanity_name` boolean, 
  `is_scenic_name` boolean, 
  `is_exonym` boolean)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/navigable_road_names_2025_10_17_2025_08_30_01/'
TBLPROPERTIES (
  'classification'='parquet', 
  'compressionType'='none', 
  'projection.enabled'='false', 
  'typeOfData'='file')
