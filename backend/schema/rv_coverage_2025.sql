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
  's3://explorer-datasets-sources-prod/parquet_sources/rv_coverage_2025_10_17_2025_04_30_01/'
TBLPROPERTIES (
  'classification'='parquet', 
  'compressionType'='none', 
  'projection.enabled'='false', 
  'typeOfData'='file')
