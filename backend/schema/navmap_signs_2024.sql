  `region` string, 
  `country` string, 
  `admin_level_2` string, 
  `admin_level_3` string, 
  `admin_level_4` string, 
  `condition_pvid` bigint, 
  `attribute_type` string, 
  `attribute_value` string, 
  `link_pvid` bigint, 
  `functional_class` string, 
  `intersection_category` string, 
  `latitude` decimal, 
  `longitude` decimal, 
  `created_at` timestamp, 
  `last_changed_at` timestamp)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/navmap_signs_2024_11_15_2024_20_00_02/'
TBLPROPERTIES (
  'classification'='parquet', 
  'compressionType'='none', 
  'projection.enabled'='false', 
  'typeOfData'='file')
