  `condition_rmob_id` double, 
  `ws_region` string, 
  `country` string, 
  `admin_l2_display_name` string, 
  `admin_l3_display_name` string, 
  `direction_of_travel` string, 
  `link_rmob_id` decimal(38,0), 
  `functional_class` decimal(1,0), 
  `total_kms` double, 
  `shape_vector` string, 
  `latitude` decimal(9,5), 
  `longitude` decimal(9,5), 
  `admin_l1_pvid` double, 
  `admin_l2_pvid` double, 
  `admin_l3_pvid` double)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/old_variable_speed_limit/'
TBLPROPERTIES (
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='explorer_datasets', 
  'averageRecordSize'='66', 
  'classification'='parquet', 
  'compressionType'='none', 
  'objectCount'='194', 
  'recordCount'='651290', 
  'sizeKey'='46244839', 
  'typeOfData'='file')
