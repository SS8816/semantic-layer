  `region` string, 
  `road_link_id` bigint, 
  `change_type` string, 
  `change_date` timestamp, 
  `road_name` string, 
  `functional_class` bigint, 
  `country` string, 
  `admin_level2_name` string, 
  `admin_level3_name` string, 
  `admin_level4_name` string, 
  `shape_vector` string, 
  `longitude` double, 
  `latitude` double, 
  `total_kms` double, 
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
  's3://explorer-datasets-sources-prod/incremental/road_name_changes/change_year=2025/'
TBLPROPERTIES (
  'CRAWL_RUN_ID'='3b6c86ef-72c3-40c4-93e2-63dd0051c29b', 
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='explorer_datasets_road_name_changes', 
  'averageRecordSize'='141', 
  'classification'='parquet', 
  'compressionType'='none', 
  'objectCount'='291', 
  'partition_filtering.enabled'='true', 
  'recordCount'='5386239', 
  'sizeKey'='503238836', 
  'typeOfData'='file')
