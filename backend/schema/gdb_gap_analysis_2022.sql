  `admin4_id` double, 
  `admin4_name` string, 
  `admin3_id` double, 
  `admin3_name` string, 
  `admin2_id` double, 
  `admin2_name` string, 
  `admin1_id` bigint, 
  `admin1_name` string, 
  `drive_coverage` double, 
  `probe_coverage` double, 
  `mapillary_coverage` double, 
  `gapscore_geometry` double, 
  `gapscore_addressing` double, 
  `gapscore_speed_limit` double, 
  `gapscore_naming` double, 
  `gapscore_dot` double, 
  `gapscore_rdm` double, 
  `gapscore_total` double, 
  `gapscore_total_weight` double, 
  `country_tier` bigint, 
  `priority` bigint, 
  `shape_length` double, 
  `shape_area` double, 
  `geometry_multipolygon` string, 
  `longitude` double, 
  `latitude` double)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/gdb_gap_analysis_2022/'
TBLPROPERTIES (
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='explorer_datasets', 
  'averageRecordSize'='6238', 
  'classification'='parquet', 
  'compressionType'='none', 
  'objectCount'='3', 
  'recordCount'='111096', 
  'sizeKey'='693235293', 
  'typeOfData'='file')
