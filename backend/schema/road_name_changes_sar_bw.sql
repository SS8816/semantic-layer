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
  's3://explorer-datasets-sources-prod/incremental/road_name_changes_sar_bw/'
TBLPROPERTIES (
  'CRAWL_RUN_ID'='1948c53e-c7c5-41ac-a901-5605d96c82bf', 
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='explorer_datasets_incremental', 
  'averageRecordSize'='167', 
  'classification'='parquet', 
  'compressionType'='none', 
  'objectCount'='364', 
  'partition_filtering.enabled'='true', 
  'recordCount'='17717', 
  'sizeKey'='3577744', 
  'typeOfData'='file')
