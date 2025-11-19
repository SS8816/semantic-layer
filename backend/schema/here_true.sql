  `ws_region` string, 
  `link_rmob_id` bigint, 
  `link_pvid` bigint, 
  `functional_class` string, 
  `allows_autos` boolean, 
  `intersection_category` string, 
  `speed_category` string, 
  `low_mobility` string, 
  `is_ramp` boolean, 
  `is_paved` boolean, 
  `is_boat_ferry` boolean, 
  `is_rail_ferry` boolean, 
  `is_private` boolean, 
  `is_limited_access` boolean, 
  `link_geometry_wkt` string, 
  `link_length_kms` double, 
  `link_longitude` double, 
  `link_latitude` double, 
  `country_iso_code` string, 
  `country` string, 
  `country_pvid` bigint, 
  `level2_admin` string, 
  `level2_pvid` bigint, 
  `level3_admin` string, 
  `level3_pvid` bigint, 
  `level4_admin` string, 
  `level5_admin` string, 
  `level10_tileid` bigint, 
  `level12_tileid` bigint, 
  `level14_tileid` bigint, 
  `level16_tileid` bigint, 
  `ht_driveid` string, 
  `additional_info` string, 
  `ht_timestamp` timestamp, 
  `segment_id` bigint, 
  `egis_asset_id` bigint, 
  `egis_asset_state` string, 
  `egis_drive_date` timestamp)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/here_true_10_27_2025_19_00_02/'
TBLPROPERTIES (
  'classification'='parquet', 
  'compressionType'='none', 
  'projection.enabled'='false', 
  'typeOfData'='file')
