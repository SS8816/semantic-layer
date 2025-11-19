  `country_region` string, 
  `province_state` string, 
  `county` string, 
  `latitude` double, 
  `longitude` double, 
  `as_of_date` timestamp, 
  `case_type` string, 
  `number_of_cases` decimal, 
  `difference` decimal)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/covid_19_08_02_2023_22_06_54/'
TBLPROPERTIES (
  'classification'='parquet', 
  'compressionType'='none', 
  'projection.enabled'='false', 
  'typeOfData'='file')
