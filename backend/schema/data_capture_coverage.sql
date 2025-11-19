  `automobile` string, 
  `bus` string, 
  `taxi` string, 
  `carpool` string, 
  `pedestrian` string, 
  `truck` string, 
  `through_tr` string, 
  `delivery` string, 
  `emergency_` string, 
  `motorcycle` string, 
  `all_vehicl` string, 
  `func_class` string, 
  `link_id` string, 
  `length_km` double, 
  `geometry` string, 
  `latitude` double, 
  `longitude` double, 
  `tile_array` string, 
  `shape_file_name` string)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/data_capture_coverage/'
TBLPROPERTIES (
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='explorer_datasets', 
  'averageRecordSize'='213', 
  'classification'='parquet', 
  'compressionType'='none', 
  'objectCount'='2', 
  'recordCount'='293021', 
  'sizeKey'='23717601', 
  'typeOfData'='file')
