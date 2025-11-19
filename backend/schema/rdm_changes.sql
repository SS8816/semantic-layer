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
  `change_year` string, 
  `change_month` string, 
  `change_day` string)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/incremental/rdm_changes/'
TBLPROPERTIES (
  'CRAWL_RUN_ID'='3f6b25d2-6292-4391-81fa-42e0556ebd91', 
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='explorer_datasets_incremental', 
  'averageRecordSize'='134', 
  'classification'='parquet', 
  'compressionType'='none', 
  'objectCount'='1378', 
  'partition_filtering.enabled'='true', 
  'recordCount'='676318', 
  'sizeKey'='80573997', 
  'typeOfData'='file')
