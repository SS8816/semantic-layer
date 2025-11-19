  `ucc_tile_id` string, 
  `fastmap_tile` bigint, 
  `ucc_road_id` string, 
  `fastmap_link_id` string, 
  `applies_to_direction` string, 
  `location_distance_from_start` double, 
  `traffic_light_stopping_location_signal_group_count` int, 
  `traffic_light_stopping_location_maximum_relative_distance` double, 
  `version` bigint, 
  `functional_class` int, 
  `iso_country_code` string, 
  `start_node_id` bigint, 
  `end_node_id` bigint, 
  `latitude` double, 
  `longitude` double, 
  `shape_vector` string)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/ucc_v5/'
TBLPROPERTIES (
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='explorer_datasets', 
  'averageRecordSize'='214', 
  'classification'='parquet', 
  'compressionType'='none', 
  'objectCount'='4', 
  'recordCount'='47327', 
  'sizeKey'='6194477', 
  'typeOfData'='file')
