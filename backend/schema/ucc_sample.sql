  `ucc_tile_id` string, 
  `fastmap_tile` bigint, 
  `ucc_road_id` string, 
  `fastmap_link_id` string, 
  `applies_to_direction` string, 
  `distance_from_start` double, 
  `maximum_relative_distance` double, 
  `location_signal_group_count` int, 
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
  's3://explorer-datasets-sources-prod/parquet_sources/ucc_sample/'
TBLPROPERTIES (
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='explorer_datasets', 
  'averageRecordSize'='226', 
  'classification'='parquet', 
  'compressionType'='none', 
  'objectCount'='17', 
  'recordCount'='387907', 
  'sizeKey'='50688080', 
  'typeOfData'='file')
