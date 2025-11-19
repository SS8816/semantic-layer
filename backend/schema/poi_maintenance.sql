  `data_yr` double, 
  `data_qtr` string, 
  `category` string, 
  `poi_name` string, 
  `latitude` double, 
  `longitude` double, 
  `region` string, 
  `country` string, 
  `action` string, 
  `details` string, 
  `data_scope` string, 
  `id_detail` string)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/poi_maintenance/'
TBLPROPERTIES (
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='explorer_datasets', 
  'averageRecordSize'='43', 
  'classification'='parquet', 
  'compressionType'='none', 
  'objectCount'='1', 
  'recordCount'='171594', 
  'sizeKey'='5100864', 
  'typeOfData'='file')
