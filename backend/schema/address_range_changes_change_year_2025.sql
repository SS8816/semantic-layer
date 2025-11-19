  `region` string, 
  `road_link_id` bigint, 
  `change_type` string, 
  `change_date` timestamp, 
  `left_address_range` string, 
  `right_address_range` string, 
  `functional_class` bigint, 
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
  `change_month` string, 
  `change_day` string)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/incremental/address_range_changes/change_year=2025/'
TBLPROPERTIES (
  'CRAWL_RUN_ID'='9d5d098f-9c48-461d-87ae-13654151f1e4', 
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='explorer_datasets_ address_range_changes', 
  'averageRecordSize'='158', 
  'classification'='parquet', 
  'compressionType'='none', 
  'objectCount'='293', 
  'partition_filtering.enabled'='true', 
  'recordCount'='5999640', 
  'sizeKey'='647436144', 
  'typeOfData'='file')
