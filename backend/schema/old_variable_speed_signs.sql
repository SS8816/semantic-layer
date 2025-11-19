  `condition_rmob_id` decimal(38,0), 
  `ws_region` string, 
  `country` string, 
  `admin_l2_display_name` string, 
  `admin_l3_display_name` string, 
  `location_on_sign` string, 
  `link_rmob_id` string, 
  `functional_class` decimal(1,0), 
  `total_kms` double, 
  `shape_vector` string, 
  `latitude` string, 
  `longitude` string, 
  `admin_l1_pvid` decimal(38,0), 
  `admin_l2_pvid` decimal(38,0), 
  `admin_l3_pvid` decimal(38,0))
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/old_variable_speed_signs/'
TBLPROPERTIES (
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='explorer_datasets', 
  'averageRecordSize'='190', 
  'classification'='parquet', 
  'compressionType'='none', 
  'objectCount'='117', 
  'recordCount'='121077', 
  'sizeKey'='24342691', 
  'typeOfData'='file')
