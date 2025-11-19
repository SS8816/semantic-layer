  `region` string, 
  `link_id` bigint, 
  `change_date` timestamp, 
  `change_type` string, 
  `functional_class` decimal(1,0), 
  `is_tollway` boolean, 
  `is_controlled_access` boolean, 
  `is_motorway` boolean, 
  `is_long_haul` boolean, 
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
  `admin_l3_pvid` bigint, 
  `intersection_category` string)
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
  's3://explorer-datasets-sources-prod/incremental/new_and_updated_geometry/change_year=2025/'
TBLPROPERTIES (
  'CRAWL_RUN_ID'='58ed099b-aa50-4aa6-80cb-7c7b30b85fd2', 
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='explorer_datasets_new_and_updated_geometry', 
  'averageRecordSize'='173', 
  'classification'='parquet', 
  'compressionType'='none', 
  'objectCount'='291', 
  'partition_filtering.enabled'='true', 
  'recordCount'='14538004', 
  'sizeKey'='1401876930', 
  'typeOfData'='file')
