  `place_id` string, 
  `place_partition` string, 
  `link_pvid` string, 
  `categories` string, 
  `chains` string, 
  `suppliers` string, 
  `latitude` double, 
  `longitude` double, 
  `names` string, 
  `has_h24x7` boolean, 
  `admin_l1_pvid` string, 
  `admin_l2_pvid` string, 
  `admin_l3_pvid` string, 
  `admin_level_2` string, 
  `admin_level_3` string, 
  `admin_level_4` string, 
  `country_iso_code` string)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/places_full_2025_08_30_2025_03_49_44/'
TBLPROPERTIES (
  'classification'='parquet', 
  'compressionType'='none', 
  'projection.enabled'='false', 
  'typeOfData'='file')
