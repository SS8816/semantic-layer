  `region` string, 
  `carto_id` bigint, 
  `carto_version` double, 
  `carto_pvid` bigint, 
  `carto_geometry_type` string, 
  `feature_type` string, 
  `last_modified_on` timestamp, 
  `country` string, 
  `latitude` double, 
  `longitude` double, 
  `carto_length_meters` double, 
  `extended_attribute_expanded_inclusion` string)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/carto_active_2024_12_17_2024_04_30_03/'
TBLPROPERTIES (
  'classification'='parquet', 
  'compressionType'='none', 
  'projection.enabled'='false', 
  'typeOfData'='file')
