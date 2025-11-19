  `admin_l1_display_name` string, 
  `admin_l2_display_name` string, 
  `admin_l3_display_name` string, 
  `admin_l4_display_name` string, 
  `ws_region` string, 
  `road_point_pvid` bigint, 
  `routing_side` string, 
  `longitude` double, 
  `latitude` double, 
  `building_unit_name` string, 
  `street_address` string, 
  `left_address_range` string, 
  `right_address_range` string, 
  `source_type` string, 
  `source_id` string, 
  `is_anonymous_address_point` string, 
  `is_estimated_address_point` string)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/point_address_2024_11_16_2024_00_00_02/'
TBLPROPERTIES (
  'classification'='parquet', 
  'compressionType'='none', 
  'projection.enabled'='false', 
  'typeOfData'='file')
