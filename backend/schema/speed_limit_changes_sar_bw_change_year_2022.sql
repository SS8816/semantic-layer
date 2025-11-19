  `region` string, 
  `link_id` bigint, 
  `change_date` timestamp, 
  `change_type` string, 
  `speed_limit` string, 
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
  `intersection_category` string, 
  `external_code` string, 
  `urban` boolean, 
  `speed_type` string, 
  `limited_or_controlled_access` boolean, 
  `internal_code` string)
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
  's3://explorer-datasets-sources-prod/incremental/speed_limit_changes_sar_bw/change_year=2022/'
TBLPROPERTIES (
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='explorer_datasets_speed_limit_changes_sar_bw', 
  'averageRecordSize'='460', 
  'classification'='parquet', 
  'compressionType'='none', 
  'objectCount'='19', 
  'partition_filtering.enabled'='true', 
  'recordCount'='130', 
  'sizeKey'='163939', 
  'typeOfData'='file')
