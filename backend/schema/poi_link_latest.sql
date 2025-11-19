  `link_rmob_id` bigint, 
  `poi_rmob_id` bigint, 
  `region` string, 
  `names` string, 
  `longitude` double, 
  `latitude` double, 
  `timestamp_of_last_update` timestamp, 
  `functional_class` decimal, 
  `link_length_meters` decimal, 
  `country` string, 
  `country_iso_code` string, 
  `state` string, 
  `county` string, 
  `city` string, 
  `feature_type` string, 
  `carto_feature_type` string)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/poi_link_latest_10_19_2025_18_53_29/'
TBLPROPERTIES (
  'classification'='parquet', 
  'compressionType'='none', 
  'projection.enabled'='false', 
  'typeOfData'='file')
