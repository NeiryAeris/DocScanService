from __future__ import annotations

from typing import Any, Dict, List, Optional
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models as qm


class QdrantStore:
    def __init__(self, url: str, api_key: str, collection: str):
        self.collection = collection
        self.client = QdrantClient(url=url, api_key=(api_key or None))

    def ensure_collection(self, vector_size: int):
        existing = {c.name for c in self.client.get_collections().collections}
        if self.collection in existing:
            return

        self.client.create_collection(
            collection_name=self.collection,
            vectors_config=qm.VectorParams(size=vector_size, distance=qm.Distance.COSINE),
        )

        # Speed up filtered retrieval
        self.client.create_payload_index(
            collection_name=self.collection,
            field_name="user_id",
            field_schema=qm.PayloadSchemaType.KEYWORD,
        )
        self.client.create_payload_index(
            collection_name=self.collection,
            field_name="doc_id",
            field_schema=qm.PayloadSchemaType.KEYWORD,
        )

    def upsert(self, vectors: List[List[float]], payloads: List[Dict[str, Any]]) -> int:
        if not vectors:
            return 0
        self.ensure_collection(vector_size=len(vectors[0]))

        points = [
            qm.PointStruct(id=str(uuid.uuid4()), vector=v, payload=p)
            for v, p in zip(vectors, payloads)
        ]
        self.client.upsert(collection_name=self.collection, points=points)
        return len(points)

    def search(self, query_vector: List[float], user_id: str, doc_ids: Optional[List[str]], top_k: int):
        must = [qm.FieldCondition(key="user_id", match=qm.MatchValue(value=user_id))]
        if doc_ids:
            must.append(qm.FieldCondition(key="doc_id", match=qm.MatchAny(any=doc_ids)))
        flt = qm.Filter(must=must)

        return self.client.search(
            collection_name=self.collection,
            query_vector=query_vector,
            limit=top_k,
            with_payload=True,
            query_filter=flt,
        )

    def delete_doc(self, user_id: str, doc_id: str):
        flt = qm.Filter(
            must=[
                qm.FieldCondition(key="user_id", match=qm.MatchValue(value=user_id)),
                qm.FieldCondition(key="doc_id", match=qm.MatchValue(value=doc_id)),
            ]
        )
        self.client.delete(collection_name=self.collection, points_selector=qm.FilterSelector(filter=flt))
