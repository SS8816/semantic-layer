  `country` string, 
  `admin_l2_display_name` string, 
  `admin_l3_display_name` string, 
  `admin_l4_display_name` string, 
  `condition_rmob_id` bigint, 
  `link_rmob_id` bigint, 
  `functional_class` string, 
  `latitude` double, 
  `longitude` double, 
  `rv_types` string, 
  `rv_seasional_closure` string, 
  `rv_direction_closure` string, 
  `rv_restriction` string, 
  `restriction_detail` string)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/rv_coverage_2022/'
TBLPROPERTIES (
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='explorer_datasets', 
  'averageRecordSize'='31', 
  'classification'='parquet', 
  'compressionType'='none', 
  'objectCount'='1', 
  'recordCount'='39100', 
  'sizeKey'='1228820', 
  'typeOfData'='file')
