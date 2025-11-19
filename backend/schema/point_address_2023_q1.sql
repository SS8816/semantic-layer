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
  's3://explorer-datasets-sources-prod/parquet_sources/point_address_2023_q1/'
TBLPROPERTIES (
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='explorer_datasets', 
  'averageRecordSize'='28', 
  'classification'='parquet', 
  'compressionType'='none', 
  'objectCount'='35', 
  'recordCount'='473437168', 
  'sizeKey'='15385265206', 
  'typeOfData'='file')
