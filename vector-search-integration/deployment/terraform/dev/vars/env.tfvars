# Your Dev Google Cloud project id
dev_project_id =  "telefonica-425415"

# The Google Cloud region you will use to deploy the infrastructure
region = "us-central1"

telemetry_bigquery_dataset_id = "telemetry_genai_app_sample_sink"
telemetry_sink_name = "telemetry_logs_genai_app_sample"
telemetry_logs_filter = "jsonPayload.attributes.\"traceloop.association.properties.log_type\"=\"tracing\" jsonPayload.resource.attributes.\"service.name\"=\"vector-search-integration\""

feedback_bigquery_dataset_id = "feedback_genai_app_sample_sink"
feedback_sink_name = "feedback_logs_genai_app_sample"
feedback_logs_filter = "jsonPayload.log_type=\"feedback\""
search_engine_name = "sample-search-engine"
datastore_name = "sample-datastore"
vertexai_pipeline_sa_name = "vertexai-pipelines-sa"
vector_search_display_name = "sample_vector_search"
vector_search_deployed_index_name = "sample_vector_search_deployed"
vector_search_shard_size = "SHARD_SIZE_SMALL"
vector_search_machine_type = "e2-standard-2"
vector_search_min_replica_count = 1
vector_search_max_replica_count = 1

#The value can only be one of "global", "us" and "eu".
data_store_region = "us"
