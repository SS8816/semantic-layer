  `metadata_version` string, 
  `metadata_change_id` bigint, 
  `feature_type_domain_name` string, 
  `chain_id_domain_name` string, 
  `street_side_domain_name` string, 
  `functional_class_domain_name` string, 
  `address_format_domain_name` string, 
  `calculated_level_domain_name` string, 
  `display_lang_code_domain_name` string, 
  `display_trans_type_domain_name` string, 
  `preferred_contact_type_domain_name` string, 
  `food_type_domain_name` string, 
  `fuel_type_domain_name` string, 
  `ipd_flag_domain_name` string, 
  `building_type_domain_name` string, 
  `rest_area_type_domain_name` string, 
  `alternate_food_type_domain_name` string, 
  `regional_food_type_domain_name` string, 
  `restaurant_type_domain_name` string, 
  `subcategories_domain_name` string, 
  `poi_special_case_domain_name` string, 
  `display_class_domain_name` string, 
  `actual_address_language_code_domain_name` string, 
  `actual_address_trans_type_domain_name` string, 
  `parsed_address_language_code_domain_name` string, 
  `parsed_address_trans_type_domain_name` string, 
  `full_house_number_language_code_domain_name` string, 
  `full_house_number_trans_type_domain_name` string, 
  `cfst_publish_code_domain_name` string, 
  `landmark_icon_attachment_type_domain_name` string, 
  `icon_alpha_channel_bitmap_attachment_type_domain_name` string)
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION
  's3://explorer-datasets-sources-prod/parquet_sources/rmob_metadata_mcw_poi_domain_10_21_2025_19_00_02/'
TBLPROPERTIES (
  'classification'='parquet', 
  'compressionType'='none', 
  'projection.enabled'='false', 
  'typeOfData'='file')
