  `source_catalog` string, 
  `catalog_version` bigint, 
  `here_tile_id` string, 
  `link_attribution_ref` string, 
  `applies_to_direction` string, 
  `distance_from_start` double, 
  `signal_group_count` int, 
  `maximum_relative_distance` double, 
  `ws_region` string, 
  `topology_segment_id` bigint, 
  `nav_link_id` bigint, 
  `sequence_number` bigint, 
  `orientation` string, 
  `link_rmob_id` bigint, 
  `version` double, 
  `shape_vector` string, 
  `segment_geometry` string, 
  `link_ratio` double, 
  `orientated_link_ratio` double, 
  `point_wkt` string, 
  `stop_location_latitude` double, 
  `stop_location_longitude` double)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/ucc_v4_with_Links/'
TBLPROPERTIES (
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='explorer_datasets', 
  'averageRecordSize'='217', 
  'classification'='parquet', 
  'compressionType'='none', 
  'objectCount'='24', 
  'recordCount'='342860', 
  'sizeKey'='75355162', 
  'typeOfData'='file')
