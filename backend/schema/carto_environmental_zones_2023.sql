  `ws_region` string, 
  `carto_rmob_id` bigint, 
  `carto_pvid` bigint, 
  `carto_type` string, 
  `version` double, 
  `carto_geometry` string, 
  `longitude` double, 
  `latitude` double)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/carto_environmental_zones_2023/'
TBLPROPERTIES (
  'classification'='parquet', 
  'compressionType'='snappy', 
  'projection.enabled'='false', 
  'typeOfData'='file')
