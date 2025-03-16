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

import os
from unittest.mock import MagicMock

from google.cloud import aiplatform
from langchain_google_community.vertex_rank import VertexAIRank
from langchain_google_vertexai import VectorSearchVectorStore, VertexAIEmbeddings


def get_retriever(
    project_id: str,
    region: str,
    vector_search_bucket: str,
    vector_search_index: str,
    vector_search_index_endpoint: str,
    embedding: VertexAIEmbeddings,
) -> VectorSearchVectorStore:
    """
    Creates and returns an instance of the retriever service.

    Uses mock service if the INTEGRATION_TEST environment variable is set to "TRUE",
    otherwise initializes real Vertex AI retriever.
    """
    if os.getenv("INTEGRATION_TEST") == "TRUE":
        retriever = MagicMock()
        retriever.invoke = lambda x: []
        return retriever

    aiplatform.init(
        project=project_id,
        location=region,
        staging_bucket=f"gs://{vector_search_bucket}",
    )

    my_index = aiplatform.MatchingEngineIndex(vector_search_index)

    my_index_endpoint = aiplatform.MatchingEngineIndexEndpoint(
        vector_search_index_endpoint
    )

    return VectorSearchVectorStore.from_components(
        project_id=project_id,
        region=region,
        gcs_bucket_name=vector_search_bucket,
        index_id=my_index.name,
        endpoint_id=my_index_endpoint.name,
        embedding=embedding,
        stream_update=True,
    ).as_retriever()


def get_compressor(project_id: str, top_n: int = 5) -> VertexAIRank:
    """
    Creates and returns an instance of the compressor service.

    Uses mock service if the INTEGRATION_TEST environment variable is set to "TRUE",
    otherwise initializes real Vertex AI compressor.
    """
    if os.getenv("INTEGRATION_TEST") == "TRUE":
        compressor = MagicMock()
        compressor.compress_documents = lambda documents, query: []
        return compressor

    return VertexAIRank(
        project_id=project_id,
        location_id="global",
        ranking_config="default_ranking_config",
        title_field="id",
        top_n=top_n,
    )
