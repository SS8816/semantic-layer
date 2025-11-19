  `place_id` string COMMENT '', 
  `place_partition` string COMMENT '', 
  `as_of` timestamp COMMENT '', 
  `last_changed_at` timestamp COMMENT '', 
  `link_pvid` string COMMENT '', 
  `categories` string COMMENT '', 
  `chains` string COMMENT '', 
  `suppliers` string COMMENT '', 
  `latitude` decimal(18,5) COMMENT '', 
  `longitude` decimal(18,5) COMMENT '', 
  `names` string COMMENT '', 
  `tqs_isopen` decimal(5,4) COMMENT '', 
  `tqs_isaddresscorrect` decimal(5,4) COMMENT '', 
  `tqs_isplace` decimal(5,4) COMMENT '', 
  `tqs_isnamecorrect` decimal(5,4) COMMENT '', 
  `tqs_isphonecorrect` decimal(5,4) COMMENT '', 
  `tqs_overallscore` decimal(38,0) COMMENT '', 
  `is_core` boolean COMMENT '', 
  `core_poi_count` decimal(13,0) COMMENT '', 
  `core_poi_ids` string COMMENT '', 
  `has_url` boolean COMMENT '', 
  `has_name` boolean COMMENT '', 
  `has_display_coordinates` boolean COMMENT '', 
  `has_routing_coordinates` boolean COMMENT '', 
  `has_h24x7` boolean COMMENT '', 
  `has_hours` boolean COMMENT '', 
  `has_note` boolean COMMENT '', 
  `admin_l1_pvid` decimal(38,0) COMMENT '', 
  `admin_l2_pvid` decimal(38,0) COMMENT '', 
  `admin_l3_pvid` decimal(38,0) COMMENT '', 
  `admin_level_2` string COMMENT '', 
  `admin_level_3` string COMMENT '', 
  `admin_level_4` string COMMENT '', 
  `country_iso_code` string COMMENT '', 
  `is_encumbered` boolean COMMENT '')
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/places_full_2022/'
TBLPROPERTIES (
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='explorer_datasets', 
  'averageRecordSize'='300', 
  'classification'='parquet', 
  'compressionType'='none', 
  'has_encrypted_data'='false', 
  'objectCount'='30', 
  'parquet.compression'='SNAPPY', 
  'presto_query_id'='20230515_222602_00070_vu5zt', 
  'recordCount'='240392569', 
  'sizeKey'='34653779929', 
  'typeOfData'='file')
