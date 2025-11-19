  `ws_region` string, 
  `road_link_rmob_id` bigint, 
  `road_link_pvid` bigint, 
  `link_pvid` bigint, 
  `functional_class` string, 
  `country` string, 
  `admin_l2_display_name` string, 
  `admin_l3_display_name` string, 
  `admin_l4_display_name` string, 
  `link_geometry` string, 
  `latitude` double, 
  `longitude` double, 
  `link_length_kms` double, 
  `left_address_range` string, 
  `right_address_range` string, 
  `address_type` string, 
  `left_scheme` string, 
  `right_scheme` string, 
  `address_interpolation` string)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/navigable_road_address_apac_231C0/'
TBLPROPERTIES (
  'CrawlerSchemaDeserializerVersion'='1.0', 
  'CrawlerSchemaSerializerVersion'='1.0', 
  'UPDATED_BY_CRAWLER'='explorer_datasets', 
  'averageRecordSize'='78', 
  'classification'='parquet', 
  'compressionType'='none', 
  'objectCount'='1', 
  'recordCount'='1443330', 
  'sizeKey'='112764107', 
  'typeOfData'='file')
