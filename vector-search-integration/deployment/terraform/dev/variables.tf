# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

variable "dev_project_id" {
  type        = string
  description = "**Dev** Google Cloud Project ID for resource deployment."
}

variable "region" {
  type        = string
  description = "Google Cloud region for resource deployment."
  default     = "us-central1"
}

variable "telemetry_bigquery_dataset_id" {
  type        = string
  description = "BigQuery dataset ID for telemetry data export."
  default     = "telemetry_genai_app_sample_sink"
}

variable "feedback_bigquery_dataset_id" {
  type        = string
  description = "BigQuery dataset ID for feedback data export."
  default     = "feedback_genai_app_sample_sink"
}

variable "telemetry_logs_filter" {
  type        = string
  description = "Log Sink filter for capturing telemetry data. Captures logs with the `traceloop.association.properties.log_type` attribute set to `tracing`."
  default     = "jsonPayload.attributes.\"traceloop.association.properties.log_type\"=\"tracing\" jsonPayload.resource.attributes.\"service.name\"=\"Sample Chatbot Application\""
}

variable "feedback_logs_filter" {
  type        = string
  description = "Log Sink filter for capturing feedback data. Captures logs where the `log_type` field is `feedback`."
  default     = "jsonPayload.log_type=\"feedback\""
}

variable "telemetry_sink_name" {
  type        = string
  description = "Name of the telemetry data Log Sink."
  default     = "telemetry_logs_genai_app_sample"
}

variable "feedback_sink_name" {
  type        = string
  description = "Name of the feedback data Log Sink."
  default     = "feedback_logs_genai_app_sample"
}
variable "cloud_run_app_sa_name" {
  description = "Service account name to be used for the Cloud Run service"
  type        = string
  default     = "vector-search-integration-cr"
}

variable "cloud_run_app_roles" {
  description = "List of roles to assign to the Cloud Run app service account"
  type        = list(string)
  default = [
    "roles/aiplatform.user",
    "roles/discoveryengine.editor",
    "roles/logging.logWriter",
    "roles/cloudtrace.agent",
    "roles/storage.admin"
  ]
}
variable "vertexai_pipeline_sa_name" {
  description = "Service account name to be used for the Vertex AI service"
  type        = string
  default     = "data-ingestion-vertexai-sa"
}

variable "data_store_region" {
  type        = string
  description = "Google Cloud region for resource deployment."
  default     = "us"
}

variable "pipelines_roles" {
  description = "List of roles to assign to the Vertex AI runner service account"
  type        = list(string)
  default = [
    "roles/storage.admin",
    "roles/run.invoker",
    "roles/aiplatform.user",
    "roles/discoveryengine.admin",
    "roles/logging.logWriter",
    "roles/artifactregistry.writer",
    "roles/bigquery.dataEditor",
    "roles/bigquery.jobUser",
    "roles/bigquery.readSessionUser",
    "roles/bigquery.connectionAdmin",
    "roles/resourcemanager.projectIamAdmin"
  ]
}

variable "datastore_name" {
  description = "The name of the datastore"
  type = string
  default = "my-datastore"
}

variable "search_engine_name" {
  description = "The name of the search engine"
  type = string
  default = "my-search-engine"
}

variable "vector_search_display_name" {
  description = "The name of the vector search instance"
  type = string
  default = "my_vector_search"
}

variable "vector_search_deployed_index_name" {
  description = "The name of the vector search deployed index"
  type = string
  default = "my_vector_search_deployed"
}

variable "vector_search_embedding_size" {
  type = number
  description = "The number of dimensions for the embeddings."
  default = 768
}

variable "vector_search_approximate_neighbors_count" {
  type = number
  description = "The approximate number of neighbors to return."
  default = 150
}

variable "vector_search_min_replica_count" {
  type = number
  description = "The min replica count for vector search instance"
  default = 1
}

variable "vector_search_max_replica_count" {
  type = number
  description = "The max replica count for vector search instance"
  default = 1
}

variable "vector_search_shard_size" {
  description = "The shard size of the vector search instance"
  type = string
  default = "SHARD_SIZE_SMALL"
}

variable "vector_search_machine_type" {
  description = "The machine type for the vector search instance"
  type = string
  default = "e2-standard-2"
}