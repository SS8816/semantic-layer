  `building_id` string, 
  `iso_country_code` string, 
  `type` string, 
  `type_description` string, 
  `latitude` double, 
  `longitude` double, 
  `max_building_height` double)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/building_footprints_2d_2023_01_08_2024_20_39_57/'
TBLPROPERTIES (
  'classification'='parquet', 
  'compressionType'='none', 
  'projection.enabled'='false', 
  'typeOfData'='file')
