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
  's3://explorer-datasets-sources-prod/incremental/one_way_road_changes/'
TBLPROPERTIES (
  'CRAWL_RUN_ID'='ccb60761-cda2-4269-9574-0c14c98c9090', 
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='explorer_datasets_incremental', 
  'averageRecordSize'='96', 
  'classification'='parquet', 
  'compressionType'='none', 
  'objectCount'='1384', 
  'partition_filtering.enabled'='true', 
  'recordCount'='3475644', 
  'sizeKey'='324878048', 
  'typeOfData'='file')
