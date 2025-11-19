  `place_id` string, 
  `partition` string, 
  `as_of` timestamp, 
  `last_changed_at` timestamp, 
  `link_pvid` string, 
  `country_admin_pvid` decimal(38,0), 
  `admin_l2_pvid` decimal(38,0), 
  `admin_l3_pvid` decimal(38,0), 
  `categories` string, 
  `chains` string, 
  `suppliers` string, 
  `latitude` decimal(18,5), 
  `longitude` decimal(18,5), 
  `names` string, 
  `tqs_isopen` decimal(5,4), 
  `tqs_isaddresscorrect` decimal(5,4), 
  `tqs_isplace` decimal(5,4), 
  `tqs_isnamecorrect` decimal(5,4), 
  `tqs_isphonecorrect` decimal(5,4), 
  `tqs_overallscore` decimal(38,0), 
  `is_core` boolean, 
  `core_poi_count` decimal(13,0), 
  `core_poi_ids` string, 
  `has_url` boolean, 
  `has_name` boolean, 
  `has_display_coordinates` boolean, 
  `has_routing_coordinates` boolean, 
  `has_h24x7` boolean, 
  `has_hours` boolean, 
  `has_note` boolean, 
  `has_pay_method` boolean)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/places_full_encumbered_2022/'
TBLPROPERTIES (
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='explorer_datasets', 
  'averageRecordSize'='126', 
  'classification'='parquet', 
  'compressionType'='none', 
  'objectCount'='256', 
  'recordCount'='140810138', 
  'sizeKey'='17948946855', 
  'typeOfData'='file')
