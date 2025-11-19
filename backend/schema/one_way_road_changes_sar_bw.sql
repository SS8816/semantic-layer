  `region` string, 
  `link_id` bigint, 
  `change_date` timestamp, 
  `change_type` string, 
  `direction_of_travel` string, 
  `functional_class` decimal(1,0), 
  `is_tollway` boolean, 
  `is_controlled_access` boolean, 
  `is_motorway` boolean, 
  `is_long_haul` boolean, 
  `country` string, 
  `admin_level2_name` string, 
  `admin_level3_name` string, 
  `admin_level4_name` string, 
  `admin_l1_pvid` bigint, 
  `admin_l2_pvid` bigint, 
  `admin_l3_pvid` bigint, 
  `shape_vector` string, 
  `longitude` double, 
  `latitude` double, 
  `total_kms` double)
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
  's3://explorer-datasets-sources-prod/incremental/one_way_road_changes_sar_bw/'
TBLPROPERTIES (
  'CRAWL_RUN_ID'='b5d4a8f2-9406-4b4e-8824-4dd4cff7ed66', 
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='explorer_datasets_incremental', 
  'averageRecordSize'='314', 
  'classification'='parquet', 
  'compressionType'='none', 
  'objectCount'='228', 
  'partition_filtering.enabled'='true', 
  'recordCount'='2307', 
  'sizeKey'='1676415', 
  'typeOfData'='file')
