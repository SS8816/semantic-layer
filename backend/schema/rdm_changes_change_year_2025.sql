  `region` string, 
  `condition_id` bigint, 
  `change_date` timestamp, 
  `change_type` string, 
  `country` string, 
  `admin_level2_name` string, 
  `admin_level3_name` string, 
  `admin_level4_name` string, 
  `condition_type` string, 
  `rdm_type` string, 
  `condition_wkt` string, 
  `longitude` double, 
  `latitude` double, 
  `updated_attribute` string, 
  `admin_l1_pvid` bigint, 
  `admin_l2_pvid` bigint, 
  `admin_l3_pvid` bigint)
PARTITIONED BY ( 
  `change_month` string, 
  `change_day` string)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/incremental/rdm_changes/change_year=2025/'
TBLPROPERTIES (
  'CRAWL_RUN_ID'='f92774f2-9df0-47d4-9940-fda3d95a843d', 
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='explorer_datasets_rdm_changes', 
  'averageRecordSize'='190', 
  'classification'='parquet', 
  'compressionType'='none', 
  'objectCount'='289', 
  'partition_filtering.enabled'='true', 
  'recordCount'='191083', 
  'sizeKey'='22209122', 
  'typeOfData'='file')
