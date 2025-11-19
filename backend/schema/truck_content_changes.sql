  `region` string, 
  `link_id` bigint, 
  `condition_rmob_id` bigint, 
  `change_date` timestamp, 
  `change_type` string, 
  `transport_type` string, 
  `direction_closure` string, 
  `hazmat_permit_required` string, 
  `hazmat_type` string, 
  `physical_structure_type` string, 
  `restriction_type` string, 
  `trailer_type` string, 
  `transport_preferred_route_type` string, 
  `height` decimal(23,5), 
  `weight` decimal(26,8), 
  `width` decimal(23,5), 
  `length` decimal(23,5), 
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
  `urban` boolean, 
  `limited_or_controlled_access` boolean)
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
  's3://explorer-datasets-sources-prod/incremental/truck_content_changes/'
TBLPROPERTIES (
  'CRAWL_RUN_ID'='ccb60761-cda2-4269-9574-0c14c98c9090', 
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='explorer_datasets_incremental', 
  'averageRecordSize'='118', 
  'classification'='parquet', 
  'compressionType'='none', 
  'objectCount'='281', 
  'partition_filtering.enabled'='true', 
  'recordCount'='2507629', 
  'sizeKey'='187696138', 
  'typeOfData'='file')
