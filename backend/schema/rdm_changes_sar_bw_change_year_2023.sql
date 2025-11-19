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
  's3://explorer-datasets-sources-prod/incremental/rdm_changes_sar_bw/change_year=2023/'
TBLPROPERTIES (
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='explorer_datasets_rdm_changes_sar_bw', 
  'averageRecordSize'='781', 
  'classification'='parquet', 
  'compressionType'='none', 
  'objectCount'='18', 
  'partition_filtering.enabled'='true', 
  'recordCount'='56', 
  'sizeKey'='119370', 
  'typeOfData'='file')
